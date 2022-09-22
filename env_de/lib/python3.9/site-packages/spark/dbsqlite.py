r"""
Spark dbsqlite - a wrapper to python-sqlite
Copyright (c) 2006 Wensheng Wang
"""
try: import sqlite3 as sqlite
except ImportError:
	try: from pysqlite2 import dbapi2 as sqlite
	except ImportError:
		raise "No pysqlite2 or sqlite3"

class GetterDict(dict):
	def __init__(self,d={}):
		self.update(d)
		self.__dict__.update(d)

class DbSpark:
	def __init__(self, db='', cursortype = 'd'):
		#pysqlite2 has row_factory - sqlite.Row
		#bu we don't use it because we can't dict() it
		if cursortype == 'l': self.resulttype = 0
		elif cursortype == 'o': self.resulttype = 2
		else: self.resulttype = 1
			
		self.conn = sqlite.connect(db)
		self.commit = self.conn.commit

	def q(self, query):
		self.cursor = self.conn.execute(query)
		return self.cursor

	def qone(self, query):
		v = self.q(query).fetchone()
		if self.resulttype==1:
			return dict(zip(self.desc(),v))
		if self.resulttype==2:
			return GetterDict(zip(self.desc(),v))
		else:
			return v
		
	def qall(self, query):
		vlist = self.q(query).fetchall()
		if self.resulttype==1:
			return [dict(zip(self.desc(),v)) for v in vlist]
		if self.resulttype==2:
			return [GetterDict(zip(self.desc(),v)) for v in vlist]
		else:
			return vlist

	def desc(self):
		return [c[0] for c in self.cursor.description]

	def escape(self,string):
		return string.replace("'","''")

	def insert_id(self):
		return self.cursor.lastrowid
