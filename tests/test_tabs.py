#!/usr/bin/env python3
# -*- coding: utf-8 -*-


def write_accounts( ptm, config, hosts ) :
	config.clear()
	for i, host in enumerate( hosts ) :
		config.beginGroup( 'account%d' % i )
		config.setValue( 'host', host )
		config.setValue( 'user', 'someone' )
		config.endGroup()
	config.sync()


def test_setup_tabs_removes_the_dropped_accounts( ptm, qapp, config ) :
	write_accounts( ptm, config, [ 'one.example.com', 'two.example.com', 'three.example.com' ] )

	form = ptm.MainForm()
	assert form.tab_widget.count() == 3

	write_accounts( ptm, config, [ 'one.example.com' ] )
	form.setup_tabs()

	# the survivor must be the first tab, not whatever the shifting indexes left behind
	assert form.tab_widget.count() == 1
	assert len( form.tables ) == 1
	assert form.tab_widget.tabText( 0 ) == 'someone@one.example.com'


def test_setup_tabs_renames_kept_accounts( ptm, qapp, config ) :
	write_accounts( ptm, config, [ 'one.example.com', 'two.example.com' ] )
	form = ptm.MainForm()

	config.beginGroup( 'account0' )
	config.setValue( 'name', 'work' )
	config.endGroup()
	form.setup_tabs()

	assert form.tab_widget.count() == 2
	assert form.tab_widget.tabText( 0 ) == 'work'
