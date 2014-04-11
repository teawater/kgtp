#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys, getopt, os, ConfigParser, re, shutil, time

#This is config file name
kgtp_dir = os.environ.get("HOME") + "/kgtp/"

kgtp_repository_dict = {
	"https://github.com/teawater/kgtp.git"     :"",
	"git://code.csdn.net/teawater/kgtp.git"    :"",
	"http://git.oschina.net/teawater/kgtp.git" :"",
	"git://gitshell.com/teawater/kgtp.git"     :"",
	"git://gitcafe.com/teawater/kgtp.git"      :""}

#kgtp_branch_dict = {
	#"release" : "Last release of KGTP",
	#"master"  : "Tested but does not released",
	#"dev"     : "Untested and unreleased"}
kgtp_branch_dict = {
	"script" : "Just for test"}

kgtp_need_gdb_version = 7.6
kgtp_install_gdb = "gdb-7.6"

kgtp_py_dir_name = ""
kgtp_py_last_time = 0

class Lang:
    def __init__(self, language = "en"):
	self.data = {}
	self.language = language
	self.is_set = False
	self.add('Get following error when write config file "%s":',
		 '写配置文件"%s"时有下面的错误:')
	self.add('Get following error when read config file "%s":',
		 '读配置文件"%s"时有下面的错误:')
	self.add("Begin to setup KGTP...",
		 '开始设置KGTP...')

    def set_language(self, language):
	self.language = language
	self.is_set = True

    def add(self, en, cn):
	self.data[en] = cn

    def string(self, s):
	if self.language == "en" or (not self.data.has_key(s)):
	    return s
	return self.data[s]

def retry(string = "", ret = -1):
    while True:
	s = raw_input(string + lang.string(" [Retry]/Exit:"))
	if len(s) == 0 or s[0] == 'r' or s[0] == 'R':
	    break
	if s[0] == "E" or s[0] == "e":
	    exit(ret)

def yes_no(string = "", has_default = False, default_answer = True):
    if has_default:
	if default_answer:
	    default_str = " [Yes]/No:"
	else:
	    default_str = " Yes/[No]:"
    else:
	default_str = " Yes/No:"
    while True:
	s = raw_input(string + default_str)
	if len(s) == 0:
	    if has_default:
		return default_answer
	    continue
        if s[0] == "n" or s[0] == "N":
	    return False
        if s[0] == "y" or s[0] == "Y":
	    return True

def get_distro():
    if os.path.exists("/etc/redhat-release"):
	return "Redhat"

    try:
	fp = open("/etc/issue", "r")
	version = fp.readline()[0,6].lower()
	fp.close()
	if cmp("ubuntu", version) == 0:
	    return "Ubuntu"
    finally:
	return "other"

def get_cmd(cmd, first=True):
    f = os.popen(cmd)
    if first:
        v = f.readline()
    else:
	v = f.readlines()
    f.close()
    return v

def get_gdb_version(gdb):
    try:
	v = get_cmd(gdb + " -v")
    except:
	return -1
    if not re.match('^GNU gdb (.+) \d+\.\d+\S+$', v):
	return -1

    return float(re.search('\d+\.\d+', v).group())

def get_source_version(distro, name):
    if distro == "Redhat":
	try:
	    v = get_cmd("yum list " + name, False)
	except:
	    return 0
	if len(v) <= 0:
            return 0
	v = v[-1]
    elif distro == "Ubuntu":
	try:
	    v = get_cmd("apt-get -qq changelog " + name)
	except:
	    return 0
    else:
	return 0

    if not re.match('^'+name, v):
	return 0

    return float(re.search('\d+\.\d+', v).group())

