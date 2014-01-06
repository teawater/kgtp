#!/usr/bin/python

# Lib for web interface
# GPL
# Copyright(C) Hui Zhu (teawater@gmail.com), 2014

from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import urlparse
import cPickle

class handler(BaseHTTPRequestHandler):
	def do_GET(self):
		server.do_GET(self)

class web(HTTPServer):
	orig_config = {
			'gdb' :		'',
			'vmlinux' :	'',
		      }
	config = orig_config

	def __init__(self,
		     server_address = ('localhost', 8000),
		     RequestHandlerClass = handler,
		     config_file = "./config.ini"):
		HTTPServer.__init__(self, server_address,
				    RequestHandlerClass)
		try:
			self.config = cPickle.load(file(config_file))
		except:
			self.config = self.orig_config
		self.replenish_config()
		f = file(config_file, 'w')
		cPickle.dump(self.config, f)
		f.close()

	def replenish_config(self):
		for name in self.orig_config:
			if name not in self.config:
				self.config[name] = self.orig_config[name]

	def do_setup(self, one_handler):
		one_handler.send_response(200)
		one_handler.send_header("Content-type", "text/html")
		one_handler.end_headers()
		query = urlparse.parse_qs(one_handler.parsed_path.query)
		if len(query) > 0:
			pass
		else:
			one_handler.wfile.write('''<html><head>
				<title>KGTP setup</title>
				</head>
				<body>
				<form method="get" action="/">''')
			
			one_handler.wfile.write('''</form></body></html>''')
			#one_handler.wfile.write("<form method=\"get\" action=\"/setup\" name=\"test\"><input name=\"a\" value=\"test\"><input name=\"b\" value=\"test\"><button></button></form>")

	page_list = {
			"/" : 	do_setup,
		    }

	def do_GET(self, one_handler):
		one_handler.parsed_path = urlparse.urlparse(one_handler.path)
		if one_handler.parsed_path.path not in self.page_list:
			one_handler.send_response(404)
			one_handler.send_header("Content-type", "text/plain")
			one_handler.end_headers()
			one_handler.wfile.write("No such page")
		else:
			self.page_list[one_handler.parsed_path.path](self, one_handler)

if __name__ == "__main__":
	server = web()
	server.serve_forever()
	#server.handle_request()
