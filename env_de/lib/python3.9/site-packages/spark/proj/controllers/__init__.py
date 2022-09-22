#1: display debug error info, 0:display 500 internal error
debug = 1

#this is controller/action to be called when none specified in url
default_action= ["default","index"]

#define regular expression url patterns
#e.g. ['^car\/','vehicle'] means url /car/ will be handled by
# "index" method in "vehicle_controller"
#  ['^\d{4}\/\d{2}','blog','month'] means url /2006/02/ will be handled by
# "month" method in "blog_controller"
#the order is important, first match is honored.
#see document for more details
uripatterns = [
]

admin = {
	"dbsetting":{
		'dbname':'',
		'user':'root',
		'password':'',
	},
	"rowsperpage":5,
	"tmpdir":'/tmp',
}

import os.path
#tmpl_dir is default template directory
#cache_dir is default cache directory
#you can overwrite them here, or you can define them in 
# individual controller
tmpl_dir = os.path.join(os.path.dirname(__file__),'..','templates')
cache_dir = os.path.join(os.path.dirname(__file__),'..','cache')
