#import time
from spark.ReqBase import ReqBase
class ReqModPython(ReqBase):
	def __init__(self, req, reallympy=True):
		self.reallympy = reallympy
		self.mpyreq = req
		self.mpyreq.add_common_vars()
		self.mpyreq.content_type = "text/html"
		self.mpyreq.status = 200
		self._have_status = 0
		ReqBase.__init__(self)
		
	def send_header(self):
		pass

	def _setup_vars(self):
		self.env=self.mpyreq.subprocess_env
		self._setup_vars_from_std_env()
		#In modpython, The last of script_name is actually 
		# first part of path_info
		self.path = self.script_name[-1:]+self.path
		if self.script_name: self.script_name.pop()
		
	def _setup_form(self):
		self.form = {}
		if self.reallympy:
			from mod_python import util
			pg_fields = util.FieldStorage(self.mpyreq,1).list
			for field in pg_fields:
				self.form[field.name] = field.value

	def write(self, data):
		if type(data) == type(""):
			self.mpyreq.write(data)
		elif type(data) == type([]):
			if self.gzip_ok:
				import gzip,StringIO
				zbuf = StringIO.StringIO()
				zfile = gzip.GzipFile('wb',zbuf,6)
				zfile.write(''.join(data))
				zfile.close()
				self.mpyreq.write(zbuf.getvalue())
			else:
				self.mpyreq.write('\n'.join(data))
		else:
			self.mpyreq.write(str(data))

	def finish(self):
		return 0

	def process_headers(self):
		for header in self.headers:
			if header == 'content-type':
				self.mpyreq.content_type = self.headers[header]
			elif header == 'status':
				try:
					self.mpyreq.status = int(self.headers[header])
				except:
					self.mpyreq.status = 200
			else:
				self.mpyreq.headers_out[header]=self.headers[header]

	def redirect(self, addr):
		from mod_python import util
		util.redirect(self.mpyreq,addr)

	def get_cookie(self,coname):
		if self.reallympy:
			from mod_python import Cookie
			cookie = Cookie.get_cookies(self.mpyreq)
			if cookie.has_key(coname):
				return cookie[coname].value
			else:
				return ''
		
	def set_cookie(self, coname, codata, expires=None):
		if self.reallympy:
			from mod_python import Cookie
			cookie = Cookie.Cookie(coname,codata)
			#for simplicity
			cookie.path = '/'
			if expires: cookie.expires = expires
			Cookie.add_cookie(self.mpyreq,cookie)

