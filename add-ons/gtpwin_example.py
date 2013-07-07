#!/usr/bin/python

import sys
#To use inside GDB, need set the dir of gtpwin.py to this part.
sys.path.append('/home/teawater/kernel/svn/trunk/add-ons')

import gtpwin

nnn = 100

class example(gtpwin.gtpline):
	def load_new_val(self):
		global nnn
		nnn += 20
		self.add(nnn)
		return nnn

l = [example("a"), example("b")]
l.append(example("wwwwwwww"))
l.append(example("wwwwwwww11"))
l.append(example("wwwwwwww"))
l.append(example("wwwwwwww"))
l.append(example("wwwwwwww"))
l.append(example("wwwwwwww"))
l.append(example("wwwwwwww"))
win = gtpwin.gtpwin(l, "test")
gtpwin.run()
del(win)
