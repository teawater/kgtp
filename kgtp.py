#!/usr/bin/python
# -*- coding: utf-8 -*-

'''Script to help KGTP start.'''

import sys, getopt, os, ConfigParser, re, shutil, time

#This is config file name
KGTP_DIR = os.environ.get("HOME") + "/kgtp/"

KGTP_REPOSITORY_DICT = {
        "https://github.com/teawater/kgtp.git"     :"",
        "git://gitshell.com/teawater/kgtp.git"     :"",
        "git://code.csdn.net/teawater/kgtp.git"    :"",
        "http://git.oschina.net/teawater/kgtp.git" :"",
        "git://gitcafe.com/teawater/kgtp.git"      :""}

KGTP_BRANCH_DICT = {
        "release" : "Last release version",
        "master"  : "Last stable version",
        "dev"     : "Untested and unreleased"}

KGTP_NEED_GDB_VERSION = 7.6
KGTP_INSTALL_GDB = "gdb-7.7"

KGTP_PY_DIR_NAME = ""
KGTP_PY_LAST_TIME = 0

KGTP_PY_DEVELOP_MODE = False

class Lang(object):
    '''Language class.'''
    def __init__(self, language="en"):
        self.data = {}
        self.language = language
        self.is_set = False
        self.add('Please install "%s" before go to next step.',
                 '在进行下一步以前请先安装软件包"%s"。')
        self.add('Input "y" and press "Enter" to continue',
                 '输入"y"后按回车键继续')
        self.add("Install packages failed.",
                 "安装包失败。")
        self.add('Call command "%s" failed. ',
                 '调用命令"%s"失败。 ')
        self.add("Insmod KGTP modules?",
                 "是否装载KGTP模块到系统中？")
	self.add('Insmod KGTP module "%s" failed.',
                 '装载KGTP模块"%s"到系统中失败。')
	self.add("Cannot found sys_read from /proc/kallsyms.",
                 "无法从/proc/kallsyms中找到sys_read。")
	self.add('Please report this issue to https://github.com/teawater/kgtp/issues or teawater@gmail.com.',
                 '请汇报这个问题到 https://github.com/teawater/kgtp/issues 或者 teawater@gmail.com。')
	self.add("Cannot found sys_write from /proc/kallsyms.",
                 "无法从/proc/kallsyms中找到sys_write。")
	self.add("Cannot check Linux kernel debug image with /proc/kallsyms because it is not available.",
                 "因为/proc/kallsyms不存在，所以无法通过其检查Linux内核调试镜像是否正确。")
	self.add('Linux kernel debug image "%s" is not for current Linux kernel.',
                 'Linux内核调试镜像 "%s"不适应于当前Linux内核。')
        self.add('Get following error when write config file "%s":',
                 '写配置文件"%s"时有下面的错误:')
	self.add("KGTP config begin, please make sure current machine can access internet first.",
                 "KGTP配置开始，请确保当前主机能访问互联网。")
	self.add('Press "Enter" to continue',
                 '请按回车键继续')
	self.add('Current system is "%s".',
                 '当前系统是"%s".')
	self.add("Current system is not complete support.  Need execute some commands with yourself.\nIf you want KGTP support your system, please report to https://github.com/teawater/kgtp/issues or teawater@gmail.com.",
                 "当前系统还没有被支持，需要手动执行一些命令。\n如果你希望KGTP支持你的系统，请汇报这个到 https://github.com/teawater/kgtp/issues 或者 teawater@gmail.com。")
	self.add('Please select git repository of KGTP:',
                 '请选择KGTP的GIT仓库:')
	self.add('Please select git branch of KGTP:',
                 '请选择KGTP的GIT分支:')
	self.add('Clone KGTP source failed.',
                 '克隆KGTP源码失败。')
	self.add('Update KGTP source in "%s" failed.',
                 '升级在目录"%s"的KGTP源码失败。')
	self.add("Change to another git repository?",
                 "选择其他GIT仓库？")
	self.add("kgtp.py was updated, restarting...",
                 "kgtp.py被更新，重启中...")
	self.add('Please select a GDB:',
                 '请选择一个GDB:')
	self.add('Please input the filename of GDB:',
                 '请输入GDB的文件名:')
	self.add('Please input the filename of GDB or just "Enter" to install it now:',
                 '请输入GDB的文件名或者直接回车将开始自动安装:')
	self.add('"%s" is not right.',
                 '"%s"不正确。')
	self.add("Want input another?",
                 "要输入其他的吗?")
	self.add('Version of "%s" is older than %s that KGTP need, do you want to get a new version GDB:',
                 '"%s"的版本比KGTP需要的%s老，do you want to get a new version GDB:')
	self.add('Get following error when remove directory "%s":',
                 '删除目录"%s"时发生下面的错误:')
	self.add("Check the software source...",
                 '检查软件源...')
	self.add("GDB in software source is too old for KGTP.",
                 "软件源中的GDB比KGTP需要的老。")
	self.add("Get and build a GDB (it will not install to current system) that works OK with KGTP...",
                 '取得并编译一个可以和KGTP一起工作的GDB(并不会安装到当前系统中)...')
	self.add("Download GDB source package failed.",
                 '下载GDB源码包失败。')
	self.add("Uncompress GDB source package failed.",
                 '解压缩GDB源码包失败。')
	self.add("Build GDB failed.",
                 "编译GDB失败。")
	self.add("Install Linux kernel source failed. ",
                 '安装内核源码失败。')
	self.add('Cannot find Linux kernel source in "%s".',
                 '无法在"%s"找到内核源码。')
	self.add("Install Linux kernel debug image failed. ",
                 '安装Linux内核调试镜像失败。')
	self.add("Please input the filename of Linux kernel debug image:",
                 '请输入Linux内核调试文件的文件名:')
	self.add("Build KGTP failed. ",
                 "编译KGTP failed。 ")
	self.add("How many days are prompted to update KGTP source? (0 means every time):",
                 "多少天提示一次更新KGTP源码? (0表示每次):")
	self.add("Do you want install kgtp.py to current system?",
                 '你是否要安装kgtp.py到当前系统中?')
	self.add("Please input the directory that you want to install kgtp.py:",
                 '请输入要安装kgtp.py的目录:')
	self.add('"%s" exists but it is not a directory.',
                 '"%s"存在但是其不是一个目录。')
	self.add("Install kgtp.py failed. ",
                 '安装kgtp.py失败。 ')
	self.add('Command "sudo kgtp.py" can start KGTP now.',
                 '现在命令"sudo kgtp.py"可以启动KGTP。')
	self.add('"%s" is not a directory.',
                 '"%s"不是一个目录。')
        self.add('Get following error when read config file "%s":',
                 '读配置文件"%s"时有下面的错误:')
	self.add('Config is not complete.',
                 '配置不完整。')
	self.add('Distro is changed.',
                 '发行版被更换了。')
	self.add('Cannot execute GDB in "%s" or its version is older than %s.',
                 '不能执行GDB"%s"或者其版本比%s老。')
	self.add('Current Linux kernel version is not "%s".',
                 '当前Linux内核版本不是"%s"。')
	self.add('Linux kernel source "%s" is not right.',
                 'Linux内核源码"%s"不正确。')
	self.add('Linux kernel debug image "%s" is not right.',
                 'Linux内核调试镜像"%s"不正确。')
	self.add("KGTP source has not been updated more than %d days.",
                 'KGTP源码已经超过%d天没有更新过了。')
	self.add('Update source of KGTP?',
                 '升级KGTP源码?')
	self.add('kgtp.py is different with "%s", restarting...',
                 'kgtp.py和"%s"不同, 重启中...')

    def set_language(self, language):
        if language != "":
            self.language = language
            self.is_set = True

    def add(self, en, cn):
        self.data[en] = cn

    def string(self, s):
        if self.language == "en" or (not self.data.has_key(s)):
            return s
        return self.data[s]

