import os
from sys import argv
from typing import Callable
from subprocess import Popen

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

loc: str = '.'
isloc: bool = True
files: list[str] = []

def default_args(i: int):
	global loc, isloc
	while i < len(argv):
		if os.path.isdir(argv[i]):
			loc = argv[i][:-1] if argv[i][-1] == '/' else argv[i]
		else: files.append(argv[i])
		i += 1
	if files: isloc = False

loc = os.path.abspath(os.path.expanduser(loc))

class Blimp:
	def __init__(self, loc:str, name:str, ext:str):
		self.loc, self.name, self.ext = loc, name, ext
		self.full = f'{loc}/{name}{ext}'
		self.date = os.path.getmtime(self.full)

blimps: list[Blimp] = []

def ogle(ogler: Callable):
	global blimps, files
	blimps = []
	if isloc:
		for root, _, names in os.walk(loc):
			files = [os.path.abspath(os.path.join(root, f)) for f in names]
			break
	ogler(files)

def open_file(filename: str):
	Popen(['kde-open5', filename]).wait()

def show_in_file_manager(filename: str):
	Popen(['dolphin', '--select', filename]).wait()

def plur(noun: str):
	count = len(blimps)
	return f"{count} {noun}{'s' if count != 1 else ''}"

def comparename(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).name
	value2 = model.get_value(row2, user_data).name
	return -1 if value1 < value2 else 0 if value1 == value2 else 1

def comparepump(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).pump
	value2 = model.get_value(row2, user_data).pump
	return -1 if value1 < value2 else 0 if value1 == value2 else 1

def comparedate(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).date
	value2 = model.get_value(row2, user_data).date
	return -1 if value1 < value2 else 0 if value1 == value2 else 1

def comparesize(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).size
	value2 = model.get_value(row2, user_data).size
	return -1 if value1 < value2 else 0 if value1 == value2 else 1

def compareext(model, row1, row2, user_data):
	value1 = model.get_value(row1, user_data).ext
	value2 = model.get_value(row2, user_data).ext
	return -1 if value1 < value2 else 0 if value1 == value2 else 1


class BlimpWindow(Gtk.Window):
	def __init__(self, model, widgets):
		super().__init__(title = f'Image {self.act}r')
		self.connect('destroy', Gtk.main_quit)
		self.set_position(Gtk.WindowPosition.CENTER)
		self.set_border_width(10)

		# CSS styling
		provider = Gtk.CssProvider()
		Gtk.StyleContext().add_provider_for_screen(Gdk.Screen.get_default(),
			provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
		provider.load_from_data(b'''
			.path { padding-right: 20px }
			.tree { padding-right: 15px }
		''')

		# create default widgets and set up their events
		chk_loc = Gtk.CheckButton(label="Loc")
		chk_loc.set_active(isloc)
		chk_loc.connect("toggled", self.on_loc_toggled)
		btn_scn = Gtk.Button(label='Rescan')
		btn_rem = Gtk.Button(label='Remove')
		btn_com = Gtk.Button(label='Commit')
		btn_rem.connect('clicked', self.on_remove_clicked)
		btn_scn.connect('clicked', self.on_rescan_clicked)
		btn_com.connect('clicked', self.on_commit_clicked)
		chk_loc.wid, btn_scn.wid, btn_rem.wid, btn_com.wid = 1, 1, 1, 1
		widgets += [chk_loc, btn_scn, btn_rem, btn_com]

		# set up the grid in which the elements are to be positioned
		grid = Gtk.Grid()
		grid.set_column_homogeneous(True)
		grid.set_row_homogeneous(True)
		self.add(grid)

		# display results and path
		lbl_amt = Gtk.Label(label=plur('result'))
		lbl_path = Gtk.Label(label=loc)
		lbl_path.set_xalign(1)
		context = lbl_path.get_style_context()
		context.add_class('path')

		# create scrollable treeview
		tree = Gtk.TreeView(model=model)
		scroll = Gtk.ScrolledWindow()
		scroll.set_vexpand(True)
		scroll.add(tree)
		select = tree.get_selection()
		select.set_mode(Gtk.SelectionMode.MULTIPLE)
		tree.connect('row-activated', self.on_row_activated)
		tree.connect('button-press-event', self.on_button_press_event)
		context = tree.get_style_context()
		context.add_class('tree')
		rend = Gtk.CellRendererText()
		rend.set_property('ypad', 12)

		# add the columns
		cols = [Gtk.TreeViewColumn(title, rend, text=i)
			for i, title in enumerate(model.cols)]
		cols[0].set_visible(False)
		cols[1].set_expand(True)
		for i, col in enumerate(cols):
			col.set_property('resizable', True)
			col.set_sort_column_id(i)
			tree.append_column(col)

		wid = sum(w.wid for w in widgets)
		grid.attach(lbl_amt, 0, 0, 1, 1)
		grid.attach_next_to(lbl_path, lbl_amt, Gtk.PositionType.RIGHT, wid - 1, 1)
		grid.attach_next_to(scroll, lbl_amt, Gtk.PositionType.BOTTOM, wid, 16)
		grid.attach_next_to(widgets[0], scroll, Gtk.PositionType.BOTTOM, widgets[0].wid, 1)
		for i in range(1, len(widgets)):
			a, b = widgets[i - 1], widgets[i]
			grid.attach_next_to(b, a, Gtk.PositionType.RIGHT, b.wid, 1)

		# create the popup menu
		popup = Gtk.Menu()
		for [action, func] in [
			['Open', self.on_open_activate],
			['Show in File Manager', self.on_show_activate]
		]:
			item = Gtk.MenuItem(label=action)
			item.connect('activate', self.on_activate)
			item.fn = func
			popup.append(item)
		popup.show_all()

		# member variables
		self.lbl_amt = lbl_amt
		self.btn_rem = btn_rem
		self.btn_com = btn_com
		self.select  = select
		self.model   = model
		self.popup   = popup

	def feed(self):
		raise NotImplementedError()

	def set_sensitives(self):
		on = (len(blimps) > 0)
		self.btn_rem.set_sensitive(on)
		self.btn_com.set_sensitive(on)

	def on_rescan_clicked(self, button):
		self.lbl_amt.set_text(plur('result'))
		self.model.clear()
		self.feed()
		self.set_focus(None)

	def on_remove_clicked(self, button):
		model, paths = self.select.get_selected_rows()
		rows = []
		for row in paths:
			rows.append(model.get_iter(row))
		for row in rows:
			blimp = model.get_value(row, 0)
			blimps.remove(blimp)
			if not isloc:
				files.remove(blimp.full)
			model.remove(row)
		self.lbl_amt.set_text(plur('result'))
		self.select.unselect_all()
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

	def on_loc_toggled(self, chk):
		global isloc, files
		isloc = chk.get_active()
		if not isloc:
			files = [b.full for b in blimps]

	def on_row_activated(self, tv, row, col):
		blimp = self.model.get_value(self.model.get_iter(row), 0)
		open_file(blimp.full)

	def on_button_press_event(self, widget, event):
		if event.type == Gdk.EventType.BUTTON_PRESS:
			if event.button == 3 or event.button == 2:
				self.popup.popup_at_pointer()

	def on_activate(self, item):
		for row in self.select.get_selected_rows()[1]:
			item.fn(self.model.get_value(self.model.get_iter(row), 0))

	def on_open_activate(self, blimp: Blimp):
		open_file(blimp.full)

	def on_show_activate(self, blimp: Blimp):
		show_in_file_manager(blimp.full)
#end BlimpWindow
