#!/usr/bin/env python

#for create users for Sparkblog

import sha, getpass, sys, os.path
sys.path.append(os.path.realpath(os.path.dirname(os.path.realpath(__file__))+"/../.."))


userdata = {}
fp = 'admin_passwd'
if os.path.exists(fp):
	passwdf = open(fp,'r')
	for line in passwdf: 
		i = line.split(':')
		if len(i)>1: userdata[i[0]]=i[1]
	passwdf.close()

name = raw_input("Enter your username: ")
if len(name)<2:
        print "Username too short!"
        sys.exit()

password1 = getpass.getpass("Enter your password(>5): ")
if len(password1)<5:
        print "password too short!"
        sys.exit()
password1 = sha.new(password1).hexdigest()
password2 = getpass.getpass("Enter password again: ")
password2 = sha.new(password2).hexdigest()
if password1 != password2:
	print "passwords not match!"
	sys.exit()
	
userdata[name]=password1
passwdf = open(fp,'w')
for i in userdata: 
	passwdf.write("%s:%s"%(i,userdata[i]))
passwdf.close()
print "User created."

