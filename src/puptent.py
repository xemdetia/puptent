#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import ConfigParser

cwd = os.getcwd() # We are using this a lot, it seems more sensible to
                  # cache it.

#
# Existence & Value Functions
#
def get_config():
    return os.path.join( cwd, '.config' )

def exist_config():
    return os.path.exists( get_config() )

def exist_target( target ):
    return os.path.exists( os.path.join ( get_config(), target ))

def exist_cache():
    return os.path.exists( os.path.join ( get_config(), '.cache'))

#
# Tasks
#    
def make_target( name ):

    if ( not exist_config() ):
        print "Creating new .config directory where there wasn't one"
        os.mkdir( cwd + "/.config" )
    open( cwd + "/.config/" + name, 'w')
    load_and_set_cache( 'current', 'target', name )
    print "Target " + name + " automatically chosen as current target"

# A simple routine to open the cache file and tweak something
def load_and_set_cache( subheading, key, value ):
    
    cache_file = os.path.join( cwd, '.config/.cache' )
    cache = ConfigParser.RawConfigParser()
    if ( exist_cache() ):
        
        # Load if the .cache exists
        cache.read( cache_file )
    else:
        cache.add_section( subheading )
    cache.set( subheading, key, value )
    with open( cache_file, "w") as fp:
        cache.write(fp)

#
# Operators
#
def op_target(name=""):

    if ( name == "" ):
        if ( exist_config() ):
            for i in os.listdir( get_config() ):
                print i
        else:
            print "Error: No targets. Use `puptent target name' to create a new target"
    elif ( exist_target( name )):
        load_and_set_cache( 'current', 'target', name )
    else:
        make_target( name )
        load_and_set_cache( 'current', 'target', name )

