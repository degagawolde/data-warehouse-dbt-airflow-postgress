#import time
from pytan.lib.ReqBase import ReqBase
class ReqTwisted(ReqBase):
	""" specialized on Twisted requests """

	def __init__(self, req, reactor, properties={}):
		self.twistedreq = req
		self.http_accept_language = self.twistedreq.getHeader('Accept-Language')
		#cookie give me major problem!
		self.saved_cookies={}
		cookietxt = self.twistedreq.getHeader("cookie")
		if cookietxt:
			for c in cookietxt.split(';'):
				cook = c.lstrip()
				eqs=cook.find('=')
				k=cook[0:eqs]
				v=cook[eqs+1:]
				self.saved_cookies[k] = v

		self.reactor = reactor
		self._have_ct = 0
		self._have_status = 0
		self.server_protocol = self.twistedreq.clientproto
		self.server_name = self.twistedreq.getRequestHostname().split(':')[0]
		self.server_port = str(self.twistedreq.getHost()[2])
		self.is_ssl = self.twistedreq.isSecure()
		if self.server_port != ('80', '443')[self.is_ssl]:
			self.http_host = self.server_name + ':' + self.server_port
		else:
			self.http_host = self.server_name
		#self.script_name = [v for v in self.twistedreq.prepath[:-1] if v != '']
		self.script_name = [v for v in self.twistedreq.prepath if v != '']
		self.path_info = [v for v in self.twistedreq.postpath if v != '']
		self.request_method = self.twistedreq.method
		self.remote_host = self.twistedreq.getClient()
		self.remote_addr = self.twistedreq.getClientIP()
		self.http_user_agent = self.twistedreq.getHeader('User-Agent')
		self.request_uri = self.twistedreq.uri
		self.url = self.http_host + self.request_uri # was: self.server_name + self.request_uri

		qindex = self.request_uri.find('?')
		if qindex != -1:
			query_string = self.request_uri[qindex+1:]
		else:
			self.query_string = ''

		ReqBase.__init__(self, properties)


	def run(self):
		ReqBase.run(self)
			
	def get_form(self):
		args = {}
		for key,values in self.twistedreq.args.items():
			if isinstance(values, list) and len(values)==1:
				values = values[0]
			args[key] = values
		return args
				
	def get_vars(self):
		pass
		
	def read(self, n=None):
		""" Read from input stream.
		"""
		self.twistedreq.content.seek(0, 0)
		if n is None:
			rd = self.twistedreq.content.read()
		else:
			rd = self.twistedreq.content.read(n)
		#print "request.RequestTwisted.read: data=\n" + str(rd)
		return rd
	
	def write(self, data):
		for piece in data:
			self.twistedreq.write(piece)
		#if self.header_type == 'html':
		#	self.twistedreq.write(str(time.time()-self.pagestart_time))

	def finish(self):
		self.twistedreq.finish()

	# Headers ----------------------------------------------------------

	def appendHttpHeader(self, header):
		self.user_headers.append(header)

	def __setHttpHeader(self, header):
		#if type(header) is unicode:
		#	header = header.encode('ascii')
		key, value = header.split(':',1)
		value = value.lstrip()
		self.twistedreq.setHeader(key, value)

	def xml_headers(self, more_headers=[]):
		if getattr(self, 'sent_headers', None):
			return
		self.sent_headers = 1
		self.__setHttpHeader("Content-type: application/rss+xml;charset=utf-8")

	def http_headers(self, more_headers=[]):
		if getattr(self, 'sent_headers', None):
			return
		self.sent_headers = 1
		have_ct = 0

		# set http headers
		for header in more_headers + getattr(self, 'user_headers', []):
			if header.lower().startswith("content-type:"):
				# don't send content-type multiple times!
				if have_ct: continue
				have_ct = 1
			self.__setHttpHeader(header)

		if not have_ct:
			self.__setHttpHeader("Content-type: text/html;charset=utf-8")

	def redirect(self, addr):
		if isinstance(addr, unicode):
			addr = addr.encode('ascii')
		self.twistedreq.redirect(addr)

	def setResponseCode(self, code, message=None):
		self.twistedreq.setResponseCode(code, message)
		
	def get_cookie(self, coname):
		return self.saved_cookies.get(coname,'')
				
	def set_cookie(self, coname, codata, expires=None):
		if expires:
			self.twistedreq.addCookie(coname, codata, expires)
		else:
			self.twistedreq.addCookie(coname, codata)
