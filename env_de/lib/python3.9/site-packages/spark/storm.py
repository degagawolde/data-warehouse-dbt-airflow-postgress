r"""Storm - Spark's Tiny Object Relation Mapper(ORM)
"""

import string, new
from types import *

#the idea regarding to "belongs_to" and "has_many" comes from
#http://blog.ianbicking.org/more-on-python-metaprogramming-comment-14.html
#by brantley, the whole discussion is very interesting and inspiring
bag_belongs_to = []
bag_has_many = []
def belongs_to(what): bag_belongs_to.append(what)
def has_many(what): bag_has_many.append(what)

class MetaRecord(type):
	def __new__(cls, name, bases, dct):
		global bag_belongs_to, bag_has_many
		if name in globals(): return globals()[name]
		else:
			Record = type.__new__(cls, name, bases, dct)
			for i in bag_belongs_to: Record.belongs_to(i)
			for i in bag_has_many: Record.has_many(i)
			bag_belongs_to = []
			hag_has_many = []
			return Record


class Storm(dict):
	__metaclass__ = MetaRecord
	__CONN = None

	@classmethod
	def belongs_to(cls, what):
		def dah(self):
			belong_cls = globals().get(what,None)
			if not belong_cls:
				#we probably should raise error instead!!!
				belong_cls = type(what,(Storm,),{})
			return belong_cls.selectone(self[what+'_id'])

		setattr(cls,what,new.instancemethod(dah,None,cls))
		
	@classmethod
	def has_many(cls, what):
		def dah(self):
			hasmany_cls = globals().get(what,None)
			if not hasmany_cls:
				#we probably should raise error instead!!!
				hasmany_cls = type(what,(Storm,),{})
			dct={}
			dct[string.lower(cls.__name__)+'_id']=self['id']
			return hasmany_cls.select(**dct)

		setattr(cls,what,new.instancemethod(dah,None,cls))

	#Class method to establish connection
	@classmethod
	def conn(cls, **kwds):
		if cls.__CONN: return
		if 'driver' in kwds: driver = kwds.pop('driver')
		else: driver = 'mysql'
		import sys, os.path
		sys.path.insert(0,os.path.dirname(__file__))
		cls.__CONN = __import__('db'+driver).DbSpark(**kwds)

	@classmethod
	def exe(cls,s):
		if not cls.__CONN: raise "Database not connected"
		return cls.__CONN.qall(s)

	@classmethod
	def insert(cls,**kwds):
		vs = [[k,cls.__CONN.escape(str(kwds[k]))] for k in kwds]
		if vs:
			s = "insert into %s (%s) values ('%s')" % (
			  string.lower(cls.__name__),
			  ','.join([v[0] for v in vs]),
			  "','".join([v[1] for v in vs])
			  )

			cls.__CONN.q(s)
			insert_id = cls.__CONN.insert_id()
			cls.__CONN.commit()
			return insert_id
		else:
			raise "nothing to insert"

	@classmethod
	def select(cls,*args, **kwds):
		"""if only a int argument, select * by id
		"""
		if len(args)==1 and (type(args[0])==IntType or type(args[0])==LongType):
			q = "select * from %s where id='%s'"%(string.lower(cls.__name__),args[0])
			where = "where id='%s'"%args[0]
		else:
			if args: s = ",".join(args)
			else: s = "*"

			if kwds:
				c,limit,orderby = [],'',''
				for k in kwds:
					if k == 'limit': limit = "limit %s"%kwds[k]
					elif k == 'order': orderby = "order by %s"%kwds[k]
					else: c.append(k+"='"+str(kwds[k])+"'")
				where = " and ".join(c)
				if where: where = "where %s"%where
				where = "%s %s %s"%(where,orderby,limit)
			else: where = ""

			q = " ".join(['select',s,'from',string.lower(cls.__name__),where])

		r = cls.__CONN.qall(q)
		list = []
		for i in r:
			list.append(cls(i))
			list[-1].__dict__['where'] = where
		return list

	@classmethod
	def selectone(cls,*args, **kwds):
		r = cls.select(*args,**kwds)
		if r: return r[0]
		else: return {}

	@classmethod
	def update(cls,cond,**kwds):
		"""If cond is int, imply "where id=cond".
		If cond is str, put it afer "where" directly.
		user can use update('1=1') for global update
		"""

		if not cond or not kwds: raise "Update What?!"

		if type(cond) == IntType: w = "id='%d'" % cond
		else: w = cond

		vs = [[k,cls.__CONN.escape(str(kwds[k]))] for k in kwds]

		if vs:
			s = "UPDATE %s SET %s WHERE %s" % (
			  string.lower(cls.__name__),
			  ','.join(["%s='%s'"%(v[0],v[1]) for v  in vs]),
			  w
			  )

			#return s #for debug
			cls.__CONN.q(s)
			cls.__CONN.commit()

	@classmethod
	def delete(cls,id):
		if type(id) == IntType:
			cls.__CONN.q("delete from %s where id='%d'"%
			  (string.lower(cls.__name__),id)
			  )
			cls.__CONN.commit()
		else:
			raise "Only accept integer argument"

	def __init__(self,dct={}):
		if not self.__class__.__CONN: raise "Database not connected"

		dict.__init__(self,dct)
                #classname should be same as table name
		#direct assign will call __getattr__, and will recurse
		self.__dict__['cur_table']= string.lower(self.__class__.__name__)
		self.__dict__['where']= ''
		self.__dict__['sql_buff']={}

	def sql(self,sql):
		self.__class__.__CONN.q(sql)
		
	def save(self):
		#update or insert depend on self.where
		s = ""
		if self.where:
			f = []
			for v in self.sql_buff:
				f.append("%s='%s'"%(v,self.sql_buff[v]))
			s = "UPDATE %s SET %s %s" % (
			  self.cur_table, ','.join(f), self.where
			  )
		else:
			f,i=[],[]
			for v in self.sql_buff:
				f.append(v)
				i.append(self.sql_buff[v])
			if f and i:
				s = "INSERT INTO %s (%s) VALUES ('%s')" % (
				  self.cur_table, ','.join(f), "','".join(i)
				  )

		if s:
			self.__class__.__CONN.q(s)
			self.__class__.__CONN.commit()
		else: raise "nothing to insert"
		

	def __setattr__(self,attr,value):
		"""
		put cmds to sql buffer, to be excuted by save, destroy later
		"""
		if attr in self.__dict__:
			self.__dict__[attr]=value
		else: 
			v = self.__class__.__CONN.escape(str(value))
			self.__dict__['sql_buff'][attr] = v
			self[attr] = v

	def __getattr__(self,attr):
		"""get the first of current result"""
		if attr in self.__dict__: return self.__dict__[attr]
		try: return self[attr]
		except KeyError: pass
		raise AttributeError

__all__ = ['Storm', 'belongs_to', 'has_many']
