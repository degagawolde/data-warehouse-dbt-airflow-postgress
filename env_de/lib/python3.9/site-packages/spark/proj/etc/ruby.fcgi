#!/usr/bin/env ruby

require "fcgi"

$SPARK_ROOT = File.expand_path(File.dirname(__FILE__)+'/..')
$:.unshift(File.expand_path($SPARK_ROOT+'/lib'))

require "ReqFCGI"

FCGI.each_cgi {|cgi|
    ReqFCGI.new(cgi).run
}
