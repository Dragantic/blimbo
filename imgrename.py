#!/usr/bin/env python3

import os, re, time
from sys import argv
from PIL import Image
from subprocess import Popen

import blimbo as b
from blimbo import Blimp, BlimpWindow, Gtk

prepend = ''

ptrnFA = r'^(?P<pre>\d{7,}\..+[\._-])*(?P<tag>\d{7,})[\._]' \
	+ r'(?P<artist>[\.\~0-9A-Za-z-]+)_[_-]*' \
	+ r'(?P<title>(?:[_-]*(?!\.(?:png|jpe?g|gif|swf)$)' \
	+ r'(?:[\.\(\)\[\]\{\} 0-9A-Za-z+%!,]|[^\x00-\x80]))+)'

ptrnDA = r'^(?P<pre>)_*(?P<title>(?:[_-]*[\(\)0-9A-Za-z+!])+)' \
	+ r'_*_by_(?P<artist>(?:[_-]*[\(\)0-9A-Za-z+!])+)' \
	+ r'[~_-](?P<tag>[0-9A-Za-z]{7}(?![0-9A-Za-z]+)(?:-pre)?)$'

class Rename(Blimp):
	def __init__(self, loc:str, name:str, ext:str, pump:str):
		super().__init__(loc, name, ext)
		self.dup = bool(re.search(r'\([0-9]+\)$', name))
		bxt = ext
		try:
			with Image.open(self.full) as img:
				fmt = img.format
				bxt = '.' + str('JPG' if fmt == 'JPEG' else fmt).lower()
		except Exception as e:
			print(f'{self.full}: {e}')
		self.chx = (bxt != ext)
		self.exist = (name != pump and os.path.isfile(f'{loc}/{pump}{bxt}'))
		if self.exist:
			count = 1
			while os.path.isfile(f'{loc}/{pump} ({count}){bxt}'): count += 1
			pump += f'({count})'
		self.pump = pump + bxt

def ogler(files: list[str]):
	for x in files:
		split = os.path.split(x)
		namext = os.path.splitext(split[1])
		loc, name, ext = split[0], namext[0], namext[1]
		if name[0] == '.':
			continue
		pump = None
		m = re.match(ptrnFA, name) or re.match(ptrnDA, name)
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

		if prepend or not b.isloc or not ext:
			pump = prepend + (name if not pump else pump)

		if pump:
			b.blimps.append(Rename(loc, name, ext, pump))

def pumper():
	for x in b.blimps:
		if not isinstance(x, Rename):
			continue
		try:
			if (x.dup or x.exist) and not prepend:
				Popen(['kioclient5', 'move', x.full, 'trash:/']).wait()
			else:
				os.rename(x.full, f'{x.loc}/{x.pump}')
		except Exception as e: print(f'{x.full}: {e}')


class RenameWindow(BlimpWindow):
	def __init__(self):
		self.act = 'Rename'
		model = Gtk.ListStore(object, str, str)
		model.set_sort_func(1, b.comparepump, 0)
		model.set_sort_func(2, b.comparedate, 0)
		model.set_sort_column_id(2, Gtk.SortType.ASCENDING)
		model.cols = ['_', 'Name', 'Date']

		lbl_pre = Gtk.Label(label='Prepend:')
		txt_pre = Gtk.Entry(text=prepend)
		txt_pre.set_width_chars(5)
		lbl_pre.wid, txt_pre.wid = 1, 2
		widgets = [lbl_pre, txt_pre]
		super().__init__(model, widgets)
		self.txt_pre = txt_pre
		self.feed()

	def feed(self):
		for x in b.blimps:
			if not isinstance(x, Rename):
				continue
			name = f'{x.name}{x.ext}\n{x.pump}{"*" if x.chx else ""}' \
			+ ('\n+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+' if x.dup or x.exist else '')
			date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x.date))
			self.model.append([x, name, date])
		self.set_sensitives()

	def on_rescan_clicked(self, button):
		global prepend
		prepend = self.txt_pre.get_text()
		b.ogle(ogler)
		super().on_rescan_clicked(button)

	def on_commit_clicked(self, button):
		if super().on_commit_clicked(button) == Gtk.ResponseType.YES:
			pumper()
			self.destroy()
#end RenameWindow

i, j = 1, len(argv) - 1
while i <= j:
	if os.path.exists(argv[i]):
		break
	elif argv[i] == '-p' and i < j:
		i += 1
		prepend = argv[i]
	i += 1
b.default_args(i)
b.ogle(ogler)

RenameWindow().show_all()
Gtk.main()
