#!/usr/bin/python

import gtk
import glib
import traceback

version = '20120605+'

def modelName():
	return __name__

def run():
	gtk.main()

class gtpline:
	def __init__(self, name):
		self.name = name
		self.val = []
		self.y = []

	def val_number(self):
		return len(self.val)

	def add(self, val):
		self.val.append(val)
		self.y.append(-1)

	def remove_head(self, num):
		if self.val_number() > 0:
			if num == 0:
				del(self.val[0:])
				del(self.y[0:])
			else:
				del(self.val[0:num])
				del(self.y[0:num])

	def load_new_val(self):
		'''GUI will auto call this function each sec that you set.  Use this function call self.add to add new val to this line.
		If really got value, add and return it.  If not, add and return 0.'''
		self.add(0)
		return 0

class gtpwin(gtk.Window):
	def __init__(self, lines, title = "", sec = 1, width = 10, remove_first = False, button_each_line = 4):
		"""lines: the line class list to show.
		title: the window title.
		sec: the load new entry wait second.
		width: the width of each entry.
		remove_first :true then remove the first entry because it already record a big value.
		button_each_line: the number of button of each line.
		"""
		super(gtpwin, self).__init__()

		self.entry_width = width

		self.max_value = 0
		self.prev_width = 0
		self.prev_height = 0
		self.y_ratio = 0
		self.logfd = False

		#Setup lines
		color_limit = (0xffb0ff, 0x006000)
		num = len(lines)
		block = (color_limit[0] - color_limit[1]) / float(num)
		color = color_limit[1]
		for e in lines:
			e.bcolor = gtk.gdk.Color("#"+ "%06x" % int(color))
			e.lcolor = ((((int(color) >> 16) / float(0xff) * 1), ((int(color) >> 8 & 0xff) / float(0xff) * 1), ((int(color) & 0xff) / float(0xff) * 1)))
			color += block
		self.lines = lines

		#Set window
		self.set_title(title)
		self.connect("destroy", gtk.main_quit)

		#Create button
		bhbox = gtk.HBox(False, 0)
		self.button_hboxes = [bhbox]
		num = 0
		for line in self.lines:
			line.button = gtk.ToggleButton(line.name)
			self.set_button_color(line.button, line.bcolor)
			line.button.line = line
			line.button.connect("clicked", self.button_click)
			line.entry = gtk.Entry()
			line.entry.set_editable(False)
			hbox = gtk.HBox(False, 0)
			hbox.pack_start(line.button, False, False, 0)
			hbox.pack_start(line.entry, False, False, 0)
			bhbox.pack_start(hbox, True, False, 0)
			num += 1
			if num >= button_each_line:
				bhbox = gtk.HBox(False, 0)
				self.button_hboxes.append(bhbox)
				num = 0

		#Create self.darea
		self.darea = gtk.DrawingArea()
		self.darea.connect("expose-event", self.expose)
		self.darea.modify_bg(gtk.STATE_NORMAL, gtk.gdk.Color("#FFFFFF"))

		#menubar
		mb = gtk.MenuBar()
		#file
		filemenu = gtk.Menu()
		filem = gtk.MenuItem("File")
		filem.set_submenu(filemenu)
		save = gtk.CheckMenuItem("Save log to a CSV file")
		save.connect("activate", self.mb_save)
		save.set_active(False)
		clean = gtk.MenuItem("Clean")
		clean.connect("activate", self.mb_clean)
		exit = gtk.MenuItem("Exit")
		exit.connect("activate", gtk.main_quit)
		filemenu.append(save)
		filemenu.append(clean)
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

		#Put widgets to window
		vbox = gtk.VBox(False, 0)
		vbox.pack_start(mb, False, False, 0)
		vbox.pack_start(self.darea, True, True, 0)
		for e in self.button_hboxes:
			vbox.pack_start(e, False, False, 0)
		self.add(vbox)

		self.show_all()
		gtk.Window.maximize(self)

		#Set each button to same width
		button_size_max = 0
		entry_size_max = 0
		for line in self.lines:
			if line.button.allocation.width > button_size_max:
				button_size_max = line.button.allocation.width
			if line.entry.allocation.width > entry_size_max:
				entry_size_max = line.entry.allocation.width
		for line in self.lines:
			line.button.set_size_request(button_size_max, -1)
			line.entry.set_size_request(entry_size_max, -1)

		#Add timer
		glib.timeout_add(int(sec * 1000), self.timer_cb)
		if remove_first:
			glib.timeout_add(int(sec * 1100), self.timer_remove_first_record)

	def __del__(self):
		if self.logfd:
			self.logfd.close()
			self.logfd = False
		super(gtpwin, self).__del__()

	def each_lines(self, callback, argument = 0):
		for line in self.lines:
			callback(line, argument)

	#DrawingArea ---------------------------------------------------
	def expose(self, widget, event):
		cr = widget.window.cairo_create()

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
		entry_number = 0
		if self.entry_width * self.lines[0].val_number() > self.darea.allocation.width:
			self.entry_number = self.darea.allocation.width // self.entry_width
			for line in self.lines:
				if line.val_number() > self.entry_number:
					line.remove_head(line.val_number() - self.entry_number)

		#dash
		cr.set_source_rgb(0, 0, 0)
		cr.set_dash((1, 5))
		#dash line for x
		x = 0
		while x < self.darea.allocation.width:
			x += self.entry_width * 10
			cr.move_to(x, 0)
			cr.line_to(x, self.prev_height)
		#dash line for y
		cr.move_to(0, 10)
		cr.show_text(str(self.max_value))
		cr.move_to(0, self.darea.allocation.height/4*3)
		cr.show_text(str(self.max_value/4))
		cr.line_to(self.darea.allocation.width, self.darea.allocation.height/4*3)
		cr.move_to(0, self.darea.allocation.height/2)
		cr.show_text(str(self.max_value/2))
		cr.line_to(self.darea.allocation.width, self.darea.allocation.height/2)
		cr.move_to(0, self.darea.allocation.height/4)
		cr.show_text(str(self.max_value/4*3))
		cr.line_to(self.darea.allocation.width, self.darea.allocation.height/4)
		cr.stroke()
		cr.set_dash(())

		#lines
		self.line_max = 0
		self.each_lines(self.draw_line, cr)
		if (self.line_max > 0 and (self.line_max * 2 < self.max_value or self.line_max > self.max_value)) or self.max_value == 0:
			self.max_value = self.line_max
			self.y_ratio = 0
		self.height_change = False

	def draw_line(self, line, cr):
		if line.button.get_active():
			return
		if line.val_number() < 2:
			return

		cr.set_source_rgb(line.lcolor[0], line.lcolor[1], line.lcolor[2])
		x = 0
		for num in range(0, line.val_number()):
			if self.height_change or line.y[num] < 0:
				line.y[num] = self.prev_height - line.val[num] * self.y_ratio
			if line.val[num] > self.line_max:
				self.line_max = line.val[num]
			if num == 0:
				cr.move_to(x, line.y[num])
			else:
				cr.line_to(x, line.y[num])
			x += self.entry_width
		cr.stroke()

	#Timer ---------------------------------------------------------
	def timer_cb(self):
		for line in self.lines:
			val = 0
			try:
				val = line.load_new_val()
			except:
				print("Load new value from "+line.name+" fail because:")
				traceback.print_exc()
			line.entry.set_text(str(val))
			if self.logfd:
				self.write_csv(str(val)+",")
		if self.logfd:
			self.write_csv("\n")
		self.darea.queue_draw()
		return True

	def timer_remove_first_record(self):
		if self.lines[0].val_number() > 0:
			for line in self.lines:
				line.remove_head(1)
			return False
		else:
			return True

	def write_csv(self, msg):
		try:
			self.logfd.write(msg)
		except:
			self.dialog_error("Writ CSV file got error")
			widget.set_active(False)
			self.logfd.close()
			self.logfd = False

	#Menubar -------------------------------------------------------
	def mb_save(self, widget):
		if widget.active:
			md = gtk.FileChooserDialog(title="Save log to a CSV file", action=gtk.FILE_CHOOSER_ACTION_SAVE, buttons = (gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OK, gtk.RESPONSE_OK))
			md.set_do_overwrite_confirmation(True)
			md.set_current_name("pe.csv")
			if md.run() == gtk.RESPONSE_OK:
				try:
					self.logfd = open(md.get_filename(), "w")
					for line in self.lines:
						self.logfd.write(line.name + ",")
					self.logfd.write("\n")
					for i in range(0, self.lines[0].val_number()):
						for line in self.lines:
							self.logfd.write(str(line.val[i]) + ",")
						self.logfd.write("\n")
				except:
					if self.logfd:
						self.logfd.close()
						self.logfd = False
					self.dialog_error("Try to open file "+md.get_filename()+" got error")
					widget.set_active(False)
			else:
				widget.set_active(False)
			md.destroy()
		else:
			if self.logfd:
				self.logfd.close()
				self.logfd = False

	def mb_clean(self, widget):
		for line in self.lines:
			line.remove_head(0)
		self.darea.queue_draw()

	def show_buttons(self, widget):
		if widget.active:
			for e in self.button_hboxes:
				e.show()
		else:
			for e in self.button_hboxes:
				e.hide()

	#Button --------------------------------------------------------
	def button_click(self, widget):
		if widget.get_active():
			self.set_button_color(widget, gtk.gdk.Color("#FFFFFF"))
		else:
			self.set_button_color(widget, widget.line.bcolor)
			for val in widget.line.val:
				if val > self.max_value:
					self.max_value = val
					self.y_ratio = 0
		self.darea.queue_draw()

	def set_button_color(self, button, color):
		style = button.get_style().copy()
		style.bg[gtk.STATE_NORMAL] = color
		style.bg[gtk.STATE_ACTIVE] = color
		style.bg[gtk.STATE_PRELIGHT] = color
		style.bg[gtk.STATE_SELECTED] = color
		style.bg[gtk.STATE_INSENSITIVE] = color
		button.set_style(style)

	#Dialog -------------------------------------------------------
	def dialog_error(self, msg):
		md = gtk.MessageDialog(self,gtk.DIALOG_DESTROY_WITH_PARENT, gtk.MESSAGE_ERROR, gtk.BUTTONS_CLOSE, msg)
		md.run()
		md.destroy()
