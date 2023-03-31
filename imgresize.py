#!/usr/bin/env python3

import time
from os import path, rename, system

import blimbo as b
from blimbo import Blimp, BlimpWindow, Image, Gtk


percent = ''
wide = 1.75
minsize = 1.33


def ogler(files):
	for x in files:
		split = path.split(x)
		name = path.splitext(split[1])
		size = path.getsize(x) / 1024000
		types = ['.png', '.jpg', '.jpeg']
		if size >= minsize and (name[1] in types) or not b.isloc:
			try:
				with Image.open(x) as img:
					width, height = img.size
					asp = width / height
					if percent:
						pct = float(percent) / 100
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
					if pct < 0.999 or name[1] != '.jpg':
						pump = {'size':size, 'pct':pct, 'asp':asp}
						b.blimps.append(Blimp(split[0], name[0], name[1], pump))
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
					rename(full, old)
					full = old

				(width, height) = (int(img.width * x.pct), int(img.height * x.pct))
				img = img.resize((width, height)).convert('RGB')
				img.save(f'{x.loc}/{x.name}.jpg')
			system(f'kioclient5 move "{full}" trash:/')
		except Exception as e:
			print(f'{full}: {e}')


class ResizeWindow(BlimpWindow):
	def __init__(self):
		self.act = 'Resize'
		idx = 4
		model = Gtk.ListStore(str, str, str, str, object)
		model.set_sort_func(0, b.comparename, idx)
		model.set_sort_func(1, b.comparesize, idx)
		model.set_sort_func(2, b.compareext , idx)
		model.set_sort_func(3, b.comparedate, idx)
		model.set_sort_column_id(3, Gtk.SortType.ASCENDING)
		model.cols = ['Name', 'Size', 'Ext', 'Date']
		self.model = model
		self.idx = idx
		self.wid = 8
		super().__init__()

		# set up the layout
		grid = self.grid
		butns = self.butns
		scroll = Gtk.ScrolledWindow()
		scroll.set_vexpand(True)
		lblpct = Gtk.Label(label='Percent:')
		prcnt = Gtk.Entry(text=percent)
		lblsiz = Gtk.Label(label='Size (MB):')
		msize = Gtk.Entry(text=minsize)
		grid.attach_next_to(scroll, self.count, Gtk.PositionType.BOTTOM, 9, 16)
		grid.attach_next_to(lblpct  , scroll  , Gtk.PositionType.BOTTOM, 1, 1)
		grid.attach_next_to(prcnt   , lblpct  , Gtk.PositionType.RIGHT , 2, 1)
		grid.attach_next_to(lblsiz  , prcnt   , Gtk.PositionType.RIGHT , 1, 1)
		grid.attach_next_to(msize   , lblsiz  , Gtk.PositionType.RIGHT , 2, 1)
		grid.attach_next_to(butns[0], msize   , Gtk.PositionType.RIGHT , 1, 1)
		for i, butn in enumerate(butns[1:]):
			grid.attach_next_to(butn , butns[i], Gtk.PositionType.RIGHT , 1, 1)
		scroll.add(self.view)

		self.fillerup()
		self.prcnt = prcnt
		self.msize = msize

	def fillerup(self):
		tall = 1/wide
		for x in b.blimps:
			dscrp = ''
			if x.asp <= tall: dscrp = ' (Tall Portrait)'
			elif x.asp >= wide: dscrp = ' (Wide Landscape)'
			self.model.append([
				 f'{x.name}{x.ext}\n{x.pct*100:.2f}%, {x.asp:.2f}{dscrp}'
				,x.size
				,x.ext
				,time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(x.date))
				,x
			])
		super().fillerup()

	def on_rescan_clicked(self, button):
		global percent, minsize
		percent = self.prcnt.get_text()
		minsize = float(self.msize.get_text())
		b.ogle(ogler)
		super().on_rescan_clicked(button)

	def on_commit_clicked(self, button):
		if super().on_commit_clicked(button) == Gtk.ResponseType.YES:
			pumper()
			self.destroy()
#end ResizeWindow


percent = b.handle_args()
b.ogle(ogler)

ResizeWindow().show_all()
Gtk.main()
