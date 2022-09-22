from twisted.application import internet, service
from twisted.web import static, server, vhost, resource, util
from twisted.internet import reactor

import sys, os.path
p = os.path
spark_proj = p.realpath(p.join(p.dirname(p.realpath(__file__)),'..'))

sys.path.insert(0,spark_proj)
from spark.ReqTwisted import ReqTwisted


class SparkRoot(resource.Resource):
	isLeaf = True
    
	def render(self, request):
		ReqTwisted(request, reactor).run()
		return server.NOT_DONE_YET

root = vhost.NameVirtualHost()
root.default=SparkRoot()
root.putChild('public',static.File(p.join(spark_proj,'public')))
application = service.Application('web')
sc = service.IServiceCollection(application)
site = server.Site(root)
i = internet.TCPServer(8080, site)
i.setServiceParent(sc)