def retry(string="", ret=-1):
    while True:
        s = raw_input(string + lang.string(" [Retry]/Exit:"))
        if len(s) == 0 or s[0] == 'r' or s[0] == 'R':
            break
        if s[0] == "E" or s[0] == "e":
            exit(ret)

def yes_no(string="", has_default=False, default_answer=True):
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
        version = fp.readline().lower()
        fp.close()
        if re.match('.*ubuntu.*', version):
            return "Ubuntu"
        elif re.match('.*opensuse.*', version):
	    return "openSUSE"
    except:
        pass

    return "Other"

def get_cmd(cmd, first=True):
    f = os.popen(cmd)
    if first:
        v = f.readline().rstrip()
    else:
        v = f.readlines()
    f.close()
    return v

def get_gdb_version(gdb):
    try:
        v = get_cmd(gdb + " -v")
    except:
        return -1
    if not re.match(r'^GNU gdb (.+) \d+\.\d+.*$', v):
        return -1

    return float(re.search(r'\d+\.\d+', v).group())

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
    elif distro == "openSUSE":
        try:
            v = get_cmd("zypper info " + name, False)
        except:
            return 0
    else:
        return 0

    if distro == "openSUSE":
	got_name = False
	got_version = False
	for line in v:
	    if got_name and re.match('^Version: ', line):
		got_version = True
		v = line
		break
	    if re.match('^Name: '+name, line):
		got_name = True
    elif not re.match('^'+name, v):
        return 0

    return float(re.search(r'\d+\.\d+', v).group())

