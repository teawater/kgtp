#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, getopt, os, pickle

#This is config file name
kgtp_config = "/etc/kgtp"

#This is the lang
lang = False

class Config:
    def check(self):
        if lang in self:
            print 1

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
    print "  -l, --language=LANGUAGE          Set the language (English/Chinese) of output."
    print "  -c, --config-file=CONFIG_FILE    Set dir of config file.  The default is \"" + kgtp_config + "\"."
    print "  -r, --reconfig                   Reconfig the KGTP."
    print "  -h, --help                       Display this information."

def init(argv):
    '''Return 0 if init OK.
       Return 1 is need simple reconfig.
       Return 2 is need auto reconfig.
       Return -1 is got error.'''

    #Check if we have root permission
    if os.geteuid() != 0:
        print "You need run this script as the root."
        return -1

    #Handle argv
    lang = False
    try:
        opts, args = getopt.getopt(argv[1:], "hl:c:r", ["help", "language=", "config-file", "reconfig"])
    except getopt.GetoptError:
        usage(argv[0])
        return -1
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv[0])
            return -1
        elif opt in ("-l", "--language"):
            lang = arg
        elif opt in ("-c", "--config-file"):
            kgtp_config = arg
        elif opt in ("-r", "--reconfig"):
            return 1

    #Open config file
    try:
        config = pickle.load(file(kgtp_config))
    except:
        config = Config()
        try:
            f = file(kgtp_config, 'w+')
            pickle.dump(config, f)
            f.close()
        except:
            print "Cannot save config to \"" + kgtp_config + "\"."
            return -1
        return 1
    if config.check():
        return 1

    #Set lang
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

    #Check if KGTP need check

    #Check GDB

    #Check Linux kernel

    #Check KGTP

    #insmod

    #start GDB

    return 0

def config(auto = False):
    return 0

def run():
    return 0

if __name__ == "__main__":
    ret = init(sys.argv)
    if ret > 0:
        #KGTP need reconfig.
        auto = False
        if ret == 2:
            auto = True
        ret = config(auto)
    if ret < 0:
        exit (ret)

    run()
