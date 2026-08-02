#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# the preview used to show the raw source, mime boundaries and base64 blobs included

import base64
import quopri

from conftest import make_account
from test_protocol import FakePOP3


def wrap( body, headers = '' ) :
	head = 'From: friend@example.com\nTo: me@example.com\nSubject: hi\n'
	return head + ( headers + '\n' if headers else '' ) + '\n' + body


def test_plain_body_is_shown_as_is( ptm ) :
	out = ptm.render_message( wrap( 'hello there\n' ) )

	assert '<b>From:</b> friend@example.com' in out
	assert '<pre>hello there\n</pre>' in out


def test_headers_are_decoded( ptm ) :
	raw = 'From: =?utf-8?B?0L/RgNC40LLQtdGC?= <friend@example.com>\nSubject: =?utf-8?q?caf=C3=A9?=\n\nbody\n'

	out = ptm.render_message( raw )

	assert 'привет' in out and 'café' in out
	assert '=?utf-8?' not in out


def test_base64_body_is_decoded( ptm ) :
	body = base64.b64encode( 'wake up neo\n'.encode() ).decode()
	raw = wrap( body, 'Content-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: base64' )

	out = ptm.render_message( raw )

	assert 'wake up neo' in out
	assert body not in out			# and the blob itself is gone


def test_quoted_printable_body_is_decoded( ptm ) :
	body = quopri.encodestring( 'na=ve café — dash\n'.encode() ).decode()
	raw = wrap( body, 'Content-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: quoted-printable' )

	out = ptm.render_message( raw )

	assert 'café — dash' in out
	assert '=C3=A9' not in out


def test_koi8_body_is_decoded( ptm ) :
	body = base64.b64encode( 'привет'.encode( 'koi8-r' ) ).decode()
	raw = wrap( body, 'Content-Type: text/plain; charset=koi8-r\nContent-Transfer-Encoding: base64' )

	assert 'привет' in ptm.render_message( raw )


def test_made_up_charset_falls_back_to_guessing( ptm ) :
	body = base64.b64encode( 'привет'.encode( 'utf-8' ) ).decode()
	raw = wrap( body, 'Content-Type: text/plain; charset=nosuch-8\nContent-Transfer-Encoding: base64' )

	assert 'привет' in ptm.render_message( raw )


def test_undeclared_charset_is_guessed( ptm ) :
	body = base64.b64encode( 'привет, как дела, вот такие дела'.encode( 'utf-8' ) ).decode()
	raw = wrap( body, 'Content-Transfer-Encoding: base64' )

	assert 'привет' in ptm.render_message( raw )


MULTIPART = '''From: friend@example.com
Subject: mixed bag
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="xxx"

--xxx
Content-Type: text/plain; charset=utf-8

the readable part
--xxx
Content-Type: text/html; charset=utf-8

<html><body>the html part</body></html>
--xxx--
'''


def test_multipart_prefers_the_text_part( ptm ) :
	out = ptm.render_message( MULTIPART )

	assert 'the readable part' in out
	assert 'the html part' not in out
	assert 'boundary' not in out and '--xxx' not in out


def test_html_only_message_keeps_its_markup( ptm ) :
	raw = MULTIPART.replace( '''--xxx
Content-Type: text/plain; charset=utf-8

the readable part
''', '' )

	out = ptm.render_message( raw )

	assert '<body>the html part</body>' in out		# handed to the browser as html
	assert '&lt;body&gt;' not in out


ATTACHED = '''From: friend@example.com
Subject: here you go
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="yyy"

--yyy
Content-Type: text/plain; charset=utf-8

see attached
--yyy
Content-Type: application/pdf; name="=?utf-8?q?caf=C3=A9=2Epdf?="
Content-Disposition: attachment; filename="=?utf-8?q?caf=C3=A9=2Epdf?="
Content-Transfer-Encoding: base64

JVBERi0xLjQK
--yyy--
'''


def test_attachments_are_listed_not_dumped( ptm ) :
	out = ptm.render_message( ATTACHED )

	assert 'see attached' in out
	assert 'café.pdf' in out
	assert 'JVBERi0xLjQK' not in out


def test_attachment_only_message_still_shows_headers( ptm ) :
	raw = ATTACHED.replace( '''--yyy
Content-Type: text/plain; charset=utf-8

see attached
''', '' )

	out = ptm.render_message( raw )

	assert 'café.pdf' in out and 'here you go' in out


def test_html_in_a_plain_body_is_escaped( ptm ) :
	out = ptm.render_message( wrap( 'watch out for <script>alert(1)</script>\n' ) )

	assert '&lt;script&gt;' in out
	assert '<script>' not in out


def test_truncated_base64_still_shows_what_arrived( ptm ) :
	body = base64.b64encode( ('a long message, ' * 100).encode() ).decode()
	raw = wrap( body[:200], 'Content-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: base64' )

	out = ptm.render_message( raw )

	assert 'a long message' in out


def test_garbage_is_shown_rather_than_raising( ptm ) :
	out = ptm.render_message( 'this is not a message at all' )

	assert 'not a message' in out


def test_empty_message( ptm ) :
	assert ptm.render_message( '' ) == '<hr><pre></pre>'


def test_preview_decodes_and_the_cache_keeps_the_source( ptm, monkeypatch, globals_stub ) :
	body = base64.b64encode( 'wake up neo\n'.encode() ).decode()
	raw = wrap( body, 'Content-Type: text/plain; charset=utf-8\nContent-Transfer-Encoding: base64' ).encode()

	mbox = FakePOP3( { 1: ('UID0001', raw) } )
	mb = ptm.Mailbox( make_account() )
	monkeypatch.setattr( mb, 'open_mbox', lambda : mbox )

	assert 'wake up neo' in mb.get_message( 'UID0001' )
	assert body in mb.bodies['UID0001']		# cached raw, so a better renderer needs no refetch
	assert 'wake up neo' in mb.get_message( 'UID0001' )	# and the cached copy renders too
