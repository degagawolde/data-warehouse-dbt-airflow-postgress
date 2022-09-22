""" the name of cookie is hardcoded for now: 
spark_sid for file, and pytan_sid for db
there should be a sessions table exist in the current database,
its structure is:
+----------------+--------------+------+-----+---------+-------+
| Field          | Type         | Null | Key | Default | Extra |
+----------------+--------------+------+-----+---------+-------+
| session_id     | varchar(32)  |      | PRI |         |       |
| session_data   | text         |      |     |         |       |
| session_time   | int(10)      |      |     | 0       |       |
| session_expire | int(10)      |      |     | 0       |       |
+----------------+--------------+------+-----+---------+-------+

Sessions will not be clean up unless delete() is called, e.g., 
user logs out.  But users usually do not explictly log out.
if no automatic cleanup is implemented at application code,
we need to periodically clean up session table/dir, with a 
script or something.

Automatic cleanup in the following classes is not possible,
because sessions is de-coupled from application (e.g. users table).
Session has no idea of user_id, and IP can not be used because 
different users can have the same IP.
"""

import os, time, md5, random, cPickle, base64

class SparkSession(dict):
	def __init__(self, req, timeout=86400):

		self.timeout = timeout
		self.accessed = 0
		self.req = req

		dict.__init__(self)

		# self.cookie_name must be provided by subclass
		# for now:
		# spark_sid for file, and pytan_sid for db
		self.sid = self.req.get_cookie(self.cookie_name)

		if self.sid:
			if len(self.sid) != 32: raise "COOKIE_ERROR"
			if not self.load_sdata():
				self.sid = ''
	
		if not self.sid:
			t = time.time()
			pid = os.getpid()
			rnd1 = random.randrange(0,int(t))
			rnd2 = random.randrange(0,int(t))
			ip = req.remote_addr
			self.sid = md5.new("%d%d%d%d%s"%(t,pid,rnd1,rnd2,ip)).hexdigest()
			self.req.set_cookie(self.cookie_name,self.sid)

		self.accessed = int(time.time())


	def load_sdata(self):
		raise "Not implemented error"
			
	def save(self):
		dict = { "data": self.copy(),
			"accessed": self.accessed,
			"timeout": self.timeout}
		self.do_save(dict)

	def do_save(self,dict): raise "Not Implemented Error"
		
	def destroy(self):
		self.delete()
		expires = time.time() - 86400
		self.req.set_cookie(self.cookie_name,self.sid,expires)

	def delete(self): raise "Not Implemented Error"


class SessionDb(SparkSession):
	def __init__(self,req,db,timeout=3600):
		self.db = db
		self.cookie_name = "pytan_sid"
		SparkSession.__init__(self,req,timeout=timeout)

	def load_sdata(self):
		sql = """SELECT * FROM sessions
			WHERE session_id = '%s' 
			""" % (self.sid)
		session_data = self.db.qone(sql)

		if not session_data: return 0
		sdata = session_data['session_data']+'\n'
		sdata = cPickle.loads(base64.decodestring(sdata))
		if (time.time() - sdata['accessed']) > sdata['timeout']:
			self.delete()
			return 0
		self.timeout = sdata["timeout"]
		self.update(sdata["data"])
		return 1

	def do_save(self,dict):
		sql = """REPLACE INTO sessions
			(session_id, session_data, session_time)
			VALUES ('%s','%s','%d')
		   """ % (self.sid, 
			base64.encodestring(cPickle.dumps(dict))[:-1],
			self.accessed
			)

		self.db.q(sql)

	def delete(self):
		sql = """DELETE FROM sessions
			WHERE session_id = '%s'
		   """ % (self.sid)
		self.db.q(sql)


class SessionFile(SparkSession):
	def __init__(self,req,sessdir,timeout=3600):
		self.sessdir = sessdir
		self.cookie_name = "spark_sid"
		SparkSession.__init__(self,req,timeout=timeout)

	def load_sdata(self):
		fp = os.path.join(self.sessdir,'sparksessf_'+self.sid)
		if os.path.exists(fp): session_file = open(fp,'rb')
		else: return 0
		sdata = cPickle.load(session_file)
		if (time.time() - sdata['accessed']) > sdata['timeout']:
			self.delete()
			return 0
		self.timeout = sdata["timeout"]
		self.update(sdata["data"])
		return 1

	def do_save(self,dict):
		session_file = open(os.path.join(self.sessdir,'sparksessf_'+self.sid),'wb')
		cPickle.dump(dict,session_file,1)
		session_file.close()

	def delete(self):
		fp = os.path.join(self.sessdir,'sparksessf_'+self.sid)
		if os.path.exists(fp): os.remove(fp)
