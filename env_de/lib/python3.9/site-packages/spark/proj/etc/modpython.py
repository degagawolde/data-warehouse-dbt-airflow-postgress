""" Mod_python handler
if debug in command line, use path seperated by space, for example, 
if we want to look at http://localhost/python/hello/world
we can use command line:
python modpython.py python hello world
"""
if __name__ == '__main__':
	import sys,os.path
	sys.path.insert(0,os.path.abspath('../..'))
	class Fakereq(object):
		def __init__(self,stdout):
			self.stdout=stdout
			self.write = self.stdout.write
			self.subprocess_env = {}
			self.headers_out = {}
		def add_common_vars(self):pass

from spark.ReqModPython import ReqModPython

def handler(req):
	return ReqModPython(req).run()

if __name__ == '__main__':
	fakereq = Fakereq(sys.stdout)
	if len(sys.argv) > 1:
		fakereq.subprocess_env['SCRIPT_NAME'] = sys.argv[1]
		fakereq.subprocess_env['PATH_INFO'] = ''
		for i in range(2,len(sys.argv)):
			fakereq.subprocess_env['PATH_INFO'] += sys.argv[i]+'/'
	ReqModPython(fakereq,False).run()
