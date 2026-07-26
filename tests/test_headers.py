#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from conftest import make_account


def mailbox( ptm ) :
	return ptm.Mailbox( make_account() )


def test_decode_stuff_plain( ptm ) :
	assert mailbox( ptm ).decode_stuff( 'hello there' ) == 'hello there'


def test_decode_stuff_none( ptm ) :
	assert mailbox( ptm ).decode_stuff( None ) == ''


def test_decode_stuff_base64( ptm ) :
	assert mailbox( ptm ).decode_stuff(
		'=?utf-8?B?0L/RgNC40LLQtdGC?='
	) == 'привет'


def test_decode_stuff_quoted_printable( ptm ) :
	assert mailbox( ptm ).decode_stuff(
		'=?iso-8859-1?Q?caf=E9?='
	) == 'café'


def test_decode_stuff_mixed_words( ptm ) :
	assert mailbox( ptm ).decode_stuff(
		'Re: =?utf-8?B?0L/RgNC40LLQtdGC?='
	) == 'Re: привет'		# the spacing of the unencoded word is kept as is


def test_decode_stuff_unknown_charset( ptm ) :
	# a bogus charset must not blow up, the bytes are read as utf-8
	assert mailbox( ptm ).decode_stuff( '=?nosuch?B?aGk=?=' ) == 'hi'


def test_decode_stuff_bytes( ptm ) :
	assert mailbox( ptm ).decode_stuff( b'=?utf-8?B?aGk=?=' ) == 'hi'


def test_hide_passwords( ptm ) :
	accounts = [ make_account( ) ]
	assert ptm.hide_passwords( accounts )[0]['pass'] == '***'
	assert accounts[0]['pass'] == 'secret'		# the original is left alone
	assert ptm.hide_passwords( accounts )[0]['host'] == 'mail.example.com'


def test_debug_defaults_to_off( ptm ) :
	assert ptm.debug is False
