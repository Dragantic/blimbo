#!/usr/bin/env python3

import os, time
from sys import argv
from PIL import Image
from subprocess import Popen

import blimbo as b
from blimbo import Blimp, BlimpWindow, Gtk

percent = 0
wide = 1.75
minsize = 1.33

def ogler(files):
	for x in files:
		split = os.path.split(x)
		namext = os.path.splitext(split[1])
		loc, name, ext = split[0], namext[0], namext[1]
		size = os.path.getsize(x) / 1024000
		types = ['.png', '.jpg', '.jpeg']
		if size >= minsize and (ext in types) or not b.isloc:
			try:
				with Image.open(x) as img:
					width, height = img.size
					asp = width / height
					if percent:
						pct = percent / 100
					else:
						pct = 1
						swid = 1920
						shgt = 1080
						if width > height*wide:
							width /= (width / swid)
						elif height > width*wide:
							height /= (height / shgt)
							swid = 1280
						if height > shgt:
							pct = shgt / height
							width *= pct
						if width > swid:
							pct *= swid / width
					if pct < 0.999 or ext != '.jpg':
						blimp = Blimp(loc, name, ext)
						blimp.size = f'{size:.2f}MB'
						blimp.asp = asp
						blimp.pct = pct
						b.blimps.append(blimp)
			except Exception as e: print(f'{x}: {e}')
	b.blimps.sort(key=lambda x: x.date)

def pumper():
	for x in b.blimps:
		full = x.full
		try:
			# ext = x.ext + ('[0]' if x.ext == '.gif' else '')
			with Image.open(full) as img:
				if img.format == 'JPEG':
					old = f'{x.loc}/{x.name}_old{x.ext}'
					os.rename(full, old)
					full = old

				(width, height) = (int(img.width * x.pct), int(img.height * x.pct))
				img = img.resize((width, height)).convert('RGB')
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
		tall = 1/wide
		for x in b.blimps:
			dscrp = ''
			if x.asp <= tall: dscrp = ' (Tall Portrait)'
			elif x.asp >= wide: dscrp = ' (Wide Landscape)'
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

i, j = 1, len(argv) - 1
while i <= j:
	if os.path.exists(argv[i]):
		break
	elif i < j:
		if argv[i] == '-p':
			i += 1
			percent = float(argv[i])
		elif argv[i] == '-m':
			i += 1
			minsize = float(argv[i])
	i += 1
b.default_args(i)
b.ogle(ogler)

ResizeWindow().show_all()
Gtk.main()
