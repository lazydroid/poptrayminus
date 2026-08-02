#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# the message cache against a real socket, so poplib itself is in the loop

import pytest

from conftest import make_account
from dummy_pop3 import serve


@pytest.fixture
def server( tmp_path ) :
	srv = serve( str(tmp_path / 'pop3') )
	yield srv
	srv.shutdown()


def mailbox( ptm, server, **kwargs ) :
	return ptm.Mailbox( make_account(
		host = '127.0.0.1', port = server.server_address[1], user = 'tester@example.com', **kwargs
	) )


def topped( server ) :
	return [ c for c in server.store.commands() if c.startswith('TOP ') ]


def test_scan_then_restart_only_fetches_the_new_message( ptm, server, globals_stub ) :
	first = mailbox( ptm, server )
	first.rescan()
	assert len(first.messages) == 5
	assert len( topped( server ) ) == 5
	assert first.messages['UID0004'][5] == 'привет'		# decoded on the way in

	server.store.deliver_extra()
	server.store.forget_commands()

	second = mailbox( ptm, server )		# a fresh start, cache comes off disk
	second.rescan()

	assert topped( server ) == ['TOP 6 0']
	assert len(second.messages) == 6 and second.new_mail == 1


def test_preview_is_fetched_once( ptm, server, globals_stub ) :
	mb = mailbox( ptm, server )
	mb.rescan()
	server.store.forget_commands()

	assert 'quarterly report' in mb.get_message( 'UID0001' )
	assert topped( server ) == ['TOP 1 200']

	assert 'quarterly report' in mb.get_message( 'UID0001' )
	assert topped( server ) == ['TOP 1 200']		# second read never left the process

	again = mailbox( ptm, server )				# and not after a restart either
	assert 'quarterly report' in again.get_message( 'UID0001' )
	assert topped( server ) == ['TOP 1 200']


def test_deleted_message_is_gone_after_a_restart( ptm, server, globals_stub ) :
	mb = mailbox( ptm, server )
	mb.rescan()
	mb.get_message( 'UID0002' )

	mb.killed = set( ['UID0002'] )
	mb.rescan()						# this is what the delete button does

	assert 'DELE 2' in server.store.commands()
	assert 'UID0002' not in mb.messages and 'UID0002' not in mb.bodies

	after = mailbox( ptm, server )
	after.rescan()
	assert sorted( after.messages ) == ['UID0001', 'UID0003', 'UID0004', 'UID0005']


def test_blacklisted_message_is_deleted_on_load( ptm, server, globals_stub ) :
	mb = mailbox( ptm, server, black_from_contains = ['spam.example'] )
	mb.rescan()

	assert 'DELE 3' in server.store.commands()
	assert 'UID0003' not in mb.messages

	after = mailbox( ptm, server, black_from_contains = ['spam.example'] )
	after.rescan()
	assert 'UID0003' not in after.messages		# and it does not come back off the cache


def test_blacklist_added_after_the_cache_still_bites( ptm, server, globals_stub ) :
	plain = mailbox( ptm, server )
	plain.rescan()
	assert 'UID0003' in plain.messages
	server.store.forget_commands()

	later = mailbox( ptm, server, black_from_contains = ['spam.example'] )
	later.rescan()

	assert 'DELE 3' in server.store.commands()
	assert topped( server ) == []			# decided on the cached header alone
	assert 'UID0003' not in later.messages
