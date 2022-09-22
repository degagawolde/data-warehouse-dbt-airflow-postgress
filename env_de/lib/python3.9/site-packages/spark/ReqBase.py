"""
	ReqBase for Spark
"""

import sys
from types import FunctionType

class ReqBase:
	def __init__(self):
		"""will be called at the END of subclass contructor
		"""
		self._setup_vars()
		self._setup_form()
		self.data=''
		self.error=[]

		self.headers = {}
		self.gzip_ok = False
		self.headers['Content-type'] = 'text/html'
		self.headers['Status'] = '200'
		self.redi_page = ''
		self.uripath = '/'

		if self.is_ssl:
			self.proto='https'
		else:
			self.proto='http'
		if self.server_port:
			if (self.server_port == '80' and not self.is_ssl) \
			  or (self.server_port == '443' and self.is_ssl):
				self.server_port = ''
			else:
				self.server_port = ':'+self.server_port

		self.host_path="%s://%s%s" % (self.proto,self.server_name,self.server_port)
		#if len(self.script_name):
		#	self.host_path ="%s/%s" % (self.host_path,'/'.join(self.script_name))

		self.spark_conf = {}
		import controllers
		for k in dir(controllers):
			if not k[0:2] == '__':
				self.spark_conf.update({k:getattr(controllers,k)})

	def _setup_vars(self):
		import os
		self.env = os.environ
		self._setup_vars_from_std_env()

	def _setup_form(self):
		import cgi
		form = cgi.FieldStorage()
		self.form = {}
		for key in form:
			self.form[key] = form.getvalue(key,'')

	def _setup_vars_from_std_env(self):
		""" Sets the common HTTPD environment
		Will be used by Modpython and WSGI, but NOT twisted
		"""
		self.http_accept_language = self.env.get('HTTP_ACCEPT_LANGUAGE', 'en')
		self.server_name = self.env.get('SERVER_NAME', 'localhost')
		self.server_port = self.env.get('SERVER_PORT', '')
		self.http_host = self.env.get('HTTP_HOST','localhost')
		self.http_referer = self.env.get('HTTP_REFERER', '')
		self.saved_cookie = self.env.get('HTTP_COOKIE', '')
		self.script_name = self.env.get('SCRIPT_NAME', '')
		self.path = self.env.get('PATH_INFO', '')
		self.query_string = self.env.get('QUERY_STRING', '')
		self.request_method = self.env.get('REQUEST_METHOD', None)
		self.remote_addr = self.env.get('REMOTE_ADDR', '')
		self.accept_encoding = self.env.get('HTTP_ACCEPT_ENCODING', '')
		self.http_user_agent = self.env.get('HTTP_USER_AGENT', '')
		self.is_ssl = self.env.get('SSL_PROTOCOL', '') != '' \
			or self.env.get('SSL_PROTOCOL_VERSION', '') != '' \
			or self.env.get('HTTPS', 'off') == 'on'

		#name_path_info is last part of script_name plus path_info
		#without the first item 
		self.script_name=[v for v in self.script_name.split('/') if v != '']
		self.path = [v for v in self.path.split('/') if v != '']
		#for base / for uri /hello/world
		#on Modpython, script_name is "hello", path_info is "world"
		#for base /newcgi, for uri /newcgi/hello/world,
		#on CGI, script_name=['newcgi'],path_info=['hello']
		#on Modpython, script_name is newcgi/hello path_info = 'world'
		#So for ModPython, we need to get last part of script_name and toghter with path_info
		#to form real path_info
		if self.accept_encoding == 'gzip':
			self.gzip_ok = True

	def show(self):
		self.process_headers()
		if self.data: self.write(self.data)
		else: self.write('')

	def write(self, data):
		if type(data) == list:
			sys.stdout.write('\r\n'.join(data))
		else:
			sys.stdout.write(data)

	def process_headers(self):
                for header in self.headers:
                        self.write("%s: %s\r\n" % (header,self.headers[header]))
                self.write('\r\n')

	def get_contact(self):
		if not self.path:
			if self.spark_conf.has_key('default_action') and self.spark_conf['default_action']:
				if len(self.spark_conf['default_action'])>1 and self.spark_conf['default_action'][1]:
					return self.spark_conf['default_action']
				else:
					return [self.spark_conf['default_action'][0],"index"]
			else:
				return ["default","index"]
		path = '/'.join(self.path)
		if self.spark_conf.has_key('uripatterns') and self.spark_conf['uripatterns']:
			import re
			for p in self.spark_conf['uripatterns']:
				if re.match(p[0],path):
					if len(p)<2: return ["default","index"]
					elif len(p)<3: return [p[1],"index"]
					else: return [p[1],p[2]]

		if len(self.path)>1:
			return self.path[0:2]
		else:
			return [self.path[0],"index"]

	def run(self):
		#self.data = str(self.path)
		#self.show()
		#return self.finish()
		controller,action = self.get_contact()
		controller = controller.lower()
		conf = "controllers."+controller+"_controller"

		try:
			self.con_mod = __import__(conf,'','',[''])
		except ImportError:
			return self.print_exception()
			
		if hasattr(self.con_mod,action) and isinstance(self.con_mod.__dict__[action],FunctionType):
			data = getattr(self.con_mod,action)(self)
			#if type(data)==str or type(data)==list:
			#	# apply some filters here?
			#	self.data = data
			if data: self.data = data
		else:
			self.data = "No action method '%s' in controller '%s' " % (action,controller)

		self.show()
		return self.finish()


	def finish(self):
		pass

	def print_exception(self, type=None, value=None, tb=None, limit=None):
		self.process_headers()
		if self.spark_conf.has_key('debug') and self.spark_conf['debug']:
			if type is None:
				type, value, tb = sys.exc_info()
			import traceback
			self.write("<h3>Traceback (most recent call last):</h3>\n")
			list = traceback.format_tb(tb, limit) + \
				   traceback.format_exception_only(type, value)
			self.write("<pre>%s<strong>%s</strong></pre>\n" % ("".join(list[:-1]), list[-1]))
			del tb
		else:
			self.write('An error occured!')
		return self.finish()

	def get_cookie(self,coname):
		import Cookie
		cookie = Cookie.SimpleCookie(self.saved_cookie)
		if cookie.has_key(coname):
			return cookie[coname].value
		else:
			return ''

	def set_cookie(self,coname,codata,expires=None):
		import time
		if expires:
			expirestr = time.strftime("%A, %d-%b-%Y %H:%M:%S GMT", time.gmtime(expires))
		else:
			expirestr = " "
		self.headers['Set-Cookie'] = '%s="%s"; expires=%s; path=/;' % (coname,codata,expirestr)
	
	def redirect(self,redi):
		#the built-in server can not handle redirect
		self.data = """<html><head><meta http-equiv="refresh" content="0;url=%s"></head>
			<body><a href="%s">redirect</a></body></html>"""%(redi,redi)

	# conviniently provide a Sprite instance
	def sprite(self,tmpf):
		tmpl_dir = self.spark_conf.get('tmpl_dir','')
		cache_dir = self.spark_conf.get('cache_dir','')
		import spark.sprite
		return spark.sprite.Sprite(tmpf,tmpl_dir,cache_dir)
		  
