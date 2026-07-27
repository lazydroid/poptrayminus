#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# a dummy POP3 server to test poptrayminus against, both by hand and from pytest
#
#	python3 tests/dummy_pop3.py --port 1110 --state /tmp/dummy
#
# it keeps five messages, with encoded headers and spam scores among them, and
# adds a sixth one when the --state directory holds a file named 'extra'.
# deletions are written to that directory too, so they survive a restart, like
# on a real server.  every command is appended to the log, so a test can assert
# on the exact protocol sequence -- which is the whole point when checking that
# a cached message is *not* fetched again.

import argparse
import os
import socketserver
import threading


def make_message( frm, to, subj, date, body, score = None ) :
	head = [ 'From: %s' % frm, 'To: %s' % to, 'Subject: %s' % subj, 'Date: %s' % date ]
	if score is not None :
		head.append( 'X-Spam-Score: %s' % score )
	return '\r\n'.join( head ) + '\r\n\r\n' + body + '\r\n'


BASE = [
	make_message( 'alice@example.com', 'tester@example.com', 'Quarterly report',
		'Mon, 06 Jan 2025 10:15:00 +0000', 'Hi, here is the quarterly report.', '-30.0' ),
	make_message( 'bob@example.com', 'tester@example.com', 'Lunch tomorrow?',
		'Tue, 07 Jan 2025 12:00:00 +0000', 'Want to grab lunch?', None ),
	make_message( 'spammy@spam.example', 'tester@example.com', 'You WON a prize!!!',
		'Wed, 08 Jan 2025 03:30:00 +0000', 'Click here to claim.', '85.0' ),
	make_message( '=?utf-8?B?0JjQstCw0L0=?= <ivan@example.com>', 'tester@example.com',
		'=?utf-8?B?0L/RgNC40LLQtdGC?=',
		'Thu, 09 Jan 2025 09:45:00 +0000', 'utf-8 base64 encoded subject.', '1.0' ),
	make_message( '=?iso-8859-1?Q?Ren=E9?= <rene@example.com>', 'tester@example.com',
		'=?iso-8859-1?Q?caf=E9?=',
		'Fri, 10 Jan 2025 08:00:00 +0000', 'quoted-printable latin-1 subject.', '0.0' ),
]

SIXTH = make_message( 'carol@example.com', 'tester@example.com', 'Brand new message',
	'Mon, 13 Jan 2025 11:11:00 +0000', 'This one arrived after the first scan.', '0.0' )


class Mailstore :
	# the messages and the deletions, kept in a directory so a restart sees them again

	def __init__( self, state ) :
		self.state = state
		os.makedirs( state, exist_ok = True )

	def path( self, name ) :
		return os.path.join( self.state, name )

	def messages( self ) :
		return BASE + ( [ SIXTH ] if os.path.exists( self.path('extra') ) else [] )

	def deliver_extra( self ) :
		open( self.path('extra'), 'w' ).close()

	def deleted( self ) :
		try :
			with open( self.path('deleted') ) as ff :
				return set( int(i) for i in ff.read().split() )
		except OSError :
			return set()

	def delete( self, num ) :
		with open( self.path('deleted'), 'a' ) as ff :
			ff.write( '%d\n' % num )

	def log( self, line ) :
		with open( self.path('log'), 'a' ) as ff :
			ff.write( line + '\n' )

	def commands( self ) :
		try :
			with open( self.path('log') ) as ff :
				return ff.read().split('\n')[:-1]
		except OSError :
			return []

	def forget_commands( self ) :
		try :
			os.unlink( self.path('log') )
		except OSError :
			pass


class Handler( socketserver.StreamRequestHandler ) :
	def send( self, text ) :
		self.wfile.write( (text + '\r\n').encode() )
		self.wfile.flush()

	def send_lines( self, lines ) :
		self.send( '+OK message follows' )
		for line in lines :
			self.send( ('.' + line) if line.startswith('.') else line )	# byte stuffing
		self.send( '.' )

	def handle( self ) :
		store = self.server.store
		self.send( '+OK dummy POP3 server ready' )

		while True :
			line = self.rfile.readline()
			if not line :
				return

			parts = line.decode( errors = 'replace' ).strip().split()
			if not parts :
				continue

			cmd, args = parts[0].upper(), parts[1:]
			store.log( ' '.join( parts if cmd != 'PASS' else ['PASS', '***'] ) )

			messages = store.messages()
			dead = store.deleted()
			live = [ i for i in range( 1, len(messages) + 1 ) if i not in dead ]

			if cmd in ( 'USER', 'PASS' ) :
				self.send( '+OK ok' )
			elif cmd == 'CAPA' :
				self.send( '-ERR unsupported' )
			elif cmd == 'STAT' :
				self.send( '+OK %d %d' % ( len(live), sum( len(messages[i-1]) for i in live ) ) )
			elif cmd == 'LIST' :
				if args :
					num = int( args[0] )
					if num in dead or num > len(messages) :
						self.send( '-ERR no such message' )
					else :
						self.send( '+OK %d %d' % ( num, len(messages[num-1]) ) )
				else :
					self.send( '+OK %d messages' % len(live) )
					for i in live :
						self.send( '%d %d' % ( i, len(messages[i-1]) ) )
					self.send( '.' )
			elif cmd == 'UIDL' :
				# derived from the message number and never reused, as rfc1939 wants
				if args :
					self.send( '+OK %d UID%04d' % ( int(args[0]), int(args[0]) ) )
				else :
					self.send( '+OK' )
					for i in live :
						self.send( '%d UID%04d' % (i, i) )
					self.send( '.' )
			elif cmd in ( 'TOP', 'RETR' ) :
				num = int( args[0] )
				if num in dead or num > len(messages) :
					self.send( '-ERR no such message' )
					continue
				head, _, body = messages[num-1].partition( '\r\n\r\n' )
				if cmd == 'RETR' :
					self.send_lines( messages[num-1].split('\r\n') )
				else :
					self.send_lines( head.split('\r\n') + [''] + body.split('\r\n')[:int(args[1])] )
			elif cmd == 'DELE' :
				store.delete( int( args[0] ) )
				self.send( '+OK deleted' )
			elif cmd in ( 'NOOP', 'RSET' ) :
				self.send( '+OK' )
			elif cmd == 'QUIT' :
				self.send( '+OK bye' )
				return
			else :
				self.send( '-ERR unknown command' )


class Server( socketserver.ThreadingTCPServer ) :
	allow_reuse_address = True
	daemon_threads = True

	def __init__( self, address, store ) :
		socketserver.ThreadingTCPServer.__init__( self, address, Handler )
		self.store = store


def serve( state, port = 0 ) :
	# port 0 picks a free one, which is what the tests want
	server = Server( ('127.0.0.1', port), Mailstore( state ) )
	threading.Thread( target = server.serve_forever, daemon = True ).start()
	return server


def main() :
	parser = argparse.ArgumentParser( description = 'dummy POP3 server for poptrayminus testing' )
	parser.add_argument( '--port', type = int, default = 1110 )
	parser.add_argument( '--state', default = '/tmp/dummy_pop3',
		help = 'directory holding the log, the deletions and the "extra" flag file' )
	parser.add_argument( '--extra', action = 'store_true', help = 'deliver the sixth message and exit' )
	args = parser.parse_args()

	store = Mailstore( args.state )
	if args.extra :
		store.deliver_extra()
		return

	print( 'listening on 127.0.0.1:%d, state in %s' % (args.port, args.state) )
	Server( ('127.0.0.1', args.port), store ).serve_forever()


if __name__ == '__main__' :
	main()
