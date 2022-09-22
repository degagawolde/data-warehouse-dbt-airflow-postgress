#!/usr/bin/env python
import sys, os

p = os.path
spark_root = p.realpath(p.dirname(p.realpath(__file__))+'/..')

commands = {
    'start': 'twistd \
--python %(spark_root)s/scripts/twisted_server.py \
--pidfile %(spark_root)s/log/spark_twisted.pid \
--logfile %(spark_root)s/log/spark_twisted.log \
--no_save \
'%locals(),
    'stop': 'kill `cat %(spark_root)s/log/spark_twisted.pid`'%locals(),
}

def exit(msg):
    print 'Error:', msg
    print __doc__
    sys.exit(1)    

try:
    command = commands[sys.argv[1]]
    os.system(command)
except KeyError, why:
    exit('unkown command: %s' % why)
except IndexError, why:
    exit('missing argument')
except OSError, why:
    exit('could not %s server: %s' % (sys.argv[1], why)) 
 
