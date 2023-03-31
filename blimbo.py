import re
import subprocess
from sys import argv
from os import walk, path
from PIL import Image

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


loc: str = '.'
isloc: bool = True
files: list[str] = []

def handle_args():
	p = ''
	i = 1
	global loc, isloc
	while i < len(argv):
		if argv[i] == '-p': # prepend
			i += 1
			p = argv[i]
		elif path.isdir(argv[i]):
			loc = argv[i][:-1] if argv[i][-1] == '/' else argv[i]
		else: files.append(argv[i])
		i += 1
	if files: isloc = False
	return p


class Blimp:
	def __init__(self, loc, name, ext, pump):
		self.loc, self.name, self.ext = loc, name, ext
		full = f'{loc}/{name}{ext}'
		self.date = path.getmtime(full)

		if type(pump) == str:
		# rename
			self.dup = bool(re.search(r'\([0-9]+\)$', name))
			bxt = ext
			try:
				with Image.open(full) as img:
					format = img.format
					if   format == 'JPEG': bxt = '.jpg'
					else: bxt = '.' + format.lower()
			except Exception as e:
				print(f'{full}: {e}')
			self.chx = (bxt != ext)

			self.xst = (name != pump and path.isfile(f'{loc}/{pump}{bxt}'))
			if self.xst:
				count = 1
				while path.isfile(f'{loc}/{pump} ({count}){bxt}'): count += 1
				pump += f'({count})'
			self.pump = pump + bxt
		else:
		# resize
			self.size = f"{pump['size']:.2f}MB"
			self.asp, self.pct = pump['asp'], pump['pct']
		self.full = full

	def plump(self):
		return f'{self.loc}/{self.pump}'
#end Blimp


blimps: list[Blimp] = []

def absoluteFilePaths(dir):
	for dirpath,_,filenames in walk(dir):
		for f in filenames:
			yield path.abspath(path.join(dirpath, f))
		break

def ogle(ogler):
	global blimps, files
	blimps = []
	if isloc:
		files = list(absoluteFilePaths(loc))
	ogler(files)

def open_file(filename):
	command = ['kde-open5', filename]
	try: subprocess.Popen(command, shell=False)
	except: pass

def show_in_file_manager(filename):
	command = ['dolphin', '--select', filename]
	try: subprocess.Popen(command, shell=False)
	except: pass

def plur(noun):
	count = len(blimps)
	return f"{count} {noun}{'s' if count != 1 else ''}"

def comparename(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).name
	value2 = model.get_value(row2, user_data).name
	return docompare(value1, value2)

def comparepump(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).pump
	value2 = model.get_value(row2, user_data).pump
	return docompare(value1, value2)

def comparedate(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).date
	value2 = model.get_value(row2, user_data).date
	return docompare(value1, value2)

def comparesize(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).size
	value2 = model.get_value(row2, user_data).size
	return docompare(value1, value2)

def compareext(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).ext
	value2 = model.get_value(row2, user_data).ext
	return docompare(value1, value2)

def docompare(value1, value2):
	if value1 < value2:
		return -1
	elif value1 == value2:
		return 0
	else:
		return 1


class BlimpWindow(Gtk.Window):
	def __init__(self):
		super().__init__(title = f'Image {self.act}r')
		self.connect('destroy', Gtk.main_quit)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_border_width(10)
		model = self.model

		# set up the grid in which the elements are to be positioned
		grid = Gtk.Grid()
		grid.set_column_homogeneous(True)
		grid.set_row_homogeneous(True)
		self.add(grid)

		# display results and path
		count = Gtk.Label(label=plur('result'))
		lblpath = Gtk.Label(label=loc)
		lblpath.set_xalign(0.95)
		grid.attach(count, 0, 0, 1, 1)
		grid.attach_next_to(lblpath, count, Gtk.PositionType.RIGHT, self.wid, 1)

		# create buttons and set up their events
		btnrescan = Gtk.Button(label='Rescan')
		btnrescan.connect('clicked', self.on_rescan_clicked)
		btnremove = Gtk.Button(label='Remove')
		btnremove.connect('clicked', self.on_remove_clicked)
		btncommit = Gtk.Button(label='Commit')
		btncommit.connect('clicked', self.on_commit_clicked)
		self.butns = [btnrescan, btnremove, btncommit]
		self.rescan = btnrescan
		self.remove = btnremove
		self.commit = btncommit

		# create the treeview
		view = Gtk.TreeView(model=model)
		slect = view.get_selection()
		slect.set_mode(Gtk.SelectionMode.MULTIPLE)
		view.connect('row-activated', self.on_row_activated)
		view.connect('button-press-event', self.on_button_press_event)
		rend = Gtk.CellRendererText()
		rend.set_property('ypad', 12)

		# add the columns
		for i, title in enumerate(model.cols):
			col = Gtk.TreeViewColumn(title, rend, text=i)
			col.set_property('resizable', True)
			col.set_sort_column_id(i)
			view.append_column(col)

		# create the popup menu
		pmenu = Gtk.Menu()
		for [action, func] in [
			 ['Open', self.on_open_activate]
			,['Show in File Manager', self.on_show_activate]
			,['Show Original File', self.on_orig_activate]
		]:
			item = Gtk.MenuItem(label=action)
			item.connect('activate', self.on_activate)
			item.fn = func
			pmenu.append(item)
		pmenu.show_all()

		# set member variables
		self.count = count
		self.slect = slect
		self.pmenu = pmenu
		self.grid  = grid
		self.view  = view

	def set_sensitives(self):
		on = (len(blimps) > 0)
		self.remove.set_sensitive(on)
		self.commit.set_sensitive(on)

	def fillerup(self):
		self.set_sensitives()

	def on_rescan_clicked(self, button):
		self.count.set_text(plur('result'))
		self.model.clear()
		self.fillerup()
		self.set_focus(None)

	def on_remove_clicked(self, button):
		model, paths = self.slect.get_selected_rows()
		rows = []
		for row in paths:
			rows.append(model.get_iter(row))
		for row in rows:
			blimp = model.get_value(row, self.idx)
			blimps.remove(blimp)
			if not isloc:
				files.remove(blimp.full)
			model.remove(row)
		self.count.set_text(plur('result'))
		self.slect.unselect_all()
		self.set_sensitives()
		self.set_focus(None)

	def on_commit_clicked(self, button):
		dialog = Gtk.MessageDialog(
			 parent = self
			,title = 'Confirm'
			,message_type = Gtk.MessageType.OTHER
			,buttons = Gtk.ButtonsType.YES_NO
			,text = f"{self.act} {plur('file')}?"
		)
		response = dialog.run()
		dialog.destroy()
		self.set_focus(None)
		return response

	def on_row_activated(self, tv, row, col):
		blimp = self.model.get_value(self.model.get_iter(row), self.idx)
		open_file(blimp.full)

	def on_button_press_event(self, widget, event):
		if event.type == Gdk.EventType.BUTTON_PRESS:
			if event.button == 3 or event.button == 2:
				self.pmenu.popup_at_pointer()

	def on_activate(self, item):
		for row in self.slect.get_selected_rows()[1]:
			item.fn(self.model.get_value(self.model.get_iter(row), self.idx))

	def on_open_activate(self, blimp):
		open_file(blimp.full)

	def on_show_activate(self, blimp):
		show_in_file_manager(blimp.full)

	def on_orig_activate(self, blimp):
		orig = blimp.pump if blimp.xst else blimp.name
		orig = re.sub(r'\([0-9]+\)', '', orig)
		open_file(f'{blimp.loc}/{orig}')
#end BlimpWindow
