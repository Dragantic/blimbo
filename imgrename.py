#!/usr/bin/env python3

import re, time
from os import path, rename, system

import blimbo as b
from blimbo import Blimp, BlimpWindow, Gtk


prepend = ''

ptrnFA = r'^(?P<pre>\d{10}\..+[\._-])*(?P<tag>\d{10})[\._-]' \
	+ r'(?P<artist>[\.\~0-9A-Za-z-]+)_[_-]*' \
	+ r'(?P<title>(?:[_-]*(?!\.(?:png|jpe?g|gif|swf)$)' \
	+ r'(?:[\.\(\)\[\]\{\} 0-9A-Za-z+%!,]|[^\x00-\x80]))+)'

ptrnDA = r'^(?P<pre>)_*(?P<title>(?:[_-]*[\(\)0-9A-Za-z+!])+)' \
	+ r'_*_by_(?P<artist>(?:[_-]*[\(\)0-9A-Za-z+!])+)' \
	+ r'[~_-](?P<tag>[0-9A-Za-z]{7}(?![0-9A-Za-z]+)(?:-pre)?)'


def ogler(files):
	for x in files:
		split = path.split(x)
		name = path.splitext(split[1])
		pump = None
		m = re.match(ptrnFA, name[0]) or re.match(ptrnDA, name[0])
		if m:
			boobs, belly, booty = \
				m.group('tag'), m.group('title'), m.group('artist')
			belly = re.compile(r'_(s|t|re|m)_').sub(r"'\1_", belly)
			belly = re.compile(r'_{2,}').sub(r'_', belly)
			booty = booty.replace('_', '-')

			pre = m.group('pre')
			if pre:
				for bust in re.findall(r'\d{10}[\._-]([\.\~0-9A-Za-z-]+)', pre):
					booty += '_' + bust
			pump = f'{booty}_{belly}.{boobs}'

		if prepend or not b.isloc or not name[1]:
			if not pump: pump = name[0]
			pump = prepend + pump

		if pump:
			b.blimps.append(Blimp(split[0], name[0], name[1], pump))

def pumper():
	for x in b.blimps:
		try:
			if (x.dup or x.xst) and not prepend:
				system(f'kioclient5 move "{x.full}" trash:/')
			else:
				rename(x.full, x.plump())
		except Exception as e: print(f'{x.full}: {e}')

def fromBlimps(blimps):
	for blimp in blimps:
		yield blimp.full


class RenameWindow(BlimpWindow):
	def __init__(self):
		self.act = 'Rename'
		idx = 2
		model = Gtk.ListStore(str, str, object)
		model.set_sort_func(0, b.comparepump, idx)
		model.set_sort_func(1, b.comparedate, idx)
		model.set_sort_column_id(1, Gtk.SortType.ASCENDING)
		model.cols = ['Name', 'Date']
		self.model = model
		self.idx = idx
		self.wid = 7
		super().__init__()

		# set up the layout
		grid = self.grid
		butns = self.butns
		scroll = Gtk.ScrolledWindow()
		scroll.set_vexpand(True)
		label = Gtk.Label(label='Prepend:')
		prepd = Gtk.Entry(text=prepend)
		chkloc = Gtk.CheckButton(label="Loc")
		chkloc.set_active(b.isloc)
		chkloc.connect("toggled", self.on_chkloc_toggled)
		grid.attach_next_to(scroll, self.count, Gtk.PositionType.BOTTOM, 8, 16)
		grid.attach_next_to(label   , scroll  , Gtk.PositionType.BOTTOM, 1, 1)
		grid.attach_next_to(prepd   , label   , Gtk.PositionType.RIGHT , 3, 1)
		grid.attach_next_to(chkloc  , prepd   , Gtk.PositionType.RIGHT , 1, 1)
		grid.attach_next_to(butns[0], chkloc  , Gtk.PositionType.RIGHT , 1, 1)
		for i, butn in enumerate(butns[1:]):
			grid.attach_next_to(butn , butns[i], Gtk.PositionType.RIGHT , 1, 1)
		scroll.add(self.view)

		self.fillerup()
		self.prepd = prepd

	def fillerup(self):
		for x in b.blimps:
			name = x.name + x.ext + '\n' + x.pump + ('*' if x.chx else '') \
			+ ('\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+' if x.dup or x.xst else '')
			self.model.append([
				 name
				,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x.date))
				,x
			])
		super().fillerup()

	def on_rescan_clicked(self, button):
		global prepend
		prepend = self.prepd.get_text()
		b.ogle(ogler)
		super().on_rescan_clicked(button)

	def on_commit_clicked(self, button):
		if super().on_commit_clicked(button) == Gtk.ResponseType.YES:
			pumper()
			self.destroy()

	def on_chkloc_toggled(self, chk):
		b.isloc = chk.get_active()
		if not b.isloc:
			b.files = list(fromBlimps(b.blimps))
#end RenameWindow


prepend = b.handle_args()
b.ogle(ogler)

win = RenameWindow()
win.show_all()
Gtk.main()
