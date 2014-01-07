#!/usr/bin/python

# Lib for web interface
# GPL
# Copyright(C) Hui Zhu (teawater@gmail.com), 2014

from BaseHTTPServer import BaseHTTPRequestHandler
from BaseHTTPServer import HTTPServer
import urlparse
import cPickle
import os
import re
import inspect
import time

class config:
	def __init__(self, value = "", web_set = True,
		     web_introduce = ""):
		self.value = value
		self.web_set = web_set
		self.web_introduce = web_introduce

class handler(BaseHTTPRequestHandler):
	def do_GET(self):
		server.do_GET(self)

class web(HTTPServer):
	orig_config = {
			'GDB' 	  :	config('gdb'),
			'vmlinux' :	config("", True, '''<a
href="https://code.google.com/p/kgtp/wiki/HOWTO#Where_is_the_current_Linux_kernel_debug_image"
target="_blank">introduce</a>'''),
		      }

	config = orig_config
	running = True
	last_cmd = False
	last_cmd_args = False

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
		self.in_gdb = True
		try:
			import gdb
		except:
			self.in_gdb = False

	def replenish_config(self):
		for name in self.orig_config:
			if name not in self.config:
				self.config[name] = self.orig_config[name]

	def save_config(self):
		f = file(self.config_file, 'w')
		cPickle.dump(self.config, f)
		f.close()

	def web_head(self, one_handler):
		one_handler.send_response(200)
		one_handler.send_header("Content-type", "text/html")
		one_handler.end_headers()
		one_handler.wfile.write('''<html><head>
				<title>KGTP</title>
				</head>
				<body>
		<div style="text-align: center;">''')
		for name in self.page_list:
			one_handler.wfile.write('<a href="'+name+'">'+name+'</a> ')
		one_handler.wfile.write("</div>")

	def web_tail(self, one_handler):
		one_handler.wfile.write("</body></html>")

	def web_msg(self, one_handler, msg, show_return = True, other_html = ""):
		self.web_head(one_handler)
		one_handler.wfile.write('<div style="text-align: center;">')
		one_handler.wfile.write(msg)
		if show_return:
			one_handler.wfile.write('''<br><a href="javascript:" onClick="javascript :window.history.back(-1);">return</a>''')
		one_handler.wfile.write(other_html)
		one_handler.wfile.write("</div>")
		self.web_tail(one_handler)

	def web_config(self, one_handler, config):
		query = urlparse.parse_qs(one_handler.parsed_path.query,
					  keep_blank_values=True)

		if len(query) > 0:
			#Check if all config got return
			for name in config:
				if config[name].web_set and (name not in query):
					self.web_msg(one_handler,
							name+" is not send")
					query = {}
		else:
			self.web_head(one_handler)
			one_handler.wfile.write('''
				<form method="get" action="/">
				<table style="margin-left: auto; margin-right: auto;" border="1" cellpadding="2" cellspacing="0"><tbody>
				''')
			for name in config:
				if not config[name].web_set:
					continue
				one_handler.wfile.write("<tr><td>"+name)
				if len(config[name].web_introduce) > 0:
					one_handler.wfile.write("("+config[name].web_introduce+")")
				one_handler.wfile.write("</td>")
				one_handler.wfile.write("<td><input name=\""+name+"\" value=\""+config[name].value+"\"></td>")
				one_handler.wfile.write("</tr>\n")
			one_handler.wfile.write('''<tr>
			<td style="text-align: center;" colspan="2">
			<button>OK</button>
			<button type="reset">RESET</button>
			</td></tr></tbody></table></form>''')
			self.web_tail(one_handler)
		return query

	def query_to_config(self, config, query):
		for name in config:
			if config[name].web_set:
				config[name].value = query[name][0]

	def check_gdb(self, gdb, version = 7.6):
		if len(gdb) == 0 or gdb.find(" ") >= 0:
			return "Format of GDB is not right."
		try:
			f = os.popen(gdb + " -v")
			v = f.readline()
			f.close()
		except:
			return "Cannot exec GDB."
		if not re.match('^GNU gdb (.+) \d+\.\d+\S+$', v):
			return "Cannot get version of GDB."
		v = float(re.search('\d+\.\d+', v).group())
		if v < version:
			return '''This GDB is too old.  Please goto <a href="https://gdbt.googlecode.com" target="_blank">this link</a> get a new version.'''
		return ""

	def web_kgtp_config(self, one_handler):
		query = self.web_config(one_handler, self.config)
		if len(query) <= 0:
			return
		#Check GDB.
		ret = self.check_gdb(query["GDB"][0])
		if ret != "":
			self.web_msg(one_handler, ret)
			return
		#Check vmlinux.
		if (query["vmlinux"][0] != "") and (not os.path.exists(query["vmlinux"][0])):
			self.web_msg(one_handler, "Vmlinux is not exist.")
			return
		#Save to config
		self.query_to_config(self.config, query)
		self.save_config()
		#Set last_cmd
		self.last_cmd = self.config["GDB"].value
		self.last_cmd_args = []
		self.last_cmd_args.append(self.config["vmlinux"].value)
		self.last_cmd_args.append("-ex")
		self.last_cmd_args.append("source "+os.path.abspath(inspect.getfile(inspect.currentframe())))

		self.web_msg(one_handler, "Set success.", False, 'Please goto <a href="/monitor">/monitor</a>')
		self.running = False

	def web_kgtp_monitor(self, one_handler):
		self.web_head(one_handler)
		self.web_tail(one_handler)

	def web_kgtp_quit(self, one_handler):
		self.web_msg(one_handler, "Quited.", False)
		self.running = False

	page_list = {
			"/config"  : 	web_kgtp_config,
			"/monitor" :	web_kgtp_monitor,
			"/quit"    :	web_kgtp_quit,
		    }

	def do_GET(self, one_handler):
		one_handler.parsed_path = urlparse.urlparse(one_handler.path)
		if one_handler.parsed_path.path == "/":
			if self.in_gdb:
				self.web_kgtp_monitor(one_handler)
			else:
				self.web_kgtp_config(one_handler)
		elif one_handler.parsed_path.path not in self.page_list:
			one_handler.send_response(404)
			one_handler.send_header("Content-type", "text/plain")
			one_handler.end_headers()
			one_handler.wfile.write("No such page")
		else:
			self.page_list[one_handler.parsed_path.path](self, one_handler)
	def server_has_stop(self):
		while self.running:
			server.handle_request()

if __name__ == "__main__":
	server = web()
	server.server_has_stop()
	last_cmd = server.last_cmd
	last_cmd_args = server.last_cmd_args
	del(server)
	if last_cmd:
		os.execvp(last_cmd, last_cmd_args)
	exit(0)