def install_packages(distro, packages, auto):
    #Remove the package that doesn't need install from packages
    if distro != "Other":
        tmp_packages = []
        for i in range(0, len(packages)):
            ret = 1
            if distro == "Redhat" or distro == "openSUSE":
                ret = os.system("rpm -q " + packages[i])
            elif distro == "Ubuntu":
                ret = os.system("dpkg -s " + packages[i])
            if ret != 0:
                tmp_packages.append(packages[i])
        packages = tmp_packages
    if len(packages) == 0:
        return

    packages = " ".join(packages)
    while True:
        ret = 0
        if distro == "Redhat":
            ret = os.system("yum -y install " + packages)
        elif distro == "Ubuntu":
            ret = os.system("apt-get -y --force-yes install " + packages)
        elif distro == "openSUSE":
	    ret = os.system("zypper -n install --oldpackage " + packages)
        else:
            if auto:
                return
            while True:
                print(lang.string('Please install \"%s\" before go to next step.') %packages)
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
            if k_str != "" and k_list[i][0] == k_str:
                default = i
                default_str = "[%d]" %i
        try:
            select = input(introduce + default_str)
        except SyntaxError:
            select = default
        except Exception:
            select = -1
        if select >= 0 and select < len(k_dict):
            break
    return k_list[select][0]

def call_cmd(cmd, fail_str="", chdir="", outside_retry=False):
    '''
    Return True if call cmd success.
    '''
    if fail_str == "":
        fail_str = lang.string('Call command "%s" failed. ') %cmd
    if chdir != "":
        os.chdir(chdir)
    while True:
        ret = os.system(cmd)
        if ret == 0:
            break
        retry(fail_str, ret)
        if outside_retry:
            return False

    return True

