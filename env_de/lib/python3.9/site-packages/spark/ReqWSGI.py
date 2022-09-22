from spark.lib.ReqBase import ReqBase
import sys,time
class ReqWSGI(ReqBase):
	def __init__(self,env,start_response):
		self.env = env
		self.start_response = start_response
		ReqBase.__init__(self)
		self.headers['status']='200 OK'

	def run(self):
		ReqBase.run(self)
		if type(self.data) == type([]):
			#very slow,  newlines are not added if
			# just return self.data
			return ['\n'.join(self.data)]
		else: return [self.data]

	def _setup_vars(self):
		self._setup_vars_from_std_env()

	def _setup_form(self):
		import cgi
		form = cgi.FieldStorage(fp=self.env['wsgi.input'],
			environ=self.env, keep_blank_values=1)
		self.form = {}
		for field in form.list:
			if field.filename: val = File(field)
			else: val = field.value
			if self.form.has_key(field.name):
				self.form[field.name].append(val)
			else: self.form[field.name] = [val]
		for name,val in self.form.items():
			if len(val) == 1: self.form[name] = val[0]

	def write(self,data):
		pass

	def process_headers(self):
		head = []
		status = ""
		has_ct = False
		for header in self.headers:
			if header == "status":
				status = self.headers[header]
			else:
				head.append((header,self.headers[header]))
				if header == "content-type":
					has_ct = True
		if not has_ct:
			head.insert(0,("Content-type","text/html"))
		self.start_response(status,head)
				
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
		self.headers["Status"] ="302"
		self.headers["Location"] = redi
		return ['']
		
	def print_exception(self, type=None, value=None, tb=None, limit=None):
		self.process_headers()
		if self.spark_conf.has_key('debug') and self.spark_conf['debug']:
			if type is None:
				type, value, tb = sys.exc_info()
			import traceback
			self.data.append("<h3>Traceback (most recent call last):</h3>\n")
			list = traceback.format_tb(tb, limit) + \
				   traceback.format_exception_only(type, value)
			self.data.append("<pre>%s<strong>%s</strong></pre>\n" % ("".join(list[:-1]), list[-1]))
			del tb
		else:
			self.data.append('An error occured!')
		return self.data

