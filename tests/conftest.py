#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import importlib.util
import os
import sys
from importlib.machinery import SourceFileLoader

import pytest

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

SCRIPT = os.path.join( os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'poptrayminus', 'poptrayminus' )


def _load_script() :
	# the application is an extension-less script, so it needs an explicit loader
	loader = SourceFileLoader( 'ptm', SCRIPT )
	spec = importlib.util.spec_from_loader( loader.name, loader )
	module = importlib.util.module_from_spec( spec )
	sys.modules[loader.name] = module
	loader.exec_module( module )
	module.debug = False		# only set by the __main__ block
	return module


@pytest.fixture( scope='session' )
def ptm() :
	return _load_script()


@pytest.fixture( scope='session' )
def qapp( ptm ) :
	app = ptm.QtWidgets.QApplication.instance() or ptm.QtWidgets.QApplication( [] )
	ptm.app = app
	return app


@pytest.fixture
def globals_stub( ptm, monkeypatch ) :
	# tray / app are only bound by the __main__ block
	monkeypatch.setattr( ptm, 'tray', type( 'tray', (), { 'setToolTip': staticmethod( lambda tip : None ) } ), raising = False )
	monkeypatch.setattr( ptm, 'app', type( 'app', (), { 'processEvents': staticmethod( lambda : None ) } ), raising = False )


@pytest.fixture( autouse = True )
def cache_home( monkeypatch, tmp_path ) :
	# keep the message cache out of the real ~/.cache
	monkeypatch.setenv( 'XDG_CACHE_HOME', str(tmp_path / 'cache') )
	return tmp_path / 'cache' / 'poptrayminus'


@pytest.fixture
def config( ptm, tmp_path ) :
	# QSettings backed by a throwaway ini file, installed as the module-level global
	settings = ptm.QtCore.QSettings( str(tmp_path / 'poptrayrc'), ptm.QtCore.QSettings.IniFormat )
	ptm.config = settings
	return settings


def make_account( **kwargs ) :
	account = {
		'name': '',
		'host': 'mail.example.com',
		'port': 110,
		'user': 'someone',
		'pass': 'secret',
		'interval': 15,
		'protocol': 'POP3',
		'black_from_contains': [],
		'black_to_contains': [],
	}
	account.update( kwargs )
	return account
