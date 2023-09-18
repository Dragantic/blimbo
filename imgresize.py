#!/usr/bin/env python3

import os, time
from sys import argv
from PIL import Image
from subprocess import Popen

import blimbo as b
from blimbo import Blimp, BlimpWindow, Gtk

percent = 0
minsize = 1.33 # megabytes
types = ['.png', '.jpg', '.jpeg']

aspect_wide = 7 / 4
aspect_tall = 4 / 7

max_width  = 2880
max_height = 1620
portrait_width   = 1600
landscape_height = 1350

class Resize(Blimp):
	def __init__(self, loc:str, name:str, ext:str, size:float, asp:float, pct:float):
		super().__init__(loc, name, ext)
		self.size = f'{size:.2f}MB'
		self.asp = asp
		self.pct = pct

def ogler(files: list[str]):
	for x in files:
		split = os.path.split(x)
		namext = os.path.splitext(split[1])
		loc, name, ext = split[0], namext[0], namext[1]
		size = os.path.getsize(x) / 1024000
		if size >= minsize and (ext in types) or not b.isloc:
			try:
				with Image.open(x) as img:
					width, height = img.size
					asp = width / height
					if percent:
						pct = percent / 100
					else:
						pct = 1.0
						max_w = max_width
						max_h = max_height

						# if wide or tall, constrain only the smaller dimension
						if asp >= aspect_wide:
							width = max_width # bypass the width constraint
							max_h = landscape_height
						elif asp <= aspect_tall:
							height = max_height # bypass the height constraint
							max_w = portrait_width

						if height > max_h:
							pct *= max_h / height
							width *= pct
						if width > max_w:
							pct *= max_w / width
					if pct < 0.999 or ext != '.jpg':
						b.blimps.append(Resize(loc, name, ext, size, asp, pct))
			except Exception as e: print(f'{x}: {e}')
	b.blimps.sort(key=lambda x: x.date)

def pumper():
	for x in b.blimps:
		if not isinstance(x, Resize):
			continue
		full = x.full
		try:
			# ext = x.ext + ('[0]' if x.ext == '.gif' else '')
			with Image.open(full) as img:
				fmt = img.format
				dimensions = (round(img.width * x.pct), round(img.height * x.pct))
				img = img.resize(dimensions).convert('RGB')
				if fmt == 'JPEG':
					new = f'{x.loc}/{x.name}_new.jpg'
					img.save(new)
					Popen(['kioclient5', 'move', full, 'trash:/']).wait()
					os.rename(new, full)
				else:
					img.save(f'{x.loc}/{x.name}.jpg')
					Popen(['kioclient5', 'move', full, 'trash:/']).wait()
		except Exception as e:
			print(f'{full}: {e}')


class ResizeWindow(BlimpWindow):
	def __init__(self):
		self.act = 'Resize'
		model = Gtk.ListStore(object, str, str, str, str)
		model.set_sort_func(1, b.comparename, 0)
		model.set_sort_func(2, b.comparesize, 0)
		model.set_sort_func(3, b.compareext , 0)
		model.set_sort_func(4, b.comparedate, 0)
		model.set_sort_column_id(4, Gtk.SortType.ASCENDING)
		model.cols = ['_', 'Name', 'Size', 'Ext', 'Date']

		lbl_pct = Gtk.Label(label='Percent:')
		txt_pct = Gtk.Entry(text=percent)
		txt_pct.set_width_chars(5)
		lbl_siz = Gtk.Label(label='Size (MB):')
		txt_siz = Gtk.Entry(text=minsize)
		txt_siz.set_width_chars(5)
		lbl_pct.wid, txt_pct.wid, lbl_siz.wid, txt_siz.wid = 1, 1, 1, 1
		widgets = [lbl_pct, txt_pct, lbl_siz, txt_siz]
		super().__init__(model, widgets)
		self.txt_pct = txt_pct
		self.txt_siz = txt_siz
		self.feed()

	def feed(self):
		for x in b.blimps:
			if not isinstance(x, Resize):
				continue
			dscrp = ''
			if   x.asp >= aspect_wide: dscrp = ' (Wide Landscape)'
			elif x.asp <= aspect_tall: dscrp = ' (Tall Portrait)'
			name = f'{x.name}{x.ext}\n{x.pct*100:.2f}%, {x.asp:.2f}{dscrp}'
			date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x.date))
			self.model.append([x, name, x.size, x.ext, date])
		self.set_sensitives()

	def on_rescan_clicked(self, button):
		global percent, minsize
		percent = float(self.txt_pct.get_text())
		minsize = float(self.txt_siz.get_text())
		b.ogle(ogler)
		super().on_rescan_clicked(button)

	def on_commit_clicked(self, button):
		if super().on_commit_clicked(button) == Gtk.ResponseType.YES:
			pumper()
			self.destroy()
#end ResizeWindow

def opt_percent(i: int) -> int:
	global percent ; percent = float(argv[i])
	return 1

def opt_minsize(i: int) -> int:
	global minsize ; minsize = float(argv[i])
	return 1

def opt_types(i: int) -> int:
	global types ; types = [f'.{x}' for x in argv[i].split(',')]
	return 1

b.opts['-p'] = opt_percent
b.opts['-m'] = opt_minsize
b.opts['-t'] = opt_types
b.read_args()
b.ogle(ogler)

ResizeWindow().show_all()
Gtk.main()
