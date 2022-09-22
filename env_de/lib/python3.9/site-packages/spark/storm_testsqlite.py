import sys
from storm import *

class User(Storm):
	has_many('said')

class Said(Storm):
	belongs_to('user')

def storm_test():
	"""Test Storm ORM
	Unittest can not be used because testcases can not 
	be run independently
	"""

	###################################################
	#SetUp
	#
	Storm.conn(driver='sqlite',db='sqlite_test.db')
	User.exe("""create table user(
		id integer primary key,
		username varchar(32) not null,
		firstname varchar(32) not null default '',
		lastname varchar(32) not null default '',
		email varchar(64) not null default ''
		)"""
	)
	User.exe("""create table said(
		id integer primary key,
		user_id int not null,
		quote tinytext not null default ''
		)"""
	)
	
	###################################################
	#Insert data using instance
	#
	dbo = User()
	dbo.username = "gwash"
	dbo.firstname = "George"
	dbo.lastname = "Washngton"
	dbo.email = "george.washington@whitehouse.org"
	dbo.save()

	b = Said()
	b.user_id = 1
	b.quote = "It is far better to be alone, than to be in bad company. "
	b.save()
	
	###################################################
	#Insert data using classmethod
	#
	User.insert(username="jadams",firstname="John",lastname="Adams")
	User.insert(username="tjeff",firstname="Tom",lastname="Jefferson")

	#re-use b
	b.user_id = 3
	b.quote = "Honesty is the first chapter in the book of wisdom."
	b.save()
	b.user_id = 3
	b.quote = "I find that the harder I work, the more luck I seem to have."
	b.save()

	###################################################
	# Test belongs_to association
	#
	c = Said.selectone(1)
	d = c.user()
	assert('Washngton' == d.lastname)

	###################################################
	#select one by id, then update and save
	o3 = User.selectone(3)
	assert("where id='3'" == o3.where)
	assert('tjeff' == o3.username)
	assert('Jefferson' == o3.lastname)
	assert('Tom' == o3.firstname)
	o3.firstname= "Thomas"
	assert(o3.sql_buff == {'firstname':'Thomas'})
	o3.save()

	ss = o3.said()
	print "%s %s said:" % (o3.firstname,o3.lastname)
	for s in ss:
		print s.quote
	
	###################################################
	#Select one row by column
	#
	o2 = User.selectone(firstname="John")
	assert('jadams' == o2.username)
	assert('John' == o2.firstname)
	del o2


	###################################################
	#Update by classmethod
	#
	User.update("username='gwash'",lastname="Washington")

	###################################################
	# delete by classmethod
	#
	User.delete(2)

	###################################################
	#Select all, save is impossible
	#
	all = User.select()
	assert('Washington' == all[0].lastname)
	assert('Washington' == all[0]['lastname'])
	assert('George' == all[0].firstname)
	assert('Jefferson' == all[1].lastname)
	assert('Thomas' == all[1].firstname)
	

	###################################################
	#tearDown
	#
	#User.exe("drop database if exists sToRm_TeSt")

	print "Test Passed!"

if __name__ == '__main__':
	storm_test()
