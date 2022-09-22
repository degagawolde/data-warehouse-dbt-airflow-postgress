def index(r):
	import os.path
	return """Hello, your Spark site works!<br />
The file that display this page is "%s".<br />
You can change default controller and action in file 
"%s/__init__.py".<br /><br />
Spark online docs: 
<a href="http://pytan.com/doc/">http://pytan.com/doc/</a>
	""" %(os.path.realpath(__file__),os.path.realpath(os.path.dirname(__file__)))
