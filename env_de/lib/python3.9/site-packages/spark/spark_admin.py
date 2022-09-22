import os
import sys
import shutil
import spark
from optparse import OptionParser

join = os.path.join
cur_dir = os.getcwd()
proj_template = join(spark.__path__[0],'proj')
files_dir = join(proj_template,'files')

def main():
	usage = "usage: %prog [options] [args]"
	parser = OptionParser(usage)
	parser.add_option("-c", "--create", type="string", nargs=1, dest="name",
		help="create a new spark project")
	parser.add_option("--demo", choices=('mysql','sqlite'), dest="db_choice",
		help="setup demo wiki controllers and related files\ndb_choice is either mysql or sqlite")
	parser.add_option("--admin", action="store_true", dest="admin",
		help="setup admin controller")

	(options, args) = parser.parse_args()

	if options.name:
		setup_proj(options.name)
	elif options.db_choice:
		setup_demo(options.db_choice)
	elif options.admin:
		setup_admin()
	else:
		print_help(parser)
		
	#try:
	#	action = args[0]
	#except IndexError:
	#	print_help(parser)

def print_help(parser):
	parser.print_help(sys.stderr)
	sys.exit()

def setup_proj(name):
	proj_dir = join(cur_dir,name)
	os.mkdir(proj_dir)
	shutil.copytree(join(proj_template,'scripts'),
		join(proj_dir,'scripts'))
	shutil.copytree(join(proj_template,'etc'),
		join(proj_dir,'etc'))
	os.chmod(join(proj_dir,'etc','cgiserver.py'),0755)
	os.chmod(join(proj_dir,'etc','python.fcgi'),0755)
	shutil.copytree(join(proj_template,'controllers'),
		join(proj_dir,'controllers'))
	os.mkdir(join(proj_dir,'log'))
	os.mkdir(join(proj_dir,'cache'))
	os.chmod(join(proj_dir,'cache'),0777)
	os.mkdir(join(proj_dir,'public'))
	os.mkdir(join(proj_dir,'templates'))
	import spark.sprite
	import socket
	tp1 = spark.sprite.Sprite("apache_modpython.conf",files_dir)
	fw1 = open(join(proj_dir,'etc','apache_modpython.conf'),'w')
	tp1.assign_vars({'proj_dir':proj_dir,'server_name':socket.getfqdn()})
	fw1.write("\n".join(tp1.display(1)))
	fw1.close()
	fw1.close()
	fr2 = open(join(files_dir,'lighttpd_python.conf'))
	fw2 = open(join(proj_dir,'etc','lighttpd_python.conf'),'w')
	fw2.write(fr2.read())
	fr2.close()
	fw2.close()

def setup_demo(db):
	controllers = join(cur_dir,'controllers')
	templates = join(cur_dir,'templates')
	if not (os.path.isdir(controllers) and os.path.isdir(templates)):
		print "You are NOT in a spark project directory"
		sys.exit()
	
	import spark.sprite
	tp1 = spark.sprite.Sprite("wiki_controller.pytp",files_dir)
	fw1 = open(join(controllers,'wiki_controller.py'),'w')
	tp2 = spark.sprite.Sprite("ajaxwiki_controller.pytp",files_dir)
	fw2 = open(join(controllers,'ajaxwiki_controller.py'),'w')

	if db=="mysql":
		try: import MySQLdb
		except ImportError:
			print "you don't have mysql python module installed"
			sys.exit()
		print "You are about to create a database called sparkdemo."
		print "Make sure the user has the priviledge to do that."
		user = raw_input("what's db username? [root] >>")
		if not user: user = "root"
		passwd = raw_input("what's db password? [] >>")
		from spark.dbmysql import DbSpark
		db = DbSpark(user=user,passwd=passwd)
		db.q("""CREATE DATABASE sparkdemo;
			USE sparkdemo;
			CREATE TABLE wiki(
				word VARCHAR(100) NOT NULL UNIQUE,
				content TEXT NOT NULL);"""
		)
		vars_assign = {'driver':'mysql',
			'dbstring':'db="sparkdemo",user="%s",passwd="%s"'%(user,passwd),
			'ismysql':[{}],
		}
		tp1.assign_vars(vars_assign)
		tp2.assign_vars(vars_assign)
	else:
		from spark.dbsqlite import DbSpark
		dbname = join(cur_dir,'etc','sparkdemo.db')
		db = DbSpark(db=dbname)
		db.q("""create table wiki(
		 word VARCHAR NOT NULL UNIQUE,
		 content TEXT NOT NULL)""")
		db.commit()
		vars_assign = {'driver':'sqlite',
			'dbstring':'db="%s"' % dbname,
			}
		tp1.assign_vars(vars_assign)
		tp2.assign_vars(vars_assign)

	fw1.write("\n".join(tp1.display(1)))
	fw1.close()
	fw2.write("\n".join(tp2.display(1)))
	fw2.close()

	try: import simplejson
	except ImportError:
		import spark.contribs.ez_setup as ez_setup
		ez_setup.main(["simplejson"])
	if not os.path.isdir(join(cur_dir,'templates','wiki')):
		os.mkdir(join(cur_dir,'templates','wiki'))
	if not os.path.isdir(join(cur_dir,'public','js')):
		os.mkdir(join(cur_dir,'public','js'))
	shutil.copy(join(files_dir,'wiki.html'),join(cur_dir,'templates','wiki'))
	shutil.copy(join(files_dir,'awiki.js'),join(cur_dir,'public','js'))
	print "For ajaxwiki to work, Dojotoolkit (3.4Mb) is required."
	answer = raw_input("Do you want to download and install Dojo now? [y,n]")
	if answer in ["y", "Y"]:
		dojo_dir = join(cur_dir,'public','js','dojo')
		if not os.path.isdir(dojo_dir): os.mkdir(dojo_dir, 0755)
		dojof = download2temp('http://download.dojotoolkit.org/release-0.3.1/dojo-0.3.1-ajax.zip')
		unzip_install(dojof,dojo_dir)
	else:
		print "you need to manually download Dojo and install it into public/js/dojo"