def install_packages(distro, packages, auto):
    #Remove the package that doesn't need install from packages
    if distro != "Other":
	for i in range(0, len(packages)):
	    ret = 1
	    if distro == "Redhat":
		ret = os.system("rpm -q " + packages[i])
	    elif distro == "Ubuntu":
		ret = os.system("dpkg -s " + packages[i])
	    if ret == 0:
		del packages[i]
    if len(packages) == 0:
	return

    packages = " ".join(packages)
    while True:
	ret = 0
	if distro == "Redhat":
	    ret = os.system("sudo yum -y install " + packages)
	elif distro == "Ubuntu":
	    ret = os.system("apt-get -y --force-yes install " + packages)
	else:
	    if auto:
		return
	    while True:
		print(lang.string("Please install " + packages + " before go to next step.\n"))
		s = raw_input(lang.string('Input "y" and press "Enter" to continue'))
		if len(s) > 0 and (s[0] == 'y' or s[0] == "Y"):
		    return

	if ret == 0:
	    break
	else:
	    retry(lang.string("Install packages failed."), ret)

def select_from_dict(k_dict, k_str, introduce):
    k_list = k_dict.items()
    while True:
	default = -1
	default_str = ""
	for i in range(0, len(k_list)):
	    print("[%d] %s %s" %(i, k_list[i][0], k_list[i][1]))
	    if k_list[i][0] == k_str:
		default = i
		default_str = "[%d]" %i
	try:
	    select = input(introduce + default_str)
	except SyntaxError:
	    select = default
	except Exception:
	    select = -1
	if select >= 0 or select < len(k_dict):
	    break
    return k_list[select][0]

def call_cmd(cmd, fail_str, chdir = "", outside_retry = False):
    '''
    Return True if call cmd success.
    '''
    if chdir != "":
	os.chdir(chdir)
    while True:
	ret = os.system(cmd)
	if ret == 0:
	    break
	retry(lang.string(fail_str, ret))
	if outside_retry:
	    return False

    return True

def kgtp_insmod(gdb, kernel_image):
    global kgtp_dir

    #Insmod
    if not os.path.isdir("/sys/kernel/debug/"):
	os.system("mount -t sysfs none /sys/")
	os.system("mount -t debugfs none /sys/kernel/debug/")
    os.system("rmmod gtp")
    if os.system("insmod " + kgtp_dir + "kgtp/gtp.ko"):
	print(lang.string('Insmod KGTP module "%s" failed.') %(kgtp_dir + "kgtp/gtp.ko"))
	return False

    #Check if debug image is right
    #XXX
    ##With /proc/kallsyms
    #if os.path.isfile("/proc/kallsyms"):
	#f = read("/proc/kallsyms", "r")
	#f.read
	    #print lang.string('Linux kernel debug image "%s" is not for current Linux kernel.') %self.get(self, "kernel", "image")
	    #print lang.string('Please report to https://github.com/teawater/kgtp/issues or teawater@gmail.com.')

    ##With linux_banner
    return True