def kgtp_insmod(gdb, kernel_image):
    global KGTP_DIR

    #Insmod
    if not os.path.isdir("/sys/kernel/debug/"):
        os.system("mount -t sysfs none /sys/")
        os.system("mount -t debugfs none /sys/kernel/debug/")
    if not KGTP_PY_DEVELOP_MODE or yes_no(lang.string("Insmod KGTP modules?")):
        os.system("rmmod gtp")
        if os.system("insmod " + KGTP_DIR + "kgtp/gtp.ko"):
            print(lang.string('Insmod KGTP module "%s" failed.')
                  %(KGTP_DIR + "kgtp/gtp.ko"))
            return False

    image_wrong = False
    if os.path.isfile("/proc/kallsyms"):
        f = open("/proc/kallsyms", "r")
        got_sys_read = False
        got_sys_write = False
        while True:
            line = f.readline()
            if not line:
                break
            line = line.rstrip()
            is_sys_read = False
            is_sys_write = False
            if not got_sys_read and re.match(r'.*[^\s]\ssys_read$', line):
                is_sys_read = True
            if not got_sys_write and re.match(r'.*[^\s]\ssys_write$', line):
                is_sys_write = True
            if not is_sys_read and not is_sys_write:
                continue
            val = re.search(r'^[0-9a-fA-F]*', line).group()
            if is_sys_read:
                got_sys_read = True
                sys_read = val
            if is_sys_write:
                got_sys_write = True
                sys_write = val
            if got_sys_read and got_sys_write:
                break
        f.close()
        if got_sys_read:
            v = get_cmd(gdb + " " + kernel_image + r' -ex "printf \"%lx\\n\", sys_read" -ex "quit"', False)
            v = v[-1].rstrip()
            if v != sys_read:
                image_wrong = False
        else:
            print lang.string("Cannot found sys_read from /proc/kallsyms.")
            print lang.string('Please report this issue to https://github.com/teawater/kgtp/issues or teawater@gmail.com.')
        if got_sys_write:
            v = get_cmd(gdb + " " + kernel_image + r' -ex "printf \"%lx\\n\", sys_write" -ex "quit"', False)
            v = v[-1].rstrip()
            if v != sys_write:
                image_wrong = True
        else:
            print lang.string("Cannot found sys_write from /proc/kallsyms.")
            print lang.string('Please report this issue to https://github.com/teawater/kgtp/issues or teawater@gmail.com.')
    else:
        print lang.string("Cannot check Linux kernel debug image with /proc/kallsyms because it is not available.")

    #With linux_banner
    if not image_wrong and config.get("misc", "distro") != "openSUSE":
        v = get_cmd(gdb + " " + kernel_image + r' -ex "printf \"%s\", linux_banner" -ex "quit"', False)
        linux_banner = v[-1].rstrip()
        v = get_cmd(gdb + " " + kernel_image + r' -ex "target remote /sys/kernel/debug/gtp" -ex "printf \"%s\", linux_banner" -ex "set confirm off" -ex "quit"', False)
        if v[-3].rstrip() != linux_banner:
            image_wrong = True

    if image_wrong:
        print(lang.string('Linux kernel debug image "%s" is not for current Linux kernel.') %config.get("kernel", "image"))
        print(lang.string('Please report this issue to https://github.com/teawater/kgtp/issues or teawater@gmail.com.'))
        return False

    return True

