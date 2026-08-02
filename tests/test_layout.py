#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# window geometry, column widths and sort order kept between runs, and the
# notification landing on the mailbox it is about

from test_settings_ux import save_account


def test_defaults_when_nothing_was_saved( ptm, qapp, config ) :
	save_account( ptm, qapp, config )

	form = ptm.MainForm()

	assert form.saved_geometry is None
	assert form.columns == []
	assert ( form.sort_column, form.sort_order ) == ( 3, ptm.QtCore.Qt.DescendingOrder )
	# the old rule of thumb, a quarter of the window each for From and To
	table = form.tables[0]
	assert table.columnWidth( 1 ) == table.columnWidth( 2 ) > 0


def test_layout_round_trips( ptm, qapp, config ) :
	save_account( ptm, qapp, config )

	form = ptm.MainForm()
	form.resize( 640, 480 )
	form.tables[0].setColumnWidth( 1, 123 )
	form.tables[0].sortByColumn( 5, ptm.QtCore.Qt.AscendingOrder )
	form.save_layout()

	later = ptm.MainForm()

	assert later.columns[1] == 123
	assert ( later.sort_column, later.sort_order ) == ( 5, ptm.QtCore.Qt.AscendingOrder )
	assert later.tables[0].columnWidth( 1 ) == 123
	assert later.tables[0].header().sortIndicatorSection() == 5
	assert ( later.size().width(), later.size().height() ) == ( 640, 480 )


def test_the_layout_group_is_not_taken_for_an_account( ptm, qapp, config ) :
	# load_settings() walks account0..N by counting the groups in the config
	save_account( ptm, qapp, config )
	ptm.MainForm().save_layout()

	assert 'layout' in config.childGroups()
	assert ptm.account_count() == 1

	ptm.load_settings()
	assert len( ptm.settings ) == 1


def test_a_hand_mangled_layout_is_ignored( ptm, qapp, config ) :
	save_account( ptm, qapp, config )
	config.setValue( 'layout/columns', [ 'wide', 'wider' ] )
	config.setValue( 'layout/sort_column', '5' )

	form = ptm.MainForm()

	assert form.columns == []
	assert form.sort_column == 5


def test_closing_the_window_saves_the_layout( ptm, qapp, config, monkeypatch ) :
	save_account( ptm, qapp, config )

	form = ptm.MainForm()
	form.tables[0].setColumnWidth( 2, 222 )
	form.close()

	assert ptm.MainForm().columns[2] == 222


def test_notification_click_opens_the_mailbox_it_is_about( ptm, qapp, config, monkeypatch ) :
	save_account( ptm, qapp, config )
	config.beginGroup( 'account1' )
	config.setValue( 'host', 'other.example.com' )
	config.setValue( 'user', 'someone-else' )
	config.endGroup()
	ptm.load_settings()

	form = ptm.MainForm()
	monkeypatch.setattr( ptm, 'form', form, raising = False )
	assert form.tab_widget.currentIndex() == 0

	form.notified_tab = 1
	ptm.sysTray.onMessageClicked( None )

	assert form.tab_widget.currentIndex() == 1
	assert not form.isHidden()


def test_show_tab_ignores_a_tab_that_is_gone( ptm, qapp, config ) :
	save_account( ptm, qapp, config )

	form = ptm.MainForm()
	form.show_tab( 7 )		# the account it notified about has been deleted since

	assert form.tab_widget.currentIndex() == 0
