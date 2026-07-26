#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# the on disk message cache, so a huge mailbox is not read all over again on every start

import gzip
import hashlib
import json
import os

import pytest

from conftest import make_account
from test_protocol import FakePOP3, make_message


def counting_mbox( messages ) :
	# remembers which message numbers had their headers pulled
	mbox = FakePOP3( messages )
	mbox.topped = []
	top = mbox.top

	def counted( num, lines ) :
		mbox.topped.append( int(num) )
		return top( num, lines )

	mbox.top = counted
	return mbox


def mailbox( ptm, monkeypatch, mbox, **kwargs ) :
	mb = ptm.Mailbox( make_account( **kwargs ) )
	monkeypatch.setattr( mb, 'open_mbox', lambda : mbox )
	return mb


def test_cache_file_hashes_the_user( ptm, cache_home ) :
	mb = ptm.Mailbox( make_account( user = 'sómeone/../weird@example.com' ) )
	name = mb.cache_file()

	assert name.startswith( str(cache_home) )
	assert name.endswith(
		'mail.example.com_%s.json.gz' % hashlib.md5( 'sómeone/../weird@example.com'.encode('utf-8') ).hexdigest()
	)
	assert '/' not in name[ len(str(cache_home)) + 1 : ]


def test_cache_file_sanitizes_the_host( ptm ) :
	mb = ptm.Mailbox( make_account( host = 'mail example.com:110/../..' ) )
	assert 'mail_example.com_110_.._..' in mb.cache_file()


def test_rescan_writes_the_cache( ptm, monkeypatch, globals_stub, cache_home ) :
	mbox = counting_mbox( { 1: ('UID0001', make_message()), 2: ('UID0002', make_message()) } )
	mb = mailbox( ptm, monkeypatch, mbox )

	mb.rescan()

	with gzip.open( mb.cache_file(), 'rt', encoding = 'utf-8' ) as ff :
		data = json.load( ff )
	assert data['version'] == ptm.CACHE_VERSION
	assert data['host'] == 'mail.example.com'
	assert sorted( data['messages'] ) == ['UID0001', 'UID0002']
	assert data['messages']['UID0001'][5] == 'hi'		# subject
	assert not mb.cache_file().endswith( '.tmp' ) and mbox.topped == [1, 2]


def test_second_rescan_only_fetches_new_messages( ptm, monkeypatch, globals_stub ) :
	messages = { 1: ('UID0001', make_message()), 2: ('UID0002', make_message()) }
	first = mailbox( ptm, monkeypatch, counting_mbox( messages ) )
	first.rescan()

	messages[3] = ('UID0003', make_message( sender = 'someone@else.com' ))
	mbox = counting_mbox( messages )
	second = mailbox( ptm, monkeypatch, mbox )		# a fresh start, cache comes off disk
	second.rescan()

	assert mbox.topped == [3]		# the two known ones were not pulled again
	assert sorted( second.messages ) == ['UID0001', 'UID0002', 'UID0003']
	assert second.new_mail == 1
	assert second.messages['UID0003'][1] == 'someone@else.com'


def test_cached_message_gone_from_the_server_is_dropped( ptm, monkeypatch, globals_stub ) :
	messages = { 1: ('UID0001', make_message()), 2: ('UID0002', make_message()) }
	first = mailbox( ptm, monkeypatch, counting_mbox( messages ) )
	first.rescan()

	del messages[2]
	mbox = counting_mbox( messages )
	second = mailbox( ptm, monkeypatch, mbox )
	second.rescan()

	assert mbox.topped == []
	assert sorted( second.messages ) == ['UID0001']


def test_cache_is_per_account( ptm, monkeypatch, globals_stub ) :
	messages = { 1: ('UID0001', make_message()) }
	first = mailbox( ptm, monkeypatch, counting_mbox( messages ), user = 'someone' )
	first.rescan()

	mbox = counting_mbox( messages )
	other = mailbox( ptm, monkeypatch, mbox, user = 'somebody-else' )
	other.rescan()

	assert mbox.topped == [1]		# different user, no cache to lean on


