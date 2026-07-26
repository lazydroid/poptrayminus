#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import poplib

import pytest

from conftest import make_account


def test_title_prefers_name( ptm ) :
	mb = ptm.Mailbox( make_account( name = 'work' ) )
	assert mb.title() == 'work'


def test_title_uses_user_with_domain( ptm ) :
	mb = ptm.Mailbox( make_account( user = 'someone@example.com' ) )
	assert mb.title() == 'someone@example.com'


def test_title_joins_user_and_host( ptm ) :
	mb = ptm.Mailbox( make_account() )
	assert mb.title() == 'someone@mail.example.com'


@pytest.mark.parametrize( 'msg_from, msg_to, expected', [
	( 'spammer@example.com', 'me@example.com', True ),
	( 'SPAMMER@EXAMPLE.COM', 'me@example.com', True ),		# case insensitive
	( 'friend@example.com', 'VICTIM@example.com', True ),		# matches "to" list
	( 'friend@example.com', 'me@example.com', False ),
] )
def test_is_blacklisted( ptm, msg_from, msg_to, expected ) :
	mb = ptm.Mailbox( make_account(
		black_from_contains = ['spammer@'],
		black_to_contains = ['victim@'],
	) )
	assert mb.is_blacklisted( msg_from, msg_to, 'hello' ) is expected


def test_check_error_accepts_ok( ptm ) :
	ptm.Mailbox( make_account() ).check_error( ['+OK 2 messages'] )


def test_check_error_raises_on_err( ptm ) :
	with pytest.raises( poplib.error_proto ) :
		ptm.Mailbox( make_account() ).check_error( ['-ERR no such message'] )


def test_decode_stuff_handles_missing_header( ptm ) :
	mb = ptm.Mailbox( make_account() )
	assert mb.decode_stuff( None ) == ''
	assert mb.decode_stuff( 'Subject' ) == 'Subject'


@pytest.mark.parametrize( 'raw, expected', [
	( 'already text', 'already text' ),
	( None, '' ),
	( b'plain ascii', 'plain ascii' ),
	( 'привет'.encode('utf-8'), 'привет' ),
] )
def test_convert_to_unicode( ptm, raw, expected ) :
	assert ptm.Mailbox( make_account() ).convert_to_unicode( raw ) == expected


def test_strip_err( ptm, qapp ) :
	assert ptm.MainForm.strip_err( None, '-ERR no such message' ) == 'no such message'
