#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# poplib returns bytes on python3, while the message maps and the ui use str

import poplib

import pytest

from conftest import make_account


class FakePOP3 :
	# the handful of poplib calls Mailbox makes, answering in bytes like poplib does

	def __init__( self, messages ) :
		self.messages = messages		# { num: (uidl, raw_message) }
		self.deleted = []

	def uidl( self ) :
		lines = [ ('%d %s' % (n, u)).encode() for n, (u, _) in sorted( self.messages.items() ) ]
		return ( b'+OK', lines, sum( len(i) for i in lines ) )

	def list( self, num ) :
		return b'+OK %d %d' % ( num, len(self.messages[num][1]) )

	def top( self, num, lines ) :
		raw = self.messages[int(num)][1]
		body = raw.split( b'\n\n', 1 )[1] if lines else b''
		head = raw.split( b'\n\n', 1 )[0]
		out = head.split( b'\n' ) + ( body.split( b'\n' ) if lines else [] )
		return ( b'+OK', out, sum( len(i) for i in out ) )

	def dele( self, num ) :
		self.deleted.append( int(num) )

	def stat( self ) :
		return ( len(self.messages), 1024 )

	def quit( self ) :
		pass


MESSAGE = b'From: friend@example.com\nTo: me@example.com\nSubject: hi\nDate: Thu, 1 Jan 2015 12:00:00 +0000\nX-Spam-Score: -20\n\nhello there\n'


@pytest.fixture
def globals_stub( ptm, monkeypatch ) :
	# tray / app are only bound by the __main__ block
	monkeypatch.setattr( ptm, 'tray', type( 'tray', (), { 'setToolTip': staticmethod( lambda tip : None ) } ), raising = False )
	monkeypatch.setattr( ptm, 'app', type( 'app', (), { 'processEvents': staticmethod( lambda : None ) } ), raising = False )


@pytest.fixture
def mbox( ptm ) :
	return FakePOP3( { 1: ('UID0001', MESSAGE), 2: ('UID0002', MESSAGE) } )


def test_check_error_accepts_bytes( ptm ) :
	ptm.Mailbox( make_account() ).check_error( [b'+OK 2 messages'] )


def test_check_error_raises_on_bytes_err( ptm ) :
	with pytest.raises( poplib.error_proto ) :
		ptm.Mailbox( make_account() ).check_error( [b'-ERR nope'] )


def test_get_uidl_decodes_lines( ptm, mbox ) :
	assert ptm.Mailbox( make_account() ).get_uidl( mbox ) == ['1 UID0001', '2 UID0002']


def test_get_message_returns_text( ptm, mbox, monkeypatch ) :
	mb = ptm.Mailbox( make_account() )
	monkeypatch.setattr( mb, 'open_mbox', lambda : mbox )

	text = mb.get_message( 'UID0002' )

	assert 'Subject: hi' in text
	assert 'hello there' in text


def test_rescan_keys_messages_by_uidl( ptm, mbox, monkeypatch, globals_stub ) :
	mb = ptm.Mailbox( make_account() )
	monkeypatch.setattr( mb, 'open_mbox', lambda : mbox )

	mb.rescan()

	assert sorted( mb.messages ) == ['UID0001', 'UID0002']
	msg = mb.messages['UID0002']
	assert msg[1] == 'friend@example.com'
	assert msg[3] == '2015-01-01 12:00:00'
	assert msg[4].endswith( 'k ' )


def test_rescan_deletes_killed_message( ptm, mbox, monkeypatch, globals_stub ) :
	mb = ptm.Mailbox( make_account() )
	monkeypatch.setattr( mb, 'open_mbox', lambda : mbox )

	mb.rescan()
	mb.killed = { 'UID0002' }
	mb.rescan()

	assert mbox.deleted == [2]
	assert sorted( mb.messages ) == ['UID0001']


def test_strip_err_handles_bytes_and_plain_text( ptm, qapp ) :
	assert ptm.MainForm.strip_err( None, b'-ERR no such message' ) == 'no such message'
	assert ptm.MainForm.strip_err( None, 'connection refused' ) == 'connection refused'
