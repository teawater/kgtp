#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, getopt, os

kgtp_config = "/etc/kgtp"

class Config:
	pass

class Lang:
	def __init__(self, language = "en"):
		self.data = {}
		self.language = language

	def add(self, en, cn):
		self.data[en] = cn

	def string(self, s):
		if self.language == "en":
			return s
		return self.data[s]

def usage(name):
	print "Usage: " + name + " [option]"
	print "Options:"
	print "  -l, --language=LANGUAGE	Set the language (en/cn) of output."
	print "  -q, --quiet			"
	print "  -h, --help			Display this information."

def main(argv):
	#Check if we have root permission
	if os.geteuid() != 0:
		print "You need run this script as the root."
		return -1

	#Handle argv
	lang = False
	try:
		opts, args = getopt.getopt(argv[1:], "hl:", ["help", "language="])
	except getopt.GetoptError:
		usage(argv[0])
		return -1
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			usage(argv[0])
			return -1
		elif opt in ("-l", "--language"):
			lang = arg

	#Open config file
	try:
		config = cPickle.load(file(kgtp_config))
	except:
		config = Config()
		try:
			f = file(kgtp_config, 'w+')
			cPickle.dump(config, f)
			f.close()
		except:
			print "Cannot save config to \"" + kgtp_config + "\"."
			return -1

	if not lang:
		loop = True
		while loop:
			s = raw_input("Which language do you want use?(English/Chinese)")
			if s[0] == "e" or s[0] == "E":
				lang = Lang("en")
				loop = False
			elif s[0] == "c" or s[0] == "C":
				lang = Lang("cn")
				loop = False
	#After this part of code, the language is set to lang.language

	

	return 0

if __name__ == "__main__":
	 main(sys.argv)