#!/usr/bin/python

# This script is used to show the performance counters in graph mode
# GPL
# Copyright(C) Hui Zhu (teawater@gmail.com), 2011


pe_list = []
#0 type, 1 config, 2 name
#typt and config can get from https://code.google.com/p/kgtp/wiki/HOWTO#How_to_use_performance_counters
pe_list.append(["0","0", "CPU_CYCLES"])
pe_list.append(["0","1", "INSTRUCTIONS"])
pe_list.append(["0","2", "CACHE_REFERENCES"])
pe_list.append(["0","3", "CACHE_MISSES"])
pe_list.append(["0","4", "BRANCH_INSTRUCTIONS"])
pe_list.append(["0","5", "BRANCH_MISSES"])
pe_list.append(["0","6", "BUS_CYCLES"])
#pe_list.append(["3","0", "L1D_READ_ACCESS"])
#pe_list.append(["3","1", "L1I_READ_ACCESS"])

#sleep time
sleep_sec = 1

#0 text 1 gtk
gui_type = 1

in_gdb = False


pe_list_type = 0
pe_list_config = 1
pe_list_name = 2
pe_list_prev = 3
pe_list_qtv = 4

if in_gdb:
	import gdb
else:
	import os


class kgtp:
	fd = -1
	retry_count = 3
	buf_max = 1024
	tvariable = {}
	tvariable_next_number = 0

	def __init__(self):
		#Open fd
		try:
			self.fd = os.open("/sys/kernel/debug/gtp", os.O_RDWR)
		except:
			print "Please do not forget insmod and sudo."
			exit(0)

	def __del__(self):
		if self.fd >= 0:
			os.close(self.fd)

	def read_fd(self):
		try:
			buf = os.read(self.fd, self.buf_max)
		except:
			return False
		return buf

	def write_fd(self, msg):
		try:
			buf = os.write(self.fd, msg)
		except:
			return False
		return True

	def read(self):
		for i in range(0, self.retry_count):
			if i != 0:
				self.write_fd("-")

			buf = self.read_fd()
			if buf == False:
				continue
			buf_len = len(buf)
			if buf_len < 4:
				continue

			csum = 0
			for i in range(0, buf_len - 2):
				if i == 0:
					if buf[i] != "$":
						retry = True
						break
				elif buf[i] == '#':
					break
				else:
					csum += ord(buf[i])
			if i == 0 or buf[i] != "#":
				continue
			if int("0x"+buf[i+1:i+3], 16) != (csum & 0xff):
				continue
			buf = buf[1:i]
			self.write_fd("+")

			#print "KGTP read: "+buf
			return buf

		print "KGTP read got error"
		return False

	def write(self, msg):
		for i in range(0, self.retry_count):
			if i != 0:
				self.write_fd("-")

			csum = 0
			for c in msg:
				csum += ord(c)
			msg = "$"+msg+"#"+"%02x" % (csum & 0xff)

			if self.write_fd(msg) == False:
				continue
			if self.read_fd() != "+":
				continue

			#print "KGTP write: "+msg
			return True

		print "KGTP write got error"
		return False

	def simple_cmd(self, cmd):
		if gtp.write(cmd) == False:
			return False
		if gtp.read() != "OK":
			return False
		return True

	def tvariable_init(self):
		tvariable = {}
		tvariable_next_number = 0

		if gtp.write("qTfV") == False:
			return False
		ret = gtp.read()
		while 1:
			if ret == False:
				return False
			if ret == "l":
				return True
			ret = ret.split(":")
			if len(ret) < 4:
				print "KGTP GDBRSP package format error"
				return False
			if len(ret[3]) % 2 != 0:
				print "KGTP GDBRSP package format error"
				return False

			#Get name
			letter = ""
			name = ""
			for c in ret[3]:
				letter += c
				if len(letter) == 2:
					name += chr(int("0x"+letter, 16))
					letter = ""

			number = int("0x"+ret[0], 16)
			self.tvariable[name] = number
			if (number >= self.tvariable_next_number):
				self.tvariable_next_number = number + 1

			if gtp.write("qTsV") == False:
				return False
			ret = gtp.read()

	def tvariable_val(self, number):
		return self.tvariable_val_raw("qTV:"+"%x" % number)

	def tvariable_val_raw(self, buf):
		if gtp.write(buf) == False:
			return
		ret = gtp.read()
		if ret == False:
			return
		if ret[0] != "V":
			return

		return long("0x"+ret[1:], 16)

	def tvariable_add(self, name, val):
		if self.tvariable_next_number == 0:
			print "Must call tvariable_init before add tvariable"
			return

		buf = "QTDV:" + "%x" % self.tvariable_next_number + ":" + "%x" % val + ":0:"
		for c in name:
			buf += "%02x" % ord(c)
		if gtp.write(buf) == False:
			return
		if gtp.read() != "OK":
			print "Get something wrong when add tvariable to KGTP"
			return

		self.tvariable_next_number += 1
		return (self.tvariable_next_number - 1)

	def qtinit(self):
		return self.simple_cmd("QTinit")

	def tstart(self):
		return self.simple_cmd("QTStart")

	def tstop(self):
		return self.simple_cmd("QTStop")


