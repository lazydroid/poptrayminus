#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# per account enable/disable, the connection test and the port field

import poplib

import pytest

from dummy_pop3 import serve
from test_protocol import FakePOP3, make_message


@pytest.fixture
def server( tmp_path ) :
	srv = serve( str(tmp_path / 'pop3') )
	yield srv
	srv.shutdown()


def page( ptm, qapp, config, **fields ) :
	pp = ptm.ConfigPage()
	pp.server_edit.setText( fields.get( 'host', '127.0.0.1' ) )
	pp.port_edit.setText( str( fields.get( 'port', 110 ) ) )
	pp.user_edit.setText( fields.get( 'user', 'tester@example.com' ) )
	pp.pass_edit.setText( fields.get( 'passwd', 'secret' ) )
	return pp


def test_valid_port( ptm ) :
	assert ptm.valid_port( '110' ) and ptm.valid_port( 65535 )
	assert not ptm.valid_port( '' )
	assert not ptm.valid_port( 'abc' )
	assert not ptm.valid_port( '0' )
	assert not ptm.valid_port( '65536' )
	assert not ptm.valid_port( '-1' )


def test_is_enabled( ptm ) :
	assert ptm.is_enabled( 'true' ) and ptm.is_enabled( True ) and ptm.is_enabled( '1' )
	assert not ptm.is_enabled( 'false' )
	assert not ptm.is_enabled( 'False' )
	assert not ptm.is_enabled( '0' )
	assert not ptm.is_enabled( False )


def test_bad_port_is_marked_while_typing( ptm, qapp, config ) :
	pp = page( ptm, qapp, config )
	assert pp.port_edit.styleSheet() == ''

	pp.port_edit.setText( '99999' )		# the validator keeps letters out, not the range
	assert 'background' in pp.port_edit.styleSheet()

	pp.port_edit.setText( '995' )
	assert pp.port_edit.styleSheet() == ''


def test_bad_port_is_rejected_on_ok( ptm, qapp, config ) :
	pp = page( ptm, qapp, config, port = '0' )
	with pytest.raises( Exception, match = 'between 1 and 65535' ) :
		pp.validate_data()


def save_account( ptm, qapp, config, **fields ) :
	config.beginGroup( 'account0' )
	pp = page( ptm, qapp, config, **fields )
	if 'enabled' in fields :
		pp.enabled_check.setChecked( fields['enabled'] )
	pp.save_data()
	config.endGroup()
	ptm.load_settings()
	return pp


def test_accounts_are_enabled_by_default( ptm, qapp, config ) :
	pp = save_account( ptm, qapp, config )
	assert pp.enabled_check.isChecked()
	assert ptm.settings[0]['enabled'] is True


def test_disabled_account_round_trips( ptm, qapp, config ) :
	save_account( ptm, qapp, config, enabled = False )

	assert ptm.settings[0]['enabled'] is False

	config.beginGroup( 'account0' )		# and the dialog shows it unticked next time
	assert ptm.ConfigPage().enabled_check.isChecked() is False
	config.endGroup()


def test_disabled_account_is_not_polled( ptm, qapp, config, monkeypatch ) :
	save_account( ptm, qapp, config )

	form = ptm.MainForm()
	monkeypatch.setattr( ptm, 'tray', ptm.nullTray(), raising = False )
	monkeypatch.setattr( ptm, 'form', form, raising = False )

	scanned = []
	monkeypatch.setattr( form.mailboxen[0], 'rescan', lambda : scanned.append( 1 ) )

	form.reload( form.mailboxen[0] )
	assert scanned == [1]

	form.mailboxen[0].account['enabled'] = False
	form.reload( form.mailboxen[0] )
	assert scanned == [1]			# left alone, and no error reported


def test_disabled_account_keeps_its_messages_and_says_so( ptm, qapp, config, monkeypatch ) :
	save_account( ptm, qapp, config )

	form = ptm.MainForm()
	monkeypatch.setattr( ptm, 'tray', ptm.nullTray(), raising = False )
	monkeypatch.setattr( ptm, 'form', form, raising = False )
	monkeypatch.setattr( form.mailboxen[0], 'rescan', lambda : None )

	mb = form.mailboxen[0]
	mb.messages = { 'UID0001': ['0.0', 'a@b.c', 'd@e.f', 'date', '1 k', 'subj'] }
	mb.account['enabled'] = False
	form.reload( mb )

	assert form.tab_widget.tabText( 0 ).startswith( '(' )
	assert form.tab_widget.tabText( 0 ).endswith( '- 1' )
	assert form.tables[0].topLevelItemCount() == 1


def test_auto_reload_skips_disabled_accounts( ptm, qapp, config, monkeypatch ) :
	save_account( ptm, qapp, config )

	form = ptm.MainForm()
	monkeypatch.setattr( ptm, 'tray', ptm.nullTray(), raising = False )
	monkeypatch.setattr( ptm, 'form', form, raising = False )

	reloaded = []
	monkeypatch.setattr( form, 'reload', lambda mb : reloaded.append( mb ) )
	form.mailboxen[0].elapsed = 999

	form.auto_reload()
	assert len(reloaded) == 1

	save_account( ptm, qapp, config, enabled = False )	# auto_reload re-reads the settings
	form.mailboxen[0].elapsed = 999
	form.auto_reload()
	assert len(reloaded) == 1


def test_connection_test_reports_the_mailbox( ptm, qapp, config, server ) :
	pp = page( ptm, qapp, config, port = server.server_address[1] )

	text = pp.try_connection()

	assert 'Connected to 127.0.0.1 as tester@example.com' in text
	assert '5 messages' in text
	assert 'QUIT' in server.store.commands()	# and it hung up politely


def test_connection_test_reports_a_refusal( ptm, qapp, config, server ) :
	port = server.server_address[1]
	server.shutdown()
	server.server_close()
	pp = page( ptm, qapp, config, port = port )

	with pytest.raises( OSError ) :
		pp.try_connection()


def test_connection_test_reports_a_login_failure( ptm, qapp, config, monkeypatch ) :
	pp = page( ptm, qapp, config )

	class Rejecting( FakePOP3 ) :
		def user( self, name ) :
			pass

		def pass_( self, passwd ) :
			raise poplib.error_proto( b'-ERR authentication failed' )

	monkeypatch.setattr( ptm.poplib, 'POP3', lambda host, port, timeout : Rejecting( {} ) )

	with pytest.raises( poplib.error_proto ) :
		pp.try_connection()


def test_connection_test_refuses_a_bad_port( ptm, qapp, config ) :
	pp = page( ptm, qapp, config, port = '0' )

	with pytest.raises( Exception, match = 'between 1 and 65535' ) :
		pp.try_connection()


def test_connection_test_uses_ssl_for_pop3_ssl( ptm, qapp, config, monkeypatch ) :
	pp = page( ptm, qapp, config )
	pp.mailbox_combo.setCurrentIndex( 1 )		# switches the port to 995 as well

	used = []
	monkeypatch.setattr( ptm.poplib, 'POP3_SSL',
		lambda host, port, timeout : used.append( port ) or FakePOP3( { 1: ('UID0001', make_message()) } ) )

	pp.try_connection()
	assert used == [995]
