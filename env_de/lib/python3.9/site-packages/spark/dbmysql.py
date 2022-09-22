r"""
SparkMysql - a wrapper to python-MySQL
Copyright (c) 2005 Wensheng Wang
"""

import MySQLdb, MySQLdb.cursors

class GetterDict(dict):
	def __init__(self,d={}):
		self.update(d)
		self.__dict__.update(d)

class DbSpark:
	def __init__(self, db='', host='localhost', user='root', passwd='', cursortype = 'd'):
		self.use_getter = 0
		cursor = MySQLdb.cursors.DictCursor
		if cursortype == 'o':
			self.use_getter = 1
		elif cursortype == 'l':
			cursor = MySQLdb.cursors.Cursor
			
		self.conn = MySQLdb.connect(
			host   = host,
			user   = user,
			passwd = passwd,
			db     = db,
			cursorclass = cursor
			)

		if self.conn:
			self.cursor = self.conn.cursor()
			self.q =  self.cursor.execute
			self.one =  self.cursor.fetchone
			self.all =  self.cursor.fetchall
			self.escape = self.conn.escape_string
			self.commit = self.conn.commit
			self.insert_id = self.conn.insert_id
		else:
			self.cursor = None
			
	def qone(self,query):
		self.q(query)
		if self.use_getter:
			return GetterDict(self.cursor.fetchone())
		else:
			return self.cursor.fetchone()
		
	def qall(self,query):
		self.q(query)
		if self.use_getter:
			return [ GetterDict(d) for d in self.cursor.fetchall()]
		else:
			return self.cursor.fetchall()
	
	def desc(self):
		return [c[0] for c in self.cursor.description]

