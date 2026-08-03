#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# the config holds the password, so it should not be readable by anyone else

import os
import stat


def mode_of( config ) :
	return stat.S_IMODE( os.stat( config.fileName() ).st_mode )


def test_group_and_other_bits_are_dropped( ptm, config ) :
	config.setValue( 'account0/passwd', 'c2VjcmV0' )
	config.sync()
	os.chmod( config.fileName(), 0o644 )

	ptm.protect_config()

	assert mode_of( config ) == 0o600


def test_the_owner_bits_are_left_alone( ptm, config ) :
	config.setValue( 'account0/passwd', 'c2VjcmV0' )
	config.sync()
	os.chmod( config.fileName(), 0o400 )	# read only on purpose, keep it that way

	ptm.protect_config()

	assert mode_of( config ) == 0o400


def test_an_already_private_config_is_not_touched( ptm, config, monkeypatch ) :
	config.setValue( 'account0/passwd', 'c2VjcmV0' )
	config.sync()
	os.chmod( config.fileName(), 0o600 )

	chmodded = []
	monkeypatch.setattr( ptm.os, 'chmod', lambda path, mode : chmodded.append( path ) )
	ptm.protect_config()

	assert chmodded == []


def test_a_missing_config_is_not_an_error( ptm, config ) :
	# nothing has been saved yet, so QSettings has not written the file
	assert not os.path.exists( config.fileName() )

	ptm.protect_config()		# must not raise


def test_saving_the_settings_keeps_the_config_private( ptm, qapp, config, monkeypatch ) :
	from test_settings_ux import save_account

	monkeypatch.setattr( ptm, 'form', None, raising = False )
	save_account( ptm, qapp, config )
	config.sync()
	os.chmod( config.fileName(), 0o644 )

	ptm.ConfigForm.accept( ptm.ConfigForm() )

	assert mode_of( config ) == 0o600
