require "singleton"
$SPARK_ROOT = File.expand_path(File.join(File.dirname(__FILE__), '..'))
$:.unshift(File.expand_path($SPARK_ROOT+'/lib'))
require "ReqModRuby"

module Spark
  class Dispatcher
    include Singleton
    def handler(r)
      ReqModRuby.new(r).run
    end
  end
end

#the following are for offline debug
#just type "ruby modruby.rb"
if __FILE__ == $PROGRAM_NAME
	module Apache
		OK = 0
	end

	class Fakereq
		attr_writer :content_type
		attr_reader :subprocess_env, :paramtable, :path_info
		def initialize(path)
			@subprocess_env ={'PATH_INFO' => path.join('/')}
		end
		def send_http_header
		end
		def setup_cgi_env
		end
		def add_cgi_vars
		end
		def add_common_vars
		end
	end

	Spark::Dispatcher.instance.handler(Fakereq.new(ARGV))
end

