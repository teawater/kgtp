#!/usr/bin/python

# Lib for web interface
# GPL
# Copyright(C) Hui Zhu (teawater@gmail.com), 2014

from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import urlparse
import cPickle
import os

class handler(BaseHTTPRequestHandler):
	def do_GET(self):
		server.do_GET(self)

class web(HTTPServer):
	orig_config = {
			'GDB' :		("", 'gdb'),
			'vmlinux' :	('''<a
href="https://code.google.com/p/kgtp/wiki/HOWTO#Where_is_the_current_Linux_kernel_debug_image"
target="_blank">introduce</a>''', ''),
		      }
	config = orig_config

	def __init__(self,
		     server_address = ('localhost', 8000),
		     RequestHandlerClass = handler,
		     config_file = "./config.ini"):
		HTTPServer.__init__(self, server_address,
				    RequestHandlerClass)
		self.config_file = config_file
		try:
			self.config = cPickle.load(file(self.config_file))
		except:
			self.config = self.orig_config
		self.replenish_config()
		self.save_config()

	def replenish_config(self):
		for name in self.orig_config:
			if name not in self.config:
				self.config[name] = self.orig_config[name]

	def save_config(self):
		return
		f = file(self.config_file, 'w')
		cPickle.dump(self.config, f)
		f.close()

	def output_msg(self, one_handler, msg):
		one_handler.send_response(200)
		one_handler.send_header("Content-type", "text/html")
		one_handler.end_headers()
		one_handler.wfile.write('''<html><head>
				<title>KGTP</title>
				</head>
				<body>
		<div style="text-align: center;">''')
		one_handler.wfile.write(msg)
		one_handler.wfile.write('''<br><a href="javascript:" onClick="javascript :window.history.back(-1);">return</a>
				</div></body></html>''')

	def check_gdb(self, gdb):
		if len(gdb) == 0 or gdb.find(" ") >= 0:
			return "Format of GDB is not right."
		f = os.popen(gdb + " -v")
		return f.read()
		f.close()
		return ""
	def do_setup_set(self, one_handler, query):
		ret = self.check_gdb(query["GDB"])
		if ret != "":
			self.output_msg(one_handler, ret)
	
	def do_setup(self, one_handler):
		query = urlparse.parse_qs(one_handler.parsed_path.query,
					  keep_blank_values=True)

		if len(query) > 0:
			#Check if all config got return
			for name in self.config:
				if name not in query:
					self.output_msg(one_handler,
							name+" is not send")
					return
			self.do_setup_set(one_handler, query)
		else:
			one_handler.send_response(200)
			one_handler.send_header("Content-type", "text/html")
			one_handler.end_headers()
			one_handler.wfile.write('''<html><head>
				<title>KGTP setup</title>
				</head>
				<body>
				<form method="get" action="/">
				<table style="margin-left: auto; margin-right: auto;" border="1" cellpadding="2" cellspacing="0"><tbody>
				''')
			for name in self.config:
				one_handler.wfile.write("<tr><td>"+name)
				if len(self.config[name][0]) > 0:
					one_handler.wfile.write("("+self.config[name][0]+")")
				one_handler.wfile.write("</td>")
				one_handler.wfile.write("<td><input name=\""+name+"\" value=\""+self.config[name][1]+"\"></td>")
				one_handler.wfile.write("</tr>\n")
			one_handler.wfile.write('''<tr>
			<td style="text-align: center;" colspan="2">
			<button>OK</button>
			<button type="reset">RESET</button>
			</td></tr></tbody></table></form></body></html>''')

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
