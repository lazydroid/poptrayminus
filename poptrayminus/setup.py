#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup

setup(
	name = 'poptrayminus',
	version = '1.4.0',
	description = 'POP3 mailbox monitor with tray icon notifications',
	long_description = 'PopTray Minus checks POP3 mailbox, filters spam and shows message header previews.',
	author = 'Lenik Terenin',
	author_email = 'lenik@lazydroid.com',
	license = "GPL",
	url = 'http://lazydroid.com/poptrayminus/',
	data_files = [
		('share/poptrayminus', [
			'poptrayminus.png'
			]),
		('share/pixmaps', ['poptrayminus.png']),
		('share/applications', ['poptrayminus.desktop']),
	],
	scripts = ["poptrayminus"],
	keywords = "pop3 linux ubuntu mailbox spam tray",
)
