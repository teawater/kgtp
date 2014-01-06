#!/usr/bin/python

# Lib for web interface example
# GPL
# Copyright(C) Hui Zhu (teawater@gmail.com), 2014

import sys, inspect, os
sys.path.append(os.path.abspath(os.path.dirname(inspect.getfile(inspect.currentframe()))))
import kgtpweb

class b(kgtpweb.handler):
	def a(self):
		pass

a = ()
b = kgtpweb.web(RequestHandlerClass = b)
#b = kgtpweb.kgtpweb.handler.handler()