class Config():
    def __init__(self):
        self.c = ConfigParser.ConfigParser()
        self.filename = ""

    def set(self, section, option, value="", write=True):
        self.c.set(section, option, value)
        if write:
            self.write()

    def get(self, section, option):
        return self.c.get(section, option)

    def read(self, filename):
        self.filename = filename

        err_msg = False
        try:
            self.c.read(filename)
        except Exception, x:
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
        fp = open(self.filename, "w+")
        fp.write("# This file is generated by kgtp.py\n")
        fp.write("# DO NOT EDIT THIS FILE\n")
        self.c.write(fp)
        fp.close()

    def add_miss_section(self, miss, section):
        if not self.c.has_section(section):
            self.c.add_section(section)
            miss[section] = []

    def add_miss_option(self, miss, section, option, val, first=False):
        if not self.c.has_option(section, option):
            self.set(section, option, val, False)
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
        self.add_miss_option(miss, "gdb", "dir", "", True)
        self.add_miss_option(miss, "gdb", "source", "")

        self.add_miss_section(miss, "kernel")
        self.add_miss_option(miss, "kernel", "version", "", True)
        self.add_miss_option(miss, "kernel", "source", "")
        self.add_miss_option(miss, "kernel", "image", "")

        #This option is the status of confg:
        #"" means setup is not complete.
        #"done" means setup is complete.
        self.add_miss_option(miss, "misc", "setup", "")

        return miss

    def setup(self, auto=False):
        global KGTP_DIR, KGTP_REPOSITORY_DICT, KGTP_BRANCH_DICT, KGTP_NEED_GDB_VERSION, KGTP_INSTALL_GDB, KGTP_PY_DIR_NAME, KGTP_PY_LAST_TIME, KGTP_PY_DEVELOP_MODE

        #misc language
        config_language = self.get("misc", "language")
        if ((not auto) or config_language == "") and (not lang.is_set):
            if config_language == "en":
                default_s = "en"
                question_s = "[English]/Chinese"
            elif config_language == "cn":
                default_s = "cn"
                question_s = "English/[Chinese]"
            else:
                default_s = ""
                question_s = "English/Chinese"
            while True:
                s = raw_input("Which language do you want use?(%s)" %question_s)
                if len(s) == 0:
                    s = default_s
                if len(s) == 0:
                    continue
                if s[0] == "e" or s[0] == "E":
                    lang.set_language("en")
                    break
                elif s[0] == "c" or s[0] == "C":
                    lang.set_language("cn")
                    break
        self.set("misc", "language", lang.language)

        print(lang.string("KGTP config begin, please make sure current machine can access internet first."))
        raw_input(lang.string('Press "Enter" to continue'))

        #Add a flag to mark config file as doesn't complete.
        self.set("misc", "setup")

        #misc distro
        distro = get_distro()
        self.set("misc", "distro", distro)
        if distro == "Redhat" or distro == "Ubuntu" or distro == "openSUSE":
            print(lang.string('Current system is "%s".') %distro)
        else:
            print(lang.string("Current system is not complete support.  Need execute some commands with yourself.\nIf you want KGTP support your system, please report to https://github.com/teawater/kgtp/issues or teawater@gmail.com."))

        #Get the KGTP source code
        if distro == "Redhat":
            install_packages(distro, ["git"], auto)
        else:
            install_packages(distro, ["git-core"], auto)
        get_kgtp_failed = False
        while True:
            if get_kgtp_failed \
               or not self.get("kgtp", "repository") in KGTP_REPOSITORY_DICT \
               or not self.get("kgtp", "branch") in KGTP_BRANCH_DICT \
               or not os.path.isdir(KGTP_DIR + "kgtp/.git/"):
                shutil.rmtree(KGTP_DIR + "kgtp/", True)
                while True:
                    r = select_from_dict(KGTP_REPOSITORY_DICT,
                                         self.get("kgtp", "repository"),
                                         lang.string('Please select git repository of KGTP:'))
                    self.set("kgtp", "repository", r)
                    b = select_from_dict(KGTP_BRANCH_DICT,
                                         self.get("kgtp", "branch"),
                                         lang.string('Please select git branch of KGTP:'))
                    self.set("kgtp", "branch", b)
                    if call_cmd("git clone " + r + " -b " + b,
                                lang.string('Clone KGTP source failed.'),
                                KGTP_DIR,
                                True):
                        break
            else:
                while True:
                    if call_cmd("git pull",
                                lang.string('Update KGTP source in "%s" failed.') %(KGTP_DIR + "kgtp/"),
                                KGTP_DIR + "kgtp/", True):
                        break
                    if yes_no(lang.string("Change to another git repository?"), True, False):
                        get_kgtp_failed = True
                        break
            if not get_kgtp_failed:
                break

        #Check if kgtp.py is updated.  Restart it if need.
        if not KGTP_PY_DEVELOP_MODE:
            kgtp_py_updated = False
            if KGTP_PY_DIR_NAME == os.path.realpath(KGTP_DIR + "kgtp/kgtp.py"):
                if os.path.getmtime(KGTP_PY_DIR_NAME) != KGTP_PY_LAST_TIME:
                    kgtp_py_updated = True
            else:
                if os.system("diff " + KGTP_DIR + "kgtp/kgtp.py " + KGTP_PY_DIR_NAME) != 0:
                    kgtp_py_updated = True
            if kgtp_py_updated:
                print(lang.string("kgtp.py was updated, restarting..."))
                os.execl("/usr/bin/python", "python", KGTP_DIR + "kgtp/kgtp.py")

        #GDB
        if distro == "Other":
            install_packages(distro, ["gdb"], auto)
        while True:
            #Get gdb_dir
            gdb_dir = self.get("gdb", "dir")
            if gdb_dir == "" or not os.path.isfile(gdb_dir):
                #Find GDB from PATH
                gdb_dir_dict = {}
                gdb_dir_dict[""] = "Input another GDB"
                for p in os.environ.get("PATH").split(':'):
                    if os.path.isfile(p + "/gdb"):
                        gdb_dir_dict[p + "/gdb"] = ""
                if len(gdb_dir_dict) == 1:
                    gdb_dir = ""
                else:
                    gdb_dir = select_from_dict(gdb_dir_dict, "",
                                               lang.string('Please select a GDB:'))
            if not auto:
                if gdb_dir != "":
                    s = lang.string('Please input the filename of GDB:') + "["+ gdb_dir +"]"
                else:
                    s = lang.string('Please input the filename of GDB or just "Enter" to install it now:')
                s = raw_input(s)
                if len(s) == 0:
                    s = gdb_dir
                if len(s) != 0:
                    s = os.path.realpath(s)
                    if get_gdb_version(s) < 0:
                        print(lang.string('"%s" is not right.') %s)
                        if yes_no(lang.string("Want input another?")):
                            continue
                        else:
                            s = ""
                    gdb_dir = s
            #Check version
            if gdb_dir != "":
                if get_gdb_version(gdb_dir) >= KGTP_NEED_GDB_VERSION:
                    if gdb_dir != self.get("gdb", "dir") \
                       and self.get("gdb", "source") != "":
                        #Get a new GDB from input.
                        #So the source of GDB is not need.  Remove it.
                        shutil.rmtree(self.get("gdb", "source"), True)
                        self.set("gdb", "source")
                    self.set("gdb", "dir", gdb_dir)
                    break
                else:
                    if not yes_no((('Version of "%s" is older than %s that KGTP need, do you want to get a new version GDB:') %(gdb_dir, str(KGTP_NEED_GDB_VERSION))), True, True):
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
                self.set("gdb", "source")
            #Try to install GDB from software source
            if distro != "Other":
                print(lang.string("Check the software source..."))
                version = get_source_version(distro, "gdb")
                if version >= KGTP_NEED_GDB_VERSION:
                    print lang.string("Install GDB...")
                    install_packages(distro, ["gdb"], auto)
                    self.set("gdb", "dir", "gdb")
                    continue
                else:
                    print lang.string("GDB in software source is too old for KGTP.")
            #Install GDB from source code
            print lang.string("Get and build a GDB (it will not install to current system) that works OK with KGTP...")
            if distro == "Ubuntu":
                install_packages(distro, ["gcc", "texinfo", "m4", "flex", "bison", "libncurses5-dev", "libexpat1-dev", "python-dev", "wget"], auto)
            elif distro == "openSUSE":
		install_packages(distro,
                                 ["gcc", "texinfo", "m4", "flex",
                                  "bison","ncurses-devel", "libexpat-devel",
                                  "python-devel", "wget","make"],
                                 auto)
            else:
                install_packages(distro,
                                 ["gcc", "texinfo", "m4", "flex",
                                  "bison","ncurses-devel", "expat-devel",
                                  "python-devel", "wget"],
                                 auto)
            while True:
                shutil.rmtree(KGTP_DIR + KGTP_INSTALL_GDB + ".tar.bz2", True)
                shutil.rmtree(KGTP_DIR + KGTP_INSTALL_GDB, True)
                if not call_cmd("wget http://ftp.gnu.org/gnu/gdb/" + KGTP_INSTALL_GDB + ".tar.bz2", lang.string("Download GDB source package failed."), KGTP_DIR, True):
                    continue
                if not call_cmd("tar vxjf " + KGTP_INSTALL_GDB + ".tar.bz2" + " -C ./", lang.string("Uncompress GDB source package failed."), KGTP_DIR, True):
                    continue
                shutil.rmtree(KGTP_DIR + KGTP_INSTALL_GDB + ".tar.bz2", True)
                if not call_cmd("./configure --disable-sid --disable-rda --disable-gdbtk --disable-tk --disable-itcl --disable-tcl --disable-libgui --disable-ld --disable-gas --disable-binutils --disable-gprof --with-gdb-datadir=" + KGTP_DIR + KGTP_INSTALL_GDB + "/gdb/data-directory/", lang.string("Config GDB failed."), KGTP_DIR + KGTP_INSTALL_GDB, True):
                    continue
                if not call_cmd("make all", lang.string("Build GDB failed."), KGTP_DIR + KGTP_INSTALL_GDB, True):
                    continue
                shutil.rmtree(KGTP_DIR + KGTP_INSTALL_GDB + ".tar.bz2", True)
                break
            self.set("gdb", "source", KGTP_DIR + KGTP_INSTALL_GDB)
            self.set("gdb", "dir", KGTP_DIR + KGTP_INSTALL_GDB + "/gdb/gdb")

        #Kernel
        kernel_version = get_cmd("uname -r")
        if auto \
           and kernel_version == self.set("kernel", "version"):
	    #This part of code help other distro and auto reconfig.
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
                         KGTP_DIR)
                short_version = re.search(r'^\d+\.\d+\.\d+', kernel_version).group()
                source = ""
                for f in os.listdir(KGTP_DIR):
                    if os.path.isdir(KGTP_DIR + f) \
                       and re.match('^linux.*'+ short_version + "$", f):
                        source = f
                if source == "":
                    print lang.string('Cannot find Linux kernel source in "%s".') %KGTP_DIR
                    print lang.string('Please report this issue to https://github.com/teawater/kgtp/issues or teawater@gmail.com.')
                    exit(-1)
                try:
                    os.makedirs("/build/buildd/", 0700)
                except:
                    pass
                kernel_source = "/build/buildd/" + source
                shutil.rmtree(kernel_source, True)
                shutil.move(KGTP_DIR + source, kernel_source)
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
            kernel_image = "/usr/lib/debug/boot/vmlinux-" + kernel_version
        elif distro == "Redhat" and os.system("rpm -q kernel-" + kernel_version) == 0:
            install_packages(distro, ["kernel-devel-" + kernel_version], auto)
            if os.system("rpm -q kernel-debuginfo-" + kernel_version) != 0:
		call_cmd("debuginfo-install kernel",
			 lang.string("Install Linux kernel debug image failed. "))
            kernel_source = ""
            kernel_image = "/usr/lib/debug/lib/modules/" + kernel_version + "/vmlinux"
        elif distro == "openSUSE":
	    kernel_version_list = kernel_version.split('-')
	    if len(kernel_version_list) == 3:
		kernel_version0 = kernel_version_list[2]
		kernel_version1 = kernel_version_list[0] + '-' + kernel_version_list[1] + ".1"
		if os.system("rpm -q kernel-" + kernel_version0 + "-" + kernel_version1) == 0:
		    call_cmd("zypper modifyrepo --enable repo-debug repo-debug-update")
		    install_packages(distro, ["kernel-" + kernel_version0 + "-devel-" + kernel_version1, "kernel-" + kernel_version0 + "-devel-debuginfo-" + kernel_version1, "kernel-" + kernel_version0 + "-debugsource-" + kernel_version1], auto)
		    kernel_source = ""
		    kernel_image = "/usr/lib/debug/boot/vmlinux-" + kernel_version + ".debug"
	#Is not auto or didn't get kernel_image
        if not auto or kernel_image == "":
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
                image_dir = raw_input(lang.string("Please input the filename of Linux kernel debug image:") + show_dir)
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
        if distro == "openSUSE":
            install_packages(distro, ["make", "gcc", "glibc-devel-static"], auto)
        call_cmd("make clean", lang.string("Build KGTP failed. "), KGTP_DIR + "kgtp/")
        call_cmd("make", lang.string("Build KGTP failed. "), KGTP_DIR + "kgtp/")

        #Insmod
        if not kgtp_insmod(self.get("gdb", "dir"),
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
                    days = input(lang.string("How many days are prompted to update KGTP source? (0 means every time):") + default_str)
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
                answer = yes_no(lang.string("Do you want install kgtp.py to current system?"), self.get("misc", "install_dir") != "", True)
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
            call_cmd("cp " + KGTP_DIR + "/kgtp/kgtp.py " + self.get("misc", "install_dir") + "/", lang.string("Install kgtp.py failed. "))
            call_cmd("chmod 0700 " + self.get("misc", "install_dir") + "/kgtp.py", lang.string("Install kgtp.py failed. "))
            print(lang.string('Command "sudo kgtp.py" can start KGTP now.'))

        #Update setup_time
        self.set("misc", "setup_time", str(int(time.time())))

        #Add a flag to mark setup complete.
        self.set("misc", "setup", "done")

        return 0

def usage(name):
    global KGTP_DIR

    print "Usage: " + name + " [option]"
    print "Options:"
    print "  -l, --language=LANGUAGE         Set the language (English/Chinese) of output."
    print "  -d, --dir=KGTP_DIR              Set dir of kgtp.  The default is \"" + KGTP_DIR + "\"."
    print "  -r, --reconfig                  Reconfig the KGTP."
    print "  -e, --develop-mode"
    print "  -h, --help                      Display this information."

def init(argv):
    '''Return 0 if init OK.
       Return 1 is need simple reconfig.
       Return 2 is need auto reconfig.
       Return -1 is got error.'''

    global lang, config, KGTP_DIR, KGTP_NEED_GDB_VERSION, KGTP_PY_DIR_NAME, KGTP_PY_LAST_TIME, KGTP_PY_DEVELOP_MODE

    #Check if we have root permission
    if os.geteuid() != 0:
        print "You need run this script as the root."
        return -1

    lang = Lang()

    #Handle argv
    reconfig = False
    try:
        opts, args = getopt.getopt(argv[1:], "hel:d:r", ["help", "develop-mode", "language=", "dir", "reconfig"])
    except getopt.GetoptError:
        usage(argv[0])
        return -1
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage(argv[0])
            return -1
        if opt in ("-e", "--develop-mode"):
            KGTP_PY_DEVELOP_MODE = True
        elif opt in ("-l", "--language"):
            lang.set_language(arg)
        elif opt in ("-d", "--dir"):
            KGTP_DIR = arg
        elif opt in ("-r", "--reconfig"):
            reconfig = True

    #Get KGTP_PY_DIR_NAME
    KGTP_PY_DIR_NAME = os.path.realpath(argv[0])
    KGTP_PY_LAST_TIME = os.path.getmtime(KGTP_PY_DIR_NAME)

    #Dir
    if os.path.exists(KGTP_DIR):
        if not os.path.isdir(KGTP_DIR):
            print lang.string('"%s" is not a directory.') %KGTP_DIR
            exit(-1)
    else:
        os.mkdir(KGTP_DIR)
    os.chdir(KGTP_DIR)
    KGTP_DIR = os.path.realpath(KGTP_DIR) + "/"

    #Config
    config = Config()
    try:
        config.read(KGTP_DIR + "config")
    except Exception, x:
        print lang.string('Get following error when read config file "%s":') %config.filename
        print x
        return 1

    if reconfig:
        return 1

    #Set lang
    if not lang.is_set:
        lang.set_language(config.get("misc", "language"))

    #Check if config is done
    if config.get("misc", "setup") != "done":
        print lang.string('Config is not complete.')
        return 1

    #Check if this kgtp.py in kgtp dir or same with it.
    #If not, restart and use kgtp.py in kgtp dir.
    if not KGTP_PY_DEVELOP_MODE \
       and KGTP_PY_DIR_NAME != os.path.realpath(KGTP_DIR + "kgtp/kgtp.py") \
       and os.path.isfile(KGTP_DIR + "kgtp/kgtp.py") \
       and os.system("diff " + KGTP_DIR + "kgtp/kgtp.py " + KGTP_PY_DIR_NAME) != 0:
            print(lang.string('kgtp.py is different with "%s", restarting...') %(KGTP_DIR + "kgtp/kgtp.py"))
            os.execl("/usr/bin/python", "python", KGTP_DIR + "kgtp/kgtp.py")

    #Distro
    if get_distro() != config.get("misc", "distro"):
        print lang.string('Distro is changed.')
        return 1

    #GDB
    if get_gdb_version(config.get("gdb", "dir")) < KGTP_NEED_GDB_VERSION:
        print lang.string('Cannot execute GDB in "%s" or its version is older than %s.') %config.get("gdb", "dir"), str(KGTP_NEED_GDB_VERSION)
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
        update_days = int(config.get("misc", "update_days"))
        setup_time = int(config.get("misc", "setup_time"))
    except:
        print lang.string('Config is not complete.')
        return 1
    if update_days * 24 * 3600 + setup_time < int(time.time()):
        if update_days > 0:
            print lang.string("KGTP source has not been updated more than %d days.") %update_days
        if yes_no(lang.string("Update source of KGTP?"), True, update_days > 0):
            return 2

    return 0

def run():
    global config

    ret = init(sys.argv)
    if ret > 0:
        #KGTP need setup.
        auto = False
        if ret == 2:
            auto = True
        ret = config.setup(auto)
    if ret < 0:
        exit(ret)

    gdb_dir = config.get("gdb", "dir")
    os.execl(gdb_dir, gdb_dir, config.get("kernel", "image"),
             "-ex", "target remote /sys/kernel/debug/gtp")

if __name__ == "__main__":
    run()