def test_blacklisted_messages_are_not_cached( ptm, monkeypatch, globals_stub ) :
	mbox = counting_mbox( {
		1: ('UID0001', make_message()),
		2: ('UID0002', make_message( sender = 'spammer@example.net' )),
	} )
	mb = mailbox( ptm, monkeypatch, mbox, black_from_contains = ['spammer@'] )

	mb.rescan()

	with gzip.open( mb.cache_file(), 'rt', encoding = 'utf-8' ) as ff :
		assert sorted( json.load( ff )['messages'] ) == ['UID0001']

	again = counting_mbox( { 1: ('UID0001', make_message()) } )
	reloaded = mailbox( ptm, monkeypatch, again, black_from_contains = ['spammer@'] )
	reloaded.rescan()
	assert again.topped == [] and sorted( reloaded.messages ) == ['UID0001']


def test_cached_messages_survive_an_unreachable_server( ptm, monkeypatch, globals_stub ) :
	first = mailbox( ptm, monkeypatch, counting_mbox( { 1: ('UID0001', make_message()) } ) )
	first.rescan()

	def refuse() :
		raise OSError( 'connection refused' )

	second = ptm.Mailbox( make_account() )
	monkeypatch.setattr( second, 'open_mbox', refuse )
	with pytest.raises( OSError ) :
		second.rescan()

	assert sorted( second.messages ) == ['UID0001']		# the list is not blanked when offline


def test_missing_cache_is_not_an_error( ptm ) :
	mb = ptm.Mailbox( make_account() )
	mb.load_cache()
	assert mb.messages == {} and mb.cache_loaded


def test_corrupt_cache_is_ignored( ptm, monkeypatch, globals_stub, cache_home ) :
	mb = ptm.Mailbox( make_account() )
	cache_home.mkdir( parents = True )
	with open( mb.cache_file(), 'wb' ) as ff :
		ff.write( b'this is not gzipped json' )

	mb.load_cache()
	assert mb.messages == {}

	mbox = counting_mbox( { 1: ('UID0001', make_message()) } )
	monkeypatch.setattr( mb, 'open_mbox', lambda : mbox )
	mb.rescan()
	assert mbox.topped == [1] and sorted( mb.messages ) == ['UID0001']


def test_cache_from_another_version_is_ignored( ptm, cache_home ) :
	mb = ptm.Mailbox( make_account() )
	cache_home.mkdir( parents = True )
	with gzip.open( mb.cache_file(), 'wt', encoding = 'utf-8' ) as ff :
		json.dump( { 'version': ptm.CACHE_VERSION + 1, 'messages': { 'UID0001': [1, 2, 3, 4, 5, 6] } }, ff )

	mb.load_cache()
	assert mb.messages == {}


def test_garbled_rows_are_dropped( ptm, cache_home ) :
	mb = ptm.Mailbox( make_account() )
	cache_home.mkdir( parents = True )
	with gzip.open( mb.cache_file(), 'wt', encoding = 'utf-8' ) as ff :
		json.dump( {
			'version': ptm.CACHE_VERSION,
			'date': '2015-01-01 12:00',
			'messages': {
				'UID0001': ['0.0', 'from', 'to', 'date', 'size', 'subj'],
				'UID0002': ['too', 'short'],
				'UID0003': 'not even a list',
			},
		}, ff )

	mb.load_cache()
	assert sorted( mb.messages ) == ['UID0001']
	assert mb.date == '2015-01-01 12:00'


def test_no_cache_without_uidl( ptm, monkeypatch, globals_stub ) :
	# message numbers shift around, so there is nothing worth keeping
	mbox = counting_mbox( { 1: ('UID0001', make_message()) } )
	mbox.uidl = lambda : ( b'-ERR not supported', [], 0 )
	mb = mailbox( ptm, monkeypatch, mbox )

	mb.rescan()

	assert sorted( mb.messages ) == [1]
	assert not os.path.exists( mb.cache_file() )
