#!/usr/bin/env python
import os, sys
import cgitb; cgitb.enable()

spark_proj = os.path.join(os.path.dirname(__file__),'..')
sys.path.insert(0,spark_proj)
#os.putenv('spark_proj',spark_proj)
from spark.ReqBase import ReqBase

if __name__ == '__main__':
	if len(sys.argv) > 1:
		os.environ['PATH_INFO'] = '/'.join(sys.argv[1:])

r = ReqBase()
r.run()
