#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# regression tests for the Qt4 -> Qt5 widget API


def test_browser_form_builds( ptm, qapp ) :
	# used by both Preview and About; QVBoxLayout.setMargin() and
	# QtWidgets.QKeySequence are Qt4-only and used to blow the app up here
	form = ptm.BrowserForm( None, 'PopTray - Preview', 'hello there' )
	assert form.windowTitle() == 'PopTray - Preview'
	assert form.layout().contentsMargins().left() == 0
	assert form.findChild( ptm.QtWidgets.QTextBrowser ).toPlainText() == 'hello there'


def test_item_user_role_round_trips_uidl( ptm, qapp ) :
	# message ids are the raw UIDL values (bytes) and are looked up in
	# Mailbox.messages / Mailbox.killed, so they must come back unchanged
	tree = ptm.QtWidgets.QTreeWidget()
	item = ptm.SortedTreeWidgetItem( tree, ['0.0', 'from', 'to', 'date', 'size', 'subj'] )
	item.setData( 1, ptm.QtCore.Qt.UserRole, b'UID0002' )
	assert item.data( 1, ptm.QtCore.Qt.UserRole ) == b'UID0002'


def test_sorted_item_sorts_scores_numerically( ptm, qapp ) :
	tree = ptm.QtWidgets.QTreeWidget()
	tree.setColumnCount( 6 )
	low = ptm.SortedTreeWidgetItem( tree, ['  2.0', 'a', 'b', 'c', '1.0 k ', 'd'] )
	high = ptm.SortedTreeWidgetItem( tree, [' 10.0', 'a', 'b', 'c', '2.0 k ', 'd'] )
	tree.sortItems( 0, ptm.QtCore.Qt.AscendingOrder )
	assert low < high		# lexically '10.0' would come first