class Config():
    def __init__(self):
	self.c = ConfigParser.ConfigParser()

    def set(self, section, option, value = ""):
	self.c.set(section, option, value)

    def get(self, section, option):
	return self.c.get(section, option)

    def read(self, filename):
	self.filename = filename

	err_msg = False
	try:
	    self.c.read(filename)
	except Exception,x:
	    err_msg = x

	miss = self.add_miss()

	try:
	    self.write()
	except Exception, x:
	    print(lang.string('Get following error when write config file "%s":')) %self.filename
	    print(x)
	    exit(-1)

	if not err_msg:
	    if len(miss) > 0:
		# Get err_msg according to miss.
		err_msg = ""
		for name in miss:
		    if len(miss[name]) > 0:
			err_msg += 'Section "' + name + '" miss'
			first = True
			for val in miss[name]:
			    if first:
				first = False
			    else:
				err_msg += ','
			    err_msg = ' option "' + val + "\""
			err_msg += ".\n"
		    else:
			err_msg += 'Miss section "' + name + "\".\n"

	if err_msg:
	    raise Exception(err_msg)

    def write(self):
	fp = open(self.filename,"w+")
	fp.write("# This file is generated by kgtp.py\n")
	fp.write("# DO NOT EDIT THIS FILE\n")
	self.c.write(fp)
	fp.close()

    def add_miss_section(self, miss, section):
	if not self.c.has_section(section):
	    self.c.add_section(section)
	    miss[section] = []

    def add_miss_option(self, miss, section, option, val, first = False):
	if not self.c.has_option(section, option):
	    self.set(section, option, val)
	    if first:
		if not miss.has_key(section):
		    miss[section] = [option]
	    else:
		if miss.has_key(section) and len(miss[section]) > 0:
		    miss[section].append(option)

    def add_miss(self):
	'''Check if the config file misses some sections or options.
	Add the missing sections and options and record them in dict miss.
	Return miss.'''
	miss = {}

	self.add_miss_section(miss, "misc")
	self.add_miss_option(miss, "misc", "language", "", True)
	self.add_miss_option(miss, "misc", "distro", "")
	self.add_miss_option(miss, "misc", "update_days", "")
	self.add_miss_option(miss, "misc", "setup_time", "")
	self.add_miss_option(miss, "misc", "install_dir", "/usr/sbin/")

	self.add_miss_section(miss, "kgtp")
	self.add_miss_option(miss, "kgtp", "repository", "", True)
	self.add_miss_option(miss, "kgtp", "branch", "")

	self.add_miss_section(miss, "gdb")
	self.add_miss_option(miss, "gdb", "dir", "gdb", True)

	self.add_miss_section(miss, "kernel")
	self.add_miss_option(miss, "kernel", "version", "", True)
	self.add_miss_option(miss, "kernel", "source", "")
	self.add_miss_option(miss, "kernel", "image", "")

	#This option is the status of confg:
	#"" means setup is not complete.
	#"done" means setup is complete.
	self.add_miss_option(miss, "misc", "setup", "")

	return miss

    def setup(self, auto = False):
	global kgtp_dir, kgtp_repository_dict, kgtp_branch_dict, kgtp_need_gdb_version, kgtp_install_gdb, kgtp_py_dir_name, kgtp_py_last_time

	#Add a flag to mark config file as doesn't complete.
	self.set("misc", "setup",)
	self.write()

	#misc language
	if ((not auto) or len(self.get("misc", "language")) == 0) and (not lang.is_set):
	    while True:
		s = raw_input("Which language do you want use?(English/Chinese)")
		if len(s) == 0:
		    continue
		if s[0] == "e" or s[0] == "E":
		    lang.set_langue("en")
		    break
		elif s[0] == "c" or s[0] == "C":
		    lang.set_langue("cn")
		    break
	self.set("misc", "language", lang.language)

	print(lang.string("KGTP config begin, please make sure current machine can access internet first."))
	raw_input(lang.string('Press "Enter" to continue'))

	#misc distro
	distro = get_distro()
	self.set("misc", "distro", distro)
	if distro == "Redhat" or distro == "Ubuntu":
	    print(lang.string('Current system is "%s".') %distro)
	else:
	    print(lang.string("Current system is not complete support.  Need execute some commands with yourself.\nIf you want KGTP support your system, please report to https://github.com/teawater/kgtp/issues or teawater@gmail.com."))

	#Get the KGTP source code
	if distro == "Ubuntu":
	    install_packages(distro, ["git-core"], auto)
	else:
	    install_packages(distro, ["git"], auto)
	if not auto \
	   or not self.get("kgtp", "repository") in kgtp_repository_list \
	   or not self.get("kgtp", "branch") in kgtp_branch_dict \
	   or not os.path.isdir(kgtp_dir + "kgtp/.git/"):
	    shutil.rmtree(kgtp_dir + "kgtp/", True)
	    while True:
		r = select_from_dict(kgtp_repository_dict,
				self.get("kgtp", "repository"),
				lang.string('Please select git repository of KGTP:'))
		self.set("kgtp", "repository", r)
		b = select_from_dict(kgtp_branch_dict,
				self.get("kgtp", "branch"),
				lang.string('Please select git branch of KGTP:'))
		self.set("kgtp", "branch", b)
		if call_cmd("git clone " + r + " -b " + b,
		            lang.string('Clone KGTP source failed.'),
			    kgtp_dir,
			    True):
		    break
	else:
	    call_cmd("git pull",
		     lang.string('Update KGTP source in "%s" failed.') %(kgtp_dir + "kgtp/"),
		     kgtp_dir + "kgtp/")

	#Check if kgtp.py is updated.  Restart it if need.
	kgtp_py_updated = False
	if kgtp_py_dir_name == os.path.realpath(kgtp_dir + "kgtp/kgtp.py"):
	   if os.path.getmtime(kgtp_py_dir_name) != kgtp_py_last_time:
		kgtp_py_updated = True
	else:
	    if os.system("diff " + kgtp_dir + "kgtp/kgtp.py " + kgtp_py_dir_name) != 0:
		kgtp_py_updated = True
	if kgtp_py_updated:
	    print(lang.string("kgtp.py was updated, restarting..."))
	    self.write()
	    os.execl("/usr/bin/python", "python", kgtp_dir + "kgtp/kgtp.py")

	#GDB
	if distro == "Other":
	    install_packages(distro, ["gdb"], auto)
	while True:
	    #Get gdb_dir
	    gdb_dir = self.get("gdb", "dir")
	    if gdb_dir == "":
		#Find GDB from PATH
		for p in os.environ.get("PATH").split(':'):
		    if os.path.isfile(p + "/gdb"):
			gdb_dir = p + "/gdb"
			break
	    if not auto:
		if gdb_dir != "":
		    s = lang.string('Please input the directory of GDB:') + "["+ gdb_dir +"]"
		else:
		    s = lang.string('Please input the directory of GDB or just "Enter" to get it now:')
	        s = raw_input(s)
	        if len(s) == 0:
		    s = gdb_dir
		if len(s) != 0 and get_gdb_version(s) < 0:
		    print(lang.string('"%s" is not right.') %s)
		    continue
	        gdb_dir = os.path.realpath(s)
	    #Check version
	    if gdb_dir != "":
		if get_gdb_version(gdb_dir) >= kgtp_need_gdb_version:
		    if gdb_dir != self.get("gdb", "dir") \
		       and self.get("gdb", "source") != "":
			#Get a new GDB from input.
			#So the source of GDB is not need.  Remove it.
			shutil.rmtree(self.get("gdb", "source"), True)
			self.set("gdb", "source",)
		    self.set("gdb", "dir", gdb_dir)
		else:
		    if not yes_no((lang.string('Version of "%s" is older than %s, do you want to get a new version GDB:') %gdb_dir,str(kgtp_need_gdb_version)), True, True):
			continue
	    #GDB was built from source that is too old.  Remove it.
	    if self.get("gdb", "source") != "":
		while True:
		    try:
			shutil.rmtree(self.get("gdb", "source"))
		    except Exception, x:
			print(lang.string('Get following error when remove directory "%s":') %self.get("gdb", "source"))
			print(x)
			retry()
		self.set("gdb", "source",)
	    #Try to install GDB from software source
	    if distro != "Other":
		print(lang.string("Check the software source..."))
		version = get_source_version(distro, "gdb")
		if version >= kgtp_need_gdb_version:
		    print lang.string("Install GDB...")
		    install_packages(distro, ["gdb"], auto)
		    self.set("gdb", "dir", "gdb")
		    continue
		else:
		    print lang.string("GDB in software source is too old for KGTP.")
	    #Install GDB from source code
	    print lang.string("Get and build a GDB that works OK with KGTP...")
	    if distro == "Ubuntu":
		install_packages(distro, ["gcc", "texinfo", "m4", "flex", "bison", "libncurses5-dev", "libexpat1-dev", "python-dev", "wget"], auto)
	    else:
		install_packages(distro, "gcc", "texinfo", "m4", "flex", "bison", "ncurses-devel", "expat-devel", "python-devel", "wget", auto)
	    while True:
		ret = os.system("wget http://ftp.gnu.org/gnu/gdb/" + kgtp_install_gdb + ".tar.bz2")
		if ret != 0:
		    retry("Download source of GDB failed.")
		    continue
		ret = os.system("tar vxjf " + kgtp_install_gdb + " -C ./")
		if ret != 0:
		    shutil.rmtree(kgtp_dir + kgtp_install_gdb + ".tar.bz2", True)
		    shutil.rmtree(kgtp_dir + kgtp_install_gdb, True)
		    retry("Uncompress source package failed.")
		    continue
		shutil.rmtree(kgtp_dir + kgtp_install_gdb + ".tar.bz2", True)
		os.chdir(kgtp_dir + kgtp_install_gdb)
		ret = os.system("./configure --disable-sid --disable-rda --disable-gdbtk --disable-tk --disable-itcl --disable-tcl --disable-libgui --disable-ld --disable-gas --disable-binutils --disable-gprof --with-gdb-datadir=" + kgtp_dir + kgtp_install_gdb + "gdb/data-directory/")
		if ret == 0:
		    ret = os.system("make all")
		if ret != 0:
		    shutil.rmtree(kgtp_dir + kgtp_install_gdb, True)
		    retry("Build GDB failed.")
		    continue
		break
	    self.set("gdb", "source", kgtp_dir + kgtp_install_gdb)
	    self.set("gdb", "dir", kgtp_dir + kgtp_install_gdb + "/gdb/gdb")

	#Kernel
	kernel_version = get_cmd("uname -r")
	if auto \
	   and kernel_version == self.set("kernel", "version"):
	    kernel_source = os.path.realpath(self.get("kernel", "source"))
	    if kernel_source == "" or not os.path.isdir(kernel_source):
		kernel_source = ""
	    kernel_image = os.path.realpath(self.get("kernel", "image"))
	    if kernel_image == "" or not os.path.isfile(kernel_image):
		kernel_image = ""
	else:
	    kernel_source = ""
	    kernel_image = ""
	if distro == "Ubuntu" and os.system("dpkg -s linux-image-" + kernel_version) == 0:
	    #Install kernel dev package
	    install_packages(distro, ["linux-headers-generic"], auto)
	    #source
	    if kernel_source == "":
		install_packages(distro, ["dpkg-dev", "wget"], auto)
		call_cmd("apt-get source linux-image-" + kernel_version,
			 lang.string("Install Linux kernel source failed. "),
			 kgtp_dir)
		short_version = re.search('^\d+\.\d+\.\d+', kernel_version).group()
		source = ""
		for f in os.listdir(kgtp_dir):
		    if os.path.isdir(kgtp_dir + f) \
		       and re.match('^linux.*'+ short_version + "$", f):
			source = f
		if source == "":
		    print lang.string('Cannot find Linux kernel source in "%s".') %kgtp_dir
		    print lang.string('Please report to https://github.com/teawater/kgtp/issues or teawater@gmail.com.')
		    exit(-1)
		try:
	            os.makedirs("/build/buildd/", 0700)
		except:
		    pass
		kernel_source = "/build/buildd/" + source
		shutil.rmtree(kernel_source, True)
		shutil.move(kgtp_dir + source, kernel_source)
	    #image
	    if os.system("dpkg -s linux-image-" + kernel_version + "-dbgsym") != 0:
		name = get_cmd("lsb_release -cs")
		f = open("/etc/apt/sources.list.d/ddebs.list", "w+")
		f.write("deb http://ddebs.ubuntu.com/ " + name + " main restricted universe multiverse\n")
		f.write("deb http://ddebs.ubuntu.com/ " + name + "-security main restricted universe multiverse\n")
		f.write("deb http://ddebs.ubuntu.com/ " + name + "-updates main restricted universe multiverse\n")
		f.write("deb http://ddebs.ubuntu.com/ " + name + "-proposed main restricted universe multiverse\n")
		f.close()
		os.system("apt-get update")
		install_packages(distro, ["linux-image-" + kernel_version + "-dbgsym"], auto)
	    kernel_image =  "/usr/lib/debug/boot/vmlinux-" + kernel_version
	elif distro == "Redhat" and os.system("rpm -q kernel-" + kernel_version) == 0:
	    install_packages(distro, ["kernel-devel-" + kernel_version], auto)
	    if os.system("rpm -q kernel-debuginfo-" + kernel_version) != 0:
		call_cmd("debuginfo-install kernel",
			 lang.string("Install Linux kernel debug image failed. "))
	    kernel_source = ""
	    kernel_image = "/usr/lib/debug/lib/modules/" + kernel_version + "/vmlinux"
	elif not auto or kernel_image == "":
	    kernel_source = ""
	    if distro == "Other":
		install_packages(distro, ["kernel-header", "kernel-debug-image", "kernel-source"], auto)
	    if kernel_image != "":
		default_dir = kernel_image
		show_dir = "[" + default_dir + "]"
	    elif os.path.exists("/lib/modules/" + kernel_version + "/build/vmlinux"):
		default_dir = os.path.realpath("/lib/modules/" + kernel_version + "/build/vmlinux")
		show_dir = "[" + default_dir + "]"
	    else:
		default_dir = ""
		show_dir = ""
	    while True:
		image_dir = raw_input(lang.string("Please input the directory name of kernel debug image:") + show_dir)
		if len(image_dir) == 0:
		    image_dir = default_dir
		image_dir = os.path.realpath(image_dir)
		if os.path.isfile(image_dir):
		    break
	    kernel_image = image_dir
	self.set("kernel", "version", kernel_version)
	self.set("kernel", "source", kernel_source)
	self.set("kernel", "image", kernel_image)

	#Build KGTP
	if distro == "Redhat":
	    install_packages(distro, ["glibc-static"], auto)
	call_cmd("make", lang.string("Build KGTP failed. "), kgtp_dir + "kgtp/")

	#Insmod
	if kgtp_insmod(self.get("gdb", "dir"),
		       self.get("kernel", "image")):
	    exit(-1)

	#Ask how long do a auto reconfig to update KGTP
	try:
	    update_days = int(self.get("misc", "update_days"))
	except:
	    update_days = -1
	if not auto or update_days < 0:
	    if update_days < 0:
		default_str = ""
	    else:
		default_str = "[" + str(update_days) + "]"
	    while True:
		try:
		    days = input(lang.string("Please input the number of days to update KGTP (0 means every time):") + default_str)
		except SyntaxError:
		    days = update_days
		except Exception:
		    days = -1
		if days >= 0:
		    update_days = days
		    break
	    self.set("misc", "update_days", str(update_days))

	#Install kgtp.py
	if not auto:
	    while True:
		answer = yes_no(lang.string("Do you want install kgtp.py to your system?"))
	        if not answer:
		    self.set("misc", "install_dir")
		    break
	        else:
		    if self.get("misc", "install_dir") == "":
			default_str = ""
		    else:
			default_str = "[" + self.get("misc", "install_dir") + "]"
		    answer = raw_input(lang.string("Please input the directory that you want to install kgtp.py:") + default_str)
		    if len(answer) == 0:
			answer = self.get("misc", "install_dir")
		    if os.path.exists(answer) and not os.path.isdir(answer):
			print lang.string('"%s" exists but it is not a directory.') %answer
			continue
		    if len(answer) != 0:
			self.set("misc", "install_dir", os.path.realpath(answer) + "/")
			break
	if self.get("misc", "install_dir") != "":
	    try:
		os.makedirs(self.get("misc", "install_dir"), 0700)
	    except:
		pass
	    call_cmd("cp " + kgtp_dir + "/kgtp/kgtp.py " + self.get("misc", "install_dir") + "/")

	#Update setup_time
	self.set("misc", "setup_time", str(int(time.time())))

	#Add a flag to mark setup complete.
	self.set("misc", "setup", "done")
	self.write()

