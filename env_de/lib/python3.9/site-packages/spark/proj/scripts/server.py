"""
Spark's builtin web server.
mostly copied from standard lib CGIHTTPServer.py,
"""

import os
import sys
import posixpath
import BaseHTTPServer
import signal
import optparse
import urllib
import shutil
import mimetypes
import logging
import errno

proj_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))
sys.path.insert(0,proj_dir)

import etc.runcgi

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
		datefmt='%m-%d %H:%M', 
		filename=os.path.join(proj_dir,'log','spark_server.log'),
                filemode='w')

class SparkHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    # Make rfile unbuffered -- we need to read one line and then pass
    # the rest to a subprocess, so we can't use buffered input.
    rbufsize = 0

    static_directories = {'/public':os.path.join(proj_dir,'public')}

    def is_static(self):
        #path = self.path
        path = posixpath.normpath(urllib.unquote(self.path))
        for x in self.static_directories:
            i = len(x)
            if path[:i] == x and (not path[i:] or path[i] == '/'):
                words = filter(None,path[i+1:].split('/'))
                path = self.static_directories[x]
                for word in words:
                    drive, word = os.path.splitdrive(word)
                    head, word = os.path.split(word)
                    if word in (os.curdir, os.pardir): continue
                    path = os.path.join(path, word)
                self.phy_path = path
                return True
        return False

    def do_GET(self):
        if self.is_static():
            self.send_file(self.phy_path)
        else:
            self.run_cgi()

    def do_POST(self): self.run_cgi()

    def send_file(self,path):
        f = None
        ctype = self.guess_type(path)
        if ctype.startswith('text/'):
            mode = 'r'
        else:
            mode = 'rb'
        try:
            f = open(path, mode)
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Length", str(os.fstat(f.fileno())[6]))
        self.end_headers()
        shutil.copyfileobj(f, self.wfile)
        f.close()

    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        })

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    def log_message(self, format, *args):
        logging.info(format%args)

    def run_cgi(self):
        rest = self.path
        i = rest.rfind('?')
        if i >= 0:
            rest, query = rest[:i], rest[i+1:]
        else:
            query = ''

        # Reference: http://hoohoo.ncsa.uiuc.edu/cgi/env.html
        # XXX Much of the following could be prepared ahead of time!
        env = {}
        env['SERVER_SOFTWARE'] = self.version_string()
        env['SERVER_NAME'] = self.server.server_name
        env['GATEWAY_INTERFACE'] = 'CGI/1.1'
        env['SERVER_PROTOCOL'] = self.protocol_version
        env['SERVER_PORT'] = str(self.server.server_port)
        env['REQUEST_METHOD'] = self.command
        uqrest = urllib.unquote(rest)
        env['PATH_INFO'] = uqrest
        #env['PATH_TRANSLATED'] = self.translate_path(uqrest)
        env['SCRIPT_NAME'] = 'The script'
        if query:
            env['QUERY_STRING'] = query
        host = self.address_string()
        if host != self.client_address[0]:
            env['REMOTE_HOST'] = host
        env['REMOTE_ADDR'] = self.client_address[0]
        # XXX REMOTE_IDENT
        if self.headers.typeheader is None:
            env['CONTENT_TYPE'] = self.headers.type
        else:
            env['CONTENT_TYPE'] = self.headers.typeheader
        length = self.headers.getheader('content-length')
        if length:
            env['CONTENT_LENGTH'] = length
        accept = []
        for line in self.headers.getallmatchingheaders('accept'):
            if line[:1] in "\t\n\r ":
                accept.append(line.strip())
            else:
                accept = accept + line[7:].split(',')
        env['HTTP_ACCEPT'] = ','.join(accept)
        ua = self.headers.getheader('user-agent')
        if ua:
            env['HTTP_USER_AGENT'] = ua
        co = filter(None, self.headers.getheaders('cookie'))
        if co:
            env['HTTP_COOKIE'] = ', '.join(co)
        # XXX Other HTTP_* headers
        # Since we're setting the env in the parent, provide empty
        # values to override previously set values
        for k in ('QUERY_STRING', 'REMOTE_HOST', 'CONTENT_LENGTH',
                  'HTTP_USER_AGENT', 'HTTP_COOKIE'):
            env.setdefault(k, "")
        os.environ.update(env)

        self.send_response(200, "Script output follows")

        decoded_query = query.replace('+', ' ')

        save_stdout = sys.stdout
        try:
            try:
                sys.stdout = self.wfile
                etc.runcgi.spark_req_run()
            finally:
                sys.stdout = save_stdout
        except SystemExit, sts:
            self.log_error("CGI script exit status %s", str(sts))
        else:
            self.log_message("CGI script exited OK")