def download2temp(url):
	import urllib2
	fr = urllib2.urlopen(url)
	size = int(fr.info()['Content-Length'])
	import tempfile
	ftmp = open(tempfile.mktemp(),"w+b")
	import spark.contribs.progress
	meter = spark.contribs.progress.TextMeter()
	meter.start(text="Downloading",size=size)
	i = 0
	while i < size:
		ftmp.write(fr.read(8192))
		i += 8192
		meter.update(i)
	meter.end(size)
	ftmp.seek(0)
	return ftmp

def unzip_install(filename,install_dir):
	"""does NOT work in windows with python 2.4.2, because namelist() doesn't work.
	will fix or work around
	"""
	import zipfile
	zf = zipfile.ZipFile(filename)
	namelist = zf.namelist()
	singletop = True
	first = namelist[0].split('/')[0]
	for name in namelist:
		if not name.startswith(first):
			singletop = False
			break
	for name in namelist:
		names = name.split('/')
		if singletop: names = names[1:]
		if not os.path.isdir( join(install_dir,*names[:-1]) ):
			os.makedirs(join(install_dir, *names[:-1]) )
		if name.endswith('/'): continue
		outfile = open(join(install_dir, *names), 'wb')
		outfile.write(zf.read(name))
		outfile.close()
	

def setup_admin():
	try: import MySQLdb
	except ImportError:
			print "you don't have mysql python module installed"
			sys.exit()

	try: import simplejson
	except ImportError:
		import spark.contribs.ez_setup as ez_setup
		ez_setup.main(["simplejson"])

	create_adminfile()

	controllers = join(cur_dir,'controllers')
	templates = join(cur_dir,'templates')
	if not (os.path.isdir(controllers) and os.path.isdir(templates)):
		print "You are NOT in a spark project directory"
		sys.exit()
	
	import spark.sprite
	tp1 = spark.sprite.Sprite("admin_controller.pytp",files_dir)
	fw1 = open(join(controllers,'admin_controller.py'),'w')
	print "Make sure the user has the priviledge to manage one or more databases."
	user = raw_input("what's database username? [root] >>")
	if not user: user = "root"
	passwd = raw_input("what's database password? [] >>")
	tp1.assign_vars({'dbstring':'user="%s",passwd="%s"'%(user,passwd)})
	fw1.write("\n".join(tp1.display(1)))
	fw1.close()

	if not os.path.isdir(join(cur_dir,'templates','admin')):
		os.mkdir(join(cur_dir,'templates','admin'))
	if not os.path.isdir(join(cur_dir,'public','js')):
		os.mkdir(join(cur_dir,'public','js'))
	if not os.path.isdir(join(cur_dir,'public','admin')):
		os.mkdir(join(cur_dir,'public','admin'))
	shutil.copy(join(files_dir,'table.html'),join(cur_dir,'templates','admin'))
	shutil.copy(join(files_dir,'ajax_tables.css'),join(cur_dir,'public','admin'))
	print "For admin interface to work, Mochikit (291Kb) is required."
	answer = raw_input("Do you want to download and install Mochikit now? [y,n]")
	if answer in ["y", "Y"]:
		mochi_dir = join(cur_dir,'public','js','MochiKit')
		if not os.path.isdir(mochi_dir): os.mkdir(mochi_dir, 0755)
		mochif = download2temp('http://mochikit.com/dist/MochiKit-1.3.1.zip')
		unzip_install(mochif,mochi_dir)
		shutil.copy(join(cur_dir,'public','js','MochiKit','packed','MochiKit','MochiKit.js'),
			join(cur_dir,'public','js','MochiKit'))
	else:
		print "you need to manually download MochiKit and install it into public/js/MochiKit"



def create_adminfile():
	import sha, getpass
	userdata = {}
	fp = join(cur_dir,'etc','admin_passwd')
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