def usage(name):
    global kgtp_dir

    print "Usage: " + name + " [option]"
    print "Options:"
    print "  -l, --language=LANGUAGE	  Set the language (English/Chinese) of output."
    print "  -d, --dir=KGTP_DIR    	  Set dir of kgtp.  The default is \"" + kgtp_dir + "\"."
    print "  -r, --reconfig		  Reconfig the KGTP."
    print "  -h, --help		          Display this information."

def init(argv):
    '''Return 0 if init OK.
       Return 1 is need simple reconfig.
       Return 2 is need auto reconfig.
       Return -1 is got error.'''

    global lang, config, kgtp_dir, kgtp_need_gdb_version, kgtp_py_dir_name, kgtp_py_last_time

    #Check if we have root permission
    if os.geteuid() != 0:
	print "You need run this script as the root."
	return -1

    lang = Lang()

    #Handle argv
    try:
	opts, args = getopt.getopt(argv[1:], "hl:d:r", ["help", "language=", "dir", "reconfig"])
    except getopt.GetoptError:
	usage(argv[0])
	return -1
    for opt, arg in opts:
	if opt in ("-h", "--help"):
	    usage(argv[0])
	    return -1
	elif opt in ("-l", "--language"):
	    lang.set_langue(arg)
	elif opt in ("-d", "--dir"):
	    kgtp_dir = arg
	elif opt in ("-r", "--reconfig"):
	    return 1

    #Get kgtp_py_dir_name
    kgtp_py_dir_name = os.path.realpath(argv[0])
    kgtp_py_last_time = os.path.getmtime(kgtp_py_dir_name)

    #Dir
    if os.path.exists(kgtp_dir):
	if not os.path.isdir(kgtp_dir):
	    print lang.string('"%s" is not a directory.') %kgtp_dir
	    exit(-1)
    else:
	os.mkdir(kgtp_dir)
    os.chdir(kgtp_dir)
    kgtp_dir = os.path.realpath(kgtp_dir) + "/"

    #Config
    config = Config()
    try:
	config.read(kgtp_dir + "config")
    except Exception,x:
	print lang.string('Get following error when read config file "%s":') %config.filename
	print x
	return 1

    #Set lang
    if not lang.is_set:
        lang.set_language(config.get("misc", "language"))

    #Check if config is done
    if config.get("misc", "setup") != "done":
	print lang.string('Config is not complete.')
	return 1

    #Distro
    if get_distro() != config.get("misc", "distro"):
	print lang.string('Distro is changed.')
	return 1

    #GDB
    if get_gdb_version(config.get("gdb", "dir")) < kgtp_need_gdb_version:
	print lang.string('Cannot execute GDB in "%s" or its version is older than %s.') %self.get("gdb", "dir"), str(kgtp_need_gdb_version)
	return 1

    #Kernel
    if get_cmd("uname -r") != config.get("kernel", "version"):
	print lang.string('Current Linux kernel version is not "%s".') %config.get("kernel", "version")
	return 1
    if config.get("kernel", "source") != "" \
       and not os.path.isdir(config.get("kernel", "source")):
        print lang.string('Linux kernel source "%s" is not right.') %config.get("kernel", "source")
        return 1
    if config.get("kernel", "image") != "" \
       and not os.path.isfile(config.get("kernel", "image")):
        print lang.string('Linux kernel debug image "%s" is not right.') %config.get("kernel", "image")
        return 1

    #Insmod kgtp
    if not kgtp_insmod(config.get("gdb", "dir"), config.get("kernel", "image")):
	return 1

    #Check if need auto check
    try:
	update_days = int(self.get("misc", "update_days"))
	setup_time = int(self.get("misc", "setup_time"))
    except:
	print lang.string('Config is not complete.')
	return 1
    if update_days * 24 * 3600 + setup_time < int(time.time()):
	if update_days > 0:
	    print lang.string("KGTP source has not been updated more than %d days.") %update_days
	if yes_no("Update source of KGTP?", True, update_days > 0):
	    return 2

    return 0

def run():
    gdb_dir = config.get("gdb", "dir")
    os.execl(gdb_dir, gdb_dir, config.get("kernel", "image"))

if __name__ == "__main__":
    ret = init(sys.argv)
    if ret > 0:
	#KGTP need setup.
	auto = False
	if ret == 2:
	    auto = True
	ret = config.setup(auto)
    if ret < 0:
	exit(ret)

    run()
