#!/bin/env python

import sys, os.path
import cgitb; cgitb.enable()

sys.path.append(os.path.realpath(os.path.join(os.path.dirname(__file__),'..','..')))
from spark.lib.ReqWSGI import ReqWSGI

def handle_request(env, start_response):
    return ReqWSGI(env,start_response).run()

try:
	from flup.server.fcgi_fork import WSGIServer
except ImportError:
	print "Please install Flup (http://www.saddi.com/software/flup/)"
	sys.exit()
WSGIServer(handle_request).run()