def each_entry(callback):
	global pe_list, cpu_number
	for i in range(0, cpu_number):
		for e in pe_list:
			callback(i, e)


def init_pe(i, e):
	if (len(e) < pe_list_prev + 1):
		e.append([])
	e[pe_list_prev].append(0)
	if (len(e) < pe_list_qtv + 1):
		e.append([])

	if in_gdb:
		gdb.execute("tvariable $p_pe_type_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i)+"="+e[pe_list_type], True, False)
		gdb.execute("tvariable $p_pe_config_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i)+"="+e[pe_list_config], True, False)
		gdb.execute("tvariable $p_pe_val_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i)+"=0", True, False)
		gdb.execute("tvariable $p_pe_en_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i)+"=1", True, False)
	else:
		if gtp.tvariable_add("p_pe_type_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i), int(e[pe_list_type])) == None:
			exit(0)
		if gtp.tvariable_add("p_pe_config_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i), int(e[pe_list_config])) == None:
			exit(0)
		number = gtp.tvariable_add("p_pe_val_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i), 0)
		if number == None:
			exit(0)
		if gtp.tvariable_add("p_pe_en_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i), 1) == None:
			exit(0)
		e[pe_list_qtv].append("qTV:"+"%x" % number)

def init_kgtp():
	global cpu_number

	if in_gdb:
		cpu_number = int(gdb.parse_and_eval("$cpu_number"))
		#Set the empty tracepoint
		gdb.execute("delete tracepoints", False, False)
		gdb.execute("trace *0", True, False)
	else:
		cpu_number = gtp.tvariable_val(gtp.tvariable["cpu_number"])
		if cpu_number == None:
			exit(0)

	#Set the pe
	each_entry(init_pe)

import signal
def sigint_handler(num, e):
	if in_gdb:
		gdb.execute("tstop", True, False)
	else:
		gtp.tstop()
	exit(0)


if in_gdb:
	#close pagination
	gdb.execute("set pagination off", True, False);
	#Connect to KGTP if need
	if str(gdb.selected_thread()) == "None":
		gdb.execute("target remote /sys/kernel/debug/gtp", True, False)
else:
	gtp = kgtp()
	if gtp.qtinit == False:
		exit(0)
	if gtp.tvariable_init() == False:
		exit(0)

#Init the status to KGTP
cpu_number = 0
init_kgtp()
signal.signal(signal.SIGINT, sigint_handler)


#start
if in_gdb:
	gdb.execute("tstart", True, False)
else:
	gtp.tstart()


#text gui ---------------------------------------------------------------------
#pe_list will be set to:type, config, name, prev_value_list
if gui_type == 0:
	import time
	def output_pe(i, e):
		if in_gdb:
			current_value = long(gdb.parse_and_eval("$p_pe_val_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i)))
		else:
			current_value = gtp.tvariable_val_raw(e[pe_list_qtv][i])
			if current_value == None:
				print "Fail when get val from KGTP"
				exit(0)
		print "cpu"+str(i),e[pe_list_name],current_value-e[pe_list_prev][i]
		e[pe_list_prev][i] = current_value

	while 1:
		each_entry(output_pe)
		print
		time.sleep(sleep_sec)


#gtk gui ----------------------------------------------------------------------
#pe_list will be set to:0 type, 1 config, 2 name, 3 prev_value_list,
#			4 value_list, 5 x_list, 6 button_list,
#			7 button_color_list, 8 line_color_list
if gui_type == 1:
	#This script need python-gtk2
	import gtk
	import glib

	pe_list_value = 5
	pe_list_x = 6
	pe_list_button = 7
	pe_list_bcolor = 8
	pe_list_lcolor = 9

	pe_color = (0xffb0ff, 0x006000)

	class PyApp(gtk.Window):
		#Init ----------------------------------------------------------
		def __init__(self):
			global pe_list, cpu_number

			super(PyApp, self).__init__()

			self.max_value = 0
			self.prev_width = 0
			self.prev_height = 0
			self.y_ratio = 0
			self.entry_width = 10
			self.logfd = False

			#Set the pe
			each_entry(self.pe_init_callback)

			#Set the color
			num = len(pe_list) * cpu_number
			block = (pe_color[0] - pe_color[1]) / float(num)
			color = pe_color[1]
			for i in range(0, cpu_number):
				for e in pe_list:
					e[pe_list_bcolor].append(gtk.gdk.Color("#"+ "%06x" % int(color)))
					e[pe_list_lcolor].append((((int(color) >> 16) / float(0xff) * 1), ((int(color) >> 8 & 0xff) / float(0xff) * 1), ((int(color) & 0xff) / float(0xff) * 1)))
					color += block

			#Set window
			self.set_title("KGTP")
			self.connect("destroy", gtk.main_quit)
			gtk.Window.maximize(self)

			#menubar
			mb = gtk.MenuBar()
			#file
			filemenu = gtk.Menu()
			filem = gtk.MenuItem("File")
			filem.set_submenu(filemenu)
			save = gtk.CheckMenuItem("Save log to a CSV file")
			save.connect("activate", self.mb_save)
			save.set_active(False)
			exit = gtk.MenuItem("Exit")
			exit.connect("activate", gtk.main_quit)
			filemenu.append(save)
			filemenu.append(gtk.SeparatorMenuItem())
			filemenu.append(exit)
			mb.append(filem)
			#set
			setmenu = gtk.Menu()
			setm = gtk.MenuItem("Settings")
			setm.set_submenu(setmenu)
			show_buttons = gtk.CheckMenuItem("Show buttons")
			show_buttons.set_active(True)
			show_buttons.connect("activate", self.show_buttons)
			setmenu.append(show_buttons)
			mb.append(setm)

			#Widget
			#Creat self.darea
			self.darea = gtk.DrawingArea()
			self.darea.connect("expose-event", self.expose)
			self.darea.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#FFFFFF"))
			#Creat all ToggleButton for each pe
			each_entry(self.pe_gtk_creat_button)
			#Creat button_hboxes
			self.button_hboxes = self.pe_gtk_creat_button_hboxes_first()

			#Add mb and widget to window
			self.vbox = gtk.VBox(False, 0)
			self.vbox.pack_start(mb, False, False, 0)
			self.vbox.pack_start(self.darea, True, True, 0)
			for e in self.button_hboxes:
				self.vbox.pack_start(e, False, False, 0)
			self.add(self.vbox)

			#First show to get the right size
			self.show_all()
			size = self.pe_gtk_get_size()

			#Reset the button_hboxes
			each_entry(self.pe_gtk_remove_creat_button_hboxes)
			for e in self.button_hboxes:
				self.vbox.remove(e)
			self.button_hboxes = self.pe_gtk_creat_button_hboxes_second(size)
			for e in self.button_hboxes:
				self.vbox.pack_start(e, False, False, 0)
			self.show_all()

			#Reset the value of each button
			each_entry(self.button_reset)

			#Add timer
			glib.timeout_add(int(sleep_sec * 1000), self.timer_cb)
			#Remove the first entry because it already record a big value
			glib.timeout_add(int(sleep_sec * 1100), self.timer_remove_first_record)

		def __del__(self):
			if self.logfd:
				self.logfd.close()
				self.logfd = False

		def pe_init_callback(self, i, e):
			if (len(e) < pe_list_value + 1):
				e.append([])
			e[pe_list_value].append([])
			if (len(e) < pe_list_x + 1):
				e.append([])
			e[pe_list_x].append([])
			if (len(e) < pe_list_button + 1):
				e.append([])
			if (len(e) < pe_list_button + 1):
				e.append([])
			if (len(e) < pe_list_bcolor + 1):
				e.append([])
			if (len(e) < pe_list_lcolor + 1):
				e.append([])

		def pe_gtk_creat_button(self, i, e):
			e[pe_list_button].append(gtk.ToggleButton(e[pe_list_name]+":"+str(18446744073709551615)))
			self.set_button_color(e[pe_list_button][i], e[pe_list_bcolor][i])
			e[pe_list_button][i].connect("clicked", self.button_click)

		def pe_gtk_creat_button_hboxes_first(self):
			global pe_list, cpu_number

			hboxes = []
			self.label_list = []
			for i in range(0, cpu_number):
				hboxes.append(gtk.HBox(False, 0))
				self.label_list.append(gtk.Label("CPU"+str(i)))
				hboxes[i].pack_start(self.label_list[i], False, False, 0)
				for e in pe_list:
					hboxes[i].pack_start(e[pe_list_button][i], False, False, 0)

			return hboxes

		def pe_gtk_get_size(self):
			global pe_list, cpu_number

			#0 label size 1 button size
			size = ([],[])
			for i in range(0, cpu_number):
				size[0].append(self.label_list[i].allocation.width)
				size[1].append([])
				for e in pe_list:
					size[1][i].append(e[pe_list_button][i].allocation.width)

			return size

		def pe_gtk_remove_creat_button_hboxes(self, i, e):
			self.button_hboxes[i].remove(e[pe_list_button][i])

		def pe_gtk_creat_button_hboxes_second(self, size):
			global pe_list, cpu_number

			hboxes = []
			hbox_id = -1
			for i in range(0, cpu_number):
				keep_going = True
				prev_entry_id = 0
				while keep_going == True:
					width = self.allocation.width
					keep_going = False
					hbox_id += 1
					hboxes.append(gtk.HBox(False, 0))
					width -= size[0][i]
					hboxes[hbox_id].pack_start(gtk.Label("CPU"+str(i)), False, False, 0)
					for j in range(prev_entry_id, len(pe_list)):
						if width - size[1][i][j] <= 0:
							prev_entry_id = j
							keep_going = True
							break
						width -= size[1][i][j] + 200
						hboxes[hbox_id].pack_start(pe_list[j][pe_list_button][i], False, False, 0)

			return hboxes

		def button_reset(self, i, e):
			e[pe_list_button][i].set_label(e[pe_list_name]+":0")

		#Dialog -------------------------------------------------------
		def dialog_error(self, msg):
			md = gtk.MessageDialog(self,gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, msg)
			md.run()
			md.destroy()

		#Menubar -------------------------------------------------------
		def show_buttons(self, widget):
			if widget.active:
				for e in self.button_hboxes:
					e.show()
			else:
				for e in self.button_hboxes:
					e.hide()

		def log_write_name(self, i, e):
			self.logfd.write("CPU"+str(i)+" "+e[pe_list_name]+",")

		def mb_save(self, widget):
			if widget.active:
				md = gtk.FileChooserDialog(title="Save log to a CSV file", action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK, gtk.RESPONSE_OK))
				md.set_do_overwrite_confirmation(True)
				md.set_current_name("pe.csv")
				if md.run() == gtk.RESPONSE_OK:
					try:
						self.logfd = open(md.get_filename(), "w")
						each_entry(self.log_write_name)
						self.logfd.write("\n")
					except:
						self.dialog_error("Try to open file "+md.get_filename()+" got error")
						widget.set_active(False)
						if self.logfd:
							self.logfd.close()
							self.logfd = False
				else:
					widget.set_active(False)
				md.destroy()
			else:
				if self.logfd:
					self.logfd.close()
					self.logfd = False

		#Button --------------------------------------------------------
		def refind_max_value(self, i, e):
			if e[pe_list_button][i].get_active():
				return
			for i in e[pe_list_value][i]:
				if i > self.max_value:
					self.max_value = i
					self.y_ratio = 0

		def set_button_color(self, button, color):
			style = button.get_style().copy()
			style.bg[gtk.STATE_NORMAL] = color
			style.bg[gtk.STATE_ACTIVE] = color
			style.bg[gtk.STATE_PRELIGHT] = color
			style.bg[gtk.STATE_SELECTED] = color
			style.bg[gtk.STATE_INSENSITIVE] = color
			button.set_style(style)

		def button_click(self, widget):
			if widget.get_active():
				self.set_button_color(widget, gtk.gdk.Color("#FFFFFF"))
			else:
				color = False
				for i in range(0, cpu_number):
					for e in pe_list:
						if e[pe_list_button][i] == widget:
							color = e[pe_list_bcolor][i]
							break
					if color:
						break
				if color:
					self.set_button_color(widget, color)
				each_entry(self.refind_max_value)
			self.darea.queue_draw()

		#Timer ---------------------------------------------------------
		def write_csv(self, msg):
			try:
				self.logfd.write(msg)
			except:
				self.dialog_error("Writ CSV file got error")
				widget.set_active(False)
				self.logfd.close()
				self.logfd = False

		def pe_gtk_add(self, i, e):
			if in_gdb:
				current_value = long(gdb.parse_and_eval("$p_pe_val_"+e[pe_list_type]+e[pe_list_config]+"_"+str(i)))
			else:
				current_value = gtp.tvariable_val_raw(e[pe_list_qtv][i])
				if current_value == None:
					print "Fail when get val from KGTP"
					exit(0)
			this_value = current_value-e[pe_list_prev][i]
			e[pe_list_value][i].append(this_value)
			if this_value > self.max_value and not e[pe_list_button][i].get_active():
				self.max_value = this_value
				self.y_ratio = 0
			e[pe_list_x][i].append(-1)
			e[pe_list_prev][i] = current_value
			e[pe_list_button][i].set_label(e[pe_list_name]+":"+str(this_value))
			if self.logfd:
				write_csv(str(this_value)+",")

		def timer_cb(self):
			each_entry(self.pe_gtk_add)
			if self.logfd:
				write_csv("\n")
			self.darea.queue_draw()
			return True

		def timer_remove_first_record(self):
			if len(pe_list[0][pe_list_value][0]) >= 1:
				self.pe_remove_entry_num = 1
				each_entry(self.pe_remove_entry)
				return False
			else:
				return True

		#DrawingArea ---------------------------------------------------
		def pe_gtk_line(self, i, e):
			if len(e[pe_list_value][i]) < 2:
				return
			if e[pe_list_button][i].get_active():
				return

			self.cr.set_source_rgb(e[pe_list_lcolor][i][0], e[pe_list_lcolor][i][1], e[pe_list_lcolor][i][2])
			x = 0
			for num in range(0, len(e[pe_list_value][i])):
				if e[pe_list_value][i][num] > self.line_max:
					self.line_max = e[pe_list_value][i][num]
				if self.height_change or e[pe_list_x][i][num] < 0:
					e[pe_list_x][i][num] = self.prev_height - e[pe_list_value][i][num] * self.y_ratio
				if num == 0:
					self.cr.move_to(x, e[pe_list_x][i][num])
				else:
					self.cr.line_to(x, e[pe_list_x][i][num])
				x += self.entry_width
			self.cr.stroke()

		def pe_remove_entry(self, i, e):
			del(e[pe_list_value][i][0:self.pe_remove_entry_num])
			del(e[pe_list_x][i][0:self.pe_remove_entry_num])

		def expose(self, widget, event):
			self.cr = widget.window.cairo_create()

			#y
			if self.prev_height != self.darea.allocation.height:
				self.height_change = True
				self.prev_height = self.darea.allocation.height
			else:
				self.height_change = False
			if self.max_value > 0 and (self.height_change or self.y_ratio == 0):
				self.max_value += 100 - self.max_value % 100
				self.y_ratio = float(self.prev_height)/self.max_value
				self.height_change = True

			#x
			x_size = len(pe_list[0][pe_list_value][0])
			entry_number = 0
			if self.entry_width * x_size > self.darea.allocation.width:
				entry_number = self.darea.allocation.width // self.entry_width
				self.pe_remove_entry_num = x_size - entry_number
				each_entry(self.pe_remove_entry)

			#dash
			self.cr.set_source_rgb(0, 0, 0)
			self.cr.set_dash((1, 5))
			#dash line for x
			if entry_number == 0:
				entry_number = self.darea.allocation.width // self.entry_width
			x = 0
			while x < self.darea.allocation.width:
				x += self.entry_width * 10
				self.cr.move_to(x, 0)
				self.cr.line_to(x, self.prev_height)
			#dash line for y
			self.cr.move_to(0, 10)
			self.cr.show_text(str(self.max_value))

			self.cr.move_to(0, self.darea.allocation.height/4*3)
			self.cr.show_text(str(self.max_value/4*3))
			self.cr.line_to(self.darea.allocation.width, self.darea.allocation.height/4*3)

			self.cr.move_to(0, self.darea.allocation.height/2)
			self.cr.show_text(str(self.max_value/2))
			self.cr.line_to(self.darea.allocation.width, self.darea.allocation.height/2)

			self.cr.move_to(0, self.darea.allocation.height/4)
			self.cr.show_text(str(self.max_value/4))
			self.cr.line_to(self.darea.allocation.width, self.darea.allocation.height/4)

			self.cr.stroke()
			self.cr.set_dash(())

			self.line_max = 0
			each_entry(self.pe_gtk_line)
			if self.line_max > 0 and self.line_max * 2 < self.max_value:
				self.max_value = self.line_max
				self.y_ratio = 0

			self.height_change = False

	PyApp()
	gtk.main()
	if in_gdb:
		gdb.execute("tstop", True, False)
	else:
		gtp.tstop()
	exit(0)