class Daemon(object):
    pidfile = os.path.join(proj_dir,'log','spark_pid')

    def run(self): pass

    def start(self):
        if not hasattr(os,'fork'): sys.exit("Can't daemonize in Windows")
        if os.path.exists(self.pidfile):
            try:
                pf = open(self.pidfile)
                pid = int(pf.read().strip())
                pf.close()
            except IOError, ValueError:
                sys.exit('pidfile %s bad' % self.pidfile)
            try:
                os.kill(pid, 0)
            except OSError, (code, text):
                if code == errno.ESRCH:
                    os.remove(self.pidfile)
                else:
                    sys.exit('status missing from pidfile %s' % self.pidfile)
            else:
                sys.exit('already running?')

        try:
            if os.path.exists(self.pidfile): check = self.pidfile
            else: check = os.path.dirname(self.pidfile)
            if not os.access(check, os.W_OK):
                msg = 'unable to write to pidfile %s' % self.pidfile
                sys.exit(msg)

            #daemonize
            if os.fork(): os._exit(0)
            os.setsid()
            if os.fork(): os._exit(0)
            os.umask(077)
            null=os.open('/dev/null', os.O_RDWR)
            for i in range(3):
                os.dup2(null, i)
            os.close(null)

        except:
            logging.exception("failed to start due to an exception")
            raise

        if self.pidfile:
            open(self.pidfile, 'wb').write(str(os.getpid()))
        try:
            logging.info("Spark Web Server started")
            try:
                self.run()
            except (KeyboardInterrupt, SystemExit):
                pass
            except:
                logging.exception("stopping with an exception")
                raise
        finally:
            if self.pidfile and os.path.exists(self.pidfile):
                os.remove(self.pidfile)
            logging.info("Spark Web Server stopped")

    def stop(self):
        """Stop the running process"""
        if self.pidfile and os.path.exists(self.pidfile):
            pid = int(open(self.pidfile).read())
            os.kill(pid, signal.SIGTERM)
            # wait for a moment to see if the process dies
            import time
            for n in range(10):
                time.sleep(0.25)
                try:
                    # poll the process state
                    os.kill(pid, 0)
                except OSError, why:
                    if why[0] == errno.ESRCH:
                        # process has died
                        break
                    else:
                        raise
            else:
                sys.exit("pid %d did not die" % pid)
        else:
            sys.exit("not running")

class SparkServer(BaseHTTPServer.HTTPServer):
    "Get rid of ugly traceback on control-C"
    def serve_forever(self):
        try:
            while 1: self.handle_request()
	except KeyboardInterrupt:
            print "Spark Server Exited"
            sys.exit()
	
if __name__ == '__main__':
    p = optparse.OptionParser()
    p.add_option('-d', dest='daemon', action='store_true', help='Run as daemon')
    p.add_option('-s', dest='stop', action='store_true', help='Stop the daemon')
    p.add_option('-p', dest='port', action='store', type="int", help='specify port')
    options, args = p.parse_args()
    if options.stop:
        Daemon().stop()
        sys.exit()

    port = 8888
    if options.port: port = options.port
    s=SparkServer(('',port),SparkHTTPRequestHandler)

    if options.daemon:
        class sparkdaemon(Daemon):
            def run(self): s.serve_forever()
        sparkdaemon().start()
    else:
        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        logging.getLogger('').addHandler(console)
        print "press Control-C to stop the server"
        s.serve_forever()
