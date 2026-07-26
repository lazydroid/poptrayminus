#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try :
	from setuptools import setup
except ImportError :	# setuptools is not there on very old boxes
	from distutils.core import setup

setup(
	name = 'poptrayminus',
	version = '1.5.0',
	description = 'POP3 mailbox monitor with tray icon notifications',
	long_description = 'PopTray Minus checks POP3 mailbox, filters spam and shows message header previews.',
	author = 'Lenik Terenin',
	author_email = 'lenik@lazydroid.com',
	license = "MIT",
	classifiers = [
		'License :: OSI Approved :: MIT License',
		'Programming Language :: Python :: 3',
		'Environment :: X11 Applications :: Qt',
		'Topic :: Communications :: Email :: Post-Office :: POP3',
	],
	python_requires = '>=3.4',
	install_requires = [ 'PyQt5', 'chardet' ],
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
