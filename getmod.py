#!/usr/bin/python

# This script is used by GDB to load the symbols from Linux kernel modules
# Copyright(C) KGTP team (https://kgtp.googlecode.com), 2011-2013
# Licensed under the GNU General Public License, version 2.0 (GPLv2)

#Set special mod_search_dir
#set $mod_search_dir="dir"
#Clear special mod_search_dir
#set $mod_search_dir=(void)1
#Not ignore gtp.ko
#set $ignore_gtp_ko=0

import gdb
import os

def get_pagination():
	buf = gdb.execute("show pagination", False, True)
	begin = buf.find("State of pagination is ") + len("State of pagination is ")
	if begin < 0:
		raise NotImplementedError("Cannot get pagination")
	buf = buf[begin:]
	end = buf.rfind(".")
	buf = buf[:end]

	return buf

pagination = get_pagination()
gdb.execute("set pagination off", False, False)

def format_file(name):
	tmp = ""
	for c in name:
		if c == "_":
			c = "-"
		tmp += c
	return tmp

def get_mod_dir_name(name, search_dir):
	#get mod_dir_name
	full_name = ""
	for root, dirs, files in os.walk(search_dir):
		for afile in files:
			tmp_file = format_file(afile)
			if tmp_file == name:
				full_name = os.path.join(root,afile)
				break
		if full_name != "":
			break
	return full_name

#Check if the target is available
if str(gdb.selected_thread()) == "None":
	raise gdb.error("Please connect to Linux Kernel before use the script.")

#Output the help
print "Use GDB command \"set $mod_search_dir=dir\" to set an directory for search the modules."

ignore_gtp_ko = gdb.parse_and_eval("$ignore_gtp_ko")
if ignore_gtp_ko.type.code == gdb.TYPE_CODE_INT:
	ignore_gtp_ko = int(ignore_gtp_ko)
else:
	ignore_gtp_ko = 1

#Get the mod_search_dir
mod_search_dir_list = []
#Get dir from $mod_search_dir
tmp_dir = gdb.parse_and_eval("$mod_search_dir")
if tmp_dir.type.code == gdb.TYPE_CODE_ARRAY:
	tmp_dir = str(tmp_dir)
	tmp_dir = tmp_dir[1:len(tmp_dir)]
	tmp_dir = tmp_dir[0:tmp_dir.index("\"")]
	mod_search_dir_list.append(tmp_dir)
#Get dir that same with current vmlinux
tmp_dir = str(gdb.execute("info files", False, True))
tmp_dir = tmp_dir[tmp_dir.index("Symbols from \"")+len("Symbols from \""):len(tmp_dir)]
tmp_dir = tmp_dir[0:tmp_dir.index("\"")]
tmp_dir = tmp_dir[0:tmp_dir.rindex("/")]
mod_search_dir_list.append(tmp_dir)
#Get the dir of current Kernel
tmp_dir = "/lib/modules/" + str(os.uname()[2])
if os.path.isdir(tmp_dir):
	mod_search_dir_list.append(tmp_dir)
#Let user choice dir
mod_search_dir = ""
while mod_search_dir == "":
	for i in range(0, len(mod_search_dir_list)):
		print str(i)+". "+mod_search_dir_list[i]
	try:
		s = input('Select a directory for search the modules [0]:')
	except SyntaxError:
		s = 0
	except:
		continue
	if s < 0 or s >= len(mod_search_dir_list):
		continue
	mod_search_dir = mod_search_dir_list[s]

mod_list_offset = long(gdb.parse_and_eval("((size_t) &(((struct module *)0)->list))"))
mod_list = long(gdb.parse_and_eval("(&modules)"))
mod_list_current = mod_list

while 1:
	mod_list_current = long(gdb.parse_and_eval("((struct list_head *) "+str(mod_list_current)+")->next"))

	#check if need break the loop
	if mod_list == mod_list_current:
		break

	mod = mod_list_current - mod_list_offset

	#get mod_name
	mod_name = str(gdb.parse_and_eval("((struct module *)"+str(mod)+")->name"))
	mod_name = mod_name[mod_name.index("\"")+1:len(mod_name)]
	mod_name = mod_name[0:mod_name.index("\"")]
	mod_name += ".ko"
	mod_name = format_file(mod_name)

	mod_dir_name = get_mod_dir_name(mod_name, mod_search_dir);

	#Some Linux distrubutions may use different module name for debug binaries
	#Give another try for RHEL/CentOS here
	if mod_dir_name == "":
		mod_name_debug = mod_name + ".debug"
		mod_dir_name = get_mod_dir_name(mod_name_debug, mod_search_dir);

	command = " "

	#Add module_core to command
	tmp = str(gdb.parse_and_eval("((struct module *)"+str(mod)+")->module_core"))
	if tmp.find('<') >= 0:
		tmp = tmp[:tmp.index('<')]
	command += tmp

	#Add each sect_attrs->attrs to command
	#get nsections
	nsections = int(gdb.parse_and_eval("((struct module *)"+str(mod)+")->sect_attrs->nsections"))
	sect_attrs = long(gdb.parse_and_eval("(u64)((struct module *)"+str(mod)+")->sect_attrs"))
	for i in range(0, nsections):
		command += " -s"
		tmp = str(gdb.parse_and_eval("((struct module_sect_attrs *)"+str(sect_attrs)+")->attrs["+str(i)+"].name"))
		tmp = tmp[tmp.index("\"")+1:len(tmp)]
		tmp = tmp[0:tmp.index("\"")]
		command += " "+tmp
		tmp = str(gdb.parse_and_eval("((struct module_sect_attrs *)"+str(sect_attrs)+")->attrs["+str(i)+"].address"))
		command += " "+tmp

	if mod_dir_name == "":
		print "Cannot find out",mod_name,"from directory."
		print "Please use following command load the symbols from it:"
		print "add-symbol-file some_dir/"+mod_name+command
	else:
		if ignore_gtp_ko and mod_name == "gtp.ko":
			print "gtp.ko is ignored.  You can use command \"set $ignore_gtp_ko=0\" to close this ignore."
			print "Or you can use following command load the symbols from it:"
			print "add-symbol-file "+mod_dir_name+command
		else:
			#print "add-symbol-file "+mod_dir_name+command
			gdb.execute("add-symbol-file "+mod_dir_name+command, False, False)

gdb.execute("set pagination " + pagination, False, False)
