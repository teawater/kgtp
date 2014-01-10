#!/usr/bin/python

# Lib for web interface example
# GPL
# Copyright(C) Hui Zhu (teawater@gmail.com), 2014

import sys, inspect, os
sys.path.append(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
import kgtpweb

class hotcode(kgtpweb.web)
	def __init__(self, server_address = ('localhost', 8000))
		kgtpweb.web.__init__(server_address)
		self.page_list["/add_pid"] = self.web_add_pid

	def 

	def web_kgtp_monitor(self, one_handler):
		self.web_head(one_handler)
		self.web_tail(one_handler)