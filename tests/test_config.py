#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# regression tests for the Qt4 -> Qt5 settings API (QSettings.value() no
# longer returns a QVariant, so values must be usable as plain python objects)

import base64


def test_load_save_config_list( ptm, config ) :
	patterns = ['spammer@example.com', 'another-spammer']
	ptm.saveConfigList( 'black_from_contains', patterns )
	assert ptm.loadConfigList( 'black_from_contains' ) == patterns


def test_load_settings_reads_account( ptm, config ) :
	config.beginGroup( 'account0' )
	config.setValue( 'name', 'work' )
	config.setValue( 'host', 'mail.example.com' )
	config.setValue( 'port', 995 )
	config.setValue( 'user', 'someone' )
	config.setValue( 'passwd', base64.b64encode( b'secret' ).decode('ascii') )
	config.setValue( 'interval', 30 )
	config.setValue( 'protocol', 'POP3 SSL' )
	ptm.saveConfigList( 'black_from_contains', ['spammer'] )
	config.endGroup()

	ptm.load_settings()

	assert ptm.settings == [{
		'name': 'work',
		'host': 'mail.example.com',
		'port': 995,
		'user': 'someone',
		'pass': 'secret',
		'interval': 30,
		'protocol': 'POP3 SSL',
		'enabled': True,
		'black_from_contains': ['spammer'],
		'black_to_contains': [],
	}]


def test_load_settings_applies_defaults( ptm, config ) :
	config.beginGroup( 'account0' )
	config.setValue( 'host', 'mail.example.com' )
	config.endGroup()

	ptm.load_settings()

	acc = ptm.settings[0]
	assert acc['port'] == 110
	assert acc['interval'] == 15
	assert acc['protocol'] == 'POP3'
	assert acc['pass'] == ''		# nothing stored, b64decode fails


def test_load_settings_migrates_plaintext_password( ptm, config ) :
	config.beginGroup( 'account0' )
	config.setValue( 'host', 'mail.example.com' )
	config.setValue( 'pass', 'secret' )
	config.endGroup()

	ptm.load_settings()

	assert ptm.settings[0]['pass'] == 'secret'
	assert not config.contains( 'account0/pass' )
	assert str(config.value( 'account0/passwd' )) == base64.b64encode( b'secret' ).decode('ascii')


def test_fix_config_moves_toplevel_keys_into_account0( ptm, config ) :
	config.setValue( 'host', 'mail.example.com' )
	config.setValue( 'user', 'someone' )
	config.setValue( 'interval', 20 )

	ptm.fixConfig()

	assert not config.contains( 'host' )
	assert str(config.value( 'account0/host' )) == 'mail.example.com'
	assert str(config.value( 'account0/user' )) == 'someone'
	assert int(config.value( 'account0/interval' )) == 20


def test_config_page_populates_from_settings( ptm, qapp, config ) :
	config.beginGroup( 'account0' )
	config.setValue( 'name', 'work' )
	config.setValue( 'host', 'mail.example.com' )
	config.setValue( 'port', '995' )
	config.setValue( 'user', 'someone' )
	config.setValue( 'interval', 30 )
	config.setValue( 'protocol', 'POP3 SSL' )
	ptm.saveConfigList( 'black_to_contains', ['victim@example.com'] )

	page = ptm.ConfigPage()

	assert page.name_edit.text() == 'work'
	assert page.server_edit.text() == 'mail.example.com'
	assert page.port_edit.text() == '995'
	assert page.user_edit.text() == 'someone'
	assert page.interval_combo.currentText() == '30 min'
	assert page.mailbox_combo.currentIndex() == 1		# POP3 SSL
	assert page.black_to.toPlainText() == 'victim@example.com'
	assert page.title() == 'work'

	config.endGroup()


def test_config_page_defaults_on_empty_config( ptm, qapp, config ) :
	page = ptm.ConfigPage()

	assert page.port_edit.text() == '110'
	assert page.mailbox_combo.currentIndex() == 0		# POP3
	assert page.title() == '<empty>'


def test_config_page_protocol_change_updates_port( ptm, qapp, config ) :
	page = ptm.ConfigPage()

	page.mailbox_combo.setCurrentIndex( 1 )		# currentIndexChanged -> onMailbox
	assert page.port_edit.text() == '995'

	page.mailbox_combo.setCurrentIndex( 0 )
	assert page.port_edit.text() == '110'


def test_config_page_save_data_round_trip( ptm, qapp, config ) :
	page = ptm.ConfigPage()
	page.name_edit.setText( 'work' )
	page.server_edit.setText( 'mail.example.com' )
	page.user_edit.setText( 'someone' )
	page.pass_edit.setText( 'sécret' )
	page.mailbox_combo.setCurrentIndex( 1 )
	page.interval_combo.setCurrentIndex( 4 )		# 30 min
	page.black_from.setPlainText( 'spammer@example.com' )

	config.beginGroup( 'account0' )
	page.save_data()
	config.endGroup()

	ptm.load_settings()
	acc = ptm.settings[0]
	assert acc['name'] == 'work'
	assert acc['host'] == 'mail.example.com'
	assert acc['port'] == 995
	assert acc['user'] == 'someone'
	assert acc['pass'] == 'sécret'
	assert acc['interval'] == 30
	assert acc['protocol'] == 'POP3 SSL'
	assert acc['black_from_contains'] == ['spammer@example.com']

	config.beginGroup( 'account0' )
	assert ptm.ConfigPage().pass_edit.text() == 'sécret'
	config.endGroup()
