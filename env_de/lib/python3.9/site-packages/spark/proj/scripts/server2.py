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
import time
import urllib
import cgi
import shutil
import select
import mimetypes
import logging
import errno
from cStringIO import StringIO

proj_dir = os.path.abspath(os.path.join(os.path.dirname(__file__),'..'))

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s',
		datefmt='%m-%d %H:%M', 
		filename=os.path.join(proj_dir,'log','spark_server.log'),
                filemode='w')

class SparkHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    # Determine platform specifics
    have_fork = hasattr(os, 'fork')
    have_popen2 = hasattr(os, 'popen2')
    have_popen3 = hasattr(os, 'popen3')

    # Make rfile unbuffered -- we need to read one line and then pass
    # the rest to a subprocess, so we can't use buffered input.
    rbufsize = 0

    static_directories = {'/public':os.path.join(proj_dir,'public')}
    the_script = os.path.join(proj_dir,'etc','cgiserver.py')

    if not os.path.exists(the_script) or not os.path.isfile(the_script):
        print "script missing"
        sys.exit()

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

    def guess_type(self, path):
        base, ext = posixpath.splitext(path)
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        ext = ext.lower()
        if ext in self.extensions_map:
            return self.extensions_map[ext]
        else:
            return self.extensions_map['']

    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.py': 'text/plain',
        })

    def log_message(self, format, *args):
        """Log an arbitrary message.

        This is used by all other logging functions.  Override
        it if you have specific logging wishes.

        The first argument, FORMAT, is a format string for the
        message to be logged.  If the format string contains
        any % escapes requiring parameters, they should be
        specified as subsequent arguments (it's just like
        printf!).

        The client host and current date/time are prefixed to
        every message.

        """
        #sys.stderr.write("%s - - [%s] %s\n" %
        #                 (self.address_string(),
        #                  self.log_date_time_string(),
        #                  format%args))
        logging.info(format%args)

    def run_cgi(self):
        rest = self.path
        i = rest.rfind('?')
        if i >= 0:
            rest, query = rest[:i], rest[i+1:]
        else:
            query = ''

        scriptfile = self.the_script
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

        #the followings are directly copied from CGIHTTPServer.py
        if self.have_fork:
            # Unix -- fork as we should
            #args = [scriptfile]
            #if '=' not in decoded_query:
            #    args.append(decoded_query)
            self.wfile.flush() # Always flush before forking
            pid = os.fork()
            if pid != 0:
                # Parent
                pid, sts = os.waitpid(pid, 0)
                # throw away additional data [see bug #427345]
                while select.select([self.rfile], [], [], 0)[0]:
                    if not self.rfile.read(1):
                        break
                if sts:
                    self.log_error("CGI script exit status %#x", sts)
                return
            # Child
            try:
                os.dup2(self.rfile.fileno(), 0)
                os.dup2(self.wfile.fileno(), 1)
                os.execve(scriptfile, [], os.environ)
            except:
                self.server.handle_error(self.request, self.client_address)
                os._exit(127)

        elif self.have_popen2 or self.have_popen3:
            # Windows -- use popen2 or popen3 to create a subprocess
            if self.have_popen3:
                popenx = os.popen3
            else:
                popenx = os.popen2
            cmdline = scriptfile
            interp = sys.executable
            if interp.lower().endswith("w.exe"):
                # On Windows, use python.exe, not pythonw.exe
                interp = interp[:-5] + interp[-4:]
            cmdline = '%s -u "%s"' % (interp, cmdline)
            if '=' not in query and '"' not in query:
                cmdline = '%s "%s"' % (cmdline, query)
            self.log_message("command: %s" , cmdline)
            try:
                nbytes = int(length)
            except (TypeError, ValueError):
                nbytes = 0
            files = popenx(cmdline, 'b')
            fi = files[0]
            fo = files[1]
            if self.have_popen3:
                fe = files[2]
            if self.command.lower() == "post" and nbytes > 0:
                data = self.rfile.read(nbytes)
                fi.write(data)
            # throw away additional data [see bug #427345]
            while select.select([self.rfile._sock], [], [], 0)[0]:
                if not self.rfile._sock.recv(1):
                    break
            fi.close()
            shutil.copyfileobj(fo, self.wfile)
            if self.have_popen3:
                errors = fe.read()
                fe.close()
                if errors:
                    self.log_error('%s', errors)
            sts = fo.close()
            if sts:
                self.log_error("CGI script exit status %#x", sts)
            else:
                self.log_message("CGI script exited OK")

        else:
            # Other O.S. -- execute script in this process
            save_argv = sys.argv
            save_stdin = sys.stdin
            save_stdout = sys.stdout
            save_stderr = sys.stderr
            try:
                save_cwd = os.getcwd()
                try:
                    sys.argv = [scriptfile]
                    if '=' not in decoded_query:
                        sys.argv.append(decoded_query)
                    sys.stdout = self.wfile
                    sys.stdin = self.rfile
                    execfile(scriptfile, {"__name__": "__main__"})
                finally:
                    sys.argv = save_argv
                    sys.stdin = save_stdin
                    sys.stdout = save_stdout
                    sys.stderr = save_stderr
                    os.chdir(save_cwd)
            except SystemExit, sts:
                self.log_error("CGI script exit status %s", str(sts))
            else:
                self.log_message("CGI script exited OK")


class Daemon(object):

    uid, gid = os.getuid(), os.getgid()
    pidfile = os.path.join(proj_dir,'log','spark_pid')

    def run(self): pass

    def start(self):
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
