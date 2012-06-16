#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import ConfigParser
import tempfile
import re

cwd = os.getcwd() # We are using this a lot, it seems more sensible to
                  # cache it.

#
# Existence & Value Functions
#
def get_config():
    return os.path.join( cwd, '.config' )

def get_cache_file():
    return os.path.join( cwd, '.config/.cache' )

def get_current_target():
    if ( exist_cache() ): # Do we have a .cache with default config

        cache = ConfigParser.RawConfigParser()
        cache.read( get_cache_file() )
        return cache.get( 'current', 'target' )
    else:

        # This case implies there might be no .config directory, but
        # puptent target makes one so it shouldn't be an issue if the
        # suggestion is followed.
        print "Error: No current target selected in cache.\n" + \
            "Did you use `puptent target name' to pick a target?"
        return False

def get_variables_build_string( build ):

    var_pat = re.compile('\$\([A-Z_]*\)')
    return re.findall( var_pat, build )

# Returns a dictionary of both environment variables that are set and
# variables in the .cache file. By default, all variables in the
# .cache files override those from other sources and should have
# priority.
def get_full_env():
    
    result = dict( os.environ ) # Import existing environment
    
    if ( not exist_cache() ):
        print "Error: No .cache exists."
        return None
    
    cache_file = ConfigParser.RawConfigParser()
    cache_file.read( get_cache_file() )
    
    if ( cache_file.has_section( 'vars' )):
        
        # This overrides the stuff in result
        uppercased = []
        for i in cache_file.items( 'vars' ):
            uppercased = [(i[0].upper(), i[1])] + uppercased
        result.update( uppercased )

    return result   

def exist_config():
    return os.path.exists( get_config() )

def exist_target( target ):
    return os.path.exists( os.path.join ( get_config(), target ))

def exist_cache():
    return os.path.exists( os.path.join ( get_config(), '.cache'))

def exist_file_current_target( filename ):
    
    # This function is designed for testing one and only one file just
    # as forewarning later.
    for line in open( os.path.join( get_config(), get_current_target())):
        if line.strip() == filename:
            return True
    return False

def exist_build():
    if ( exist_config() ):
        return os.path.exists( os.path.join ( get_config(), '.build'))
    return False

#
# Tools
#
def extract_varname( variable_w_dollar ):
    return variable_w_dollar[2:-1]

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
    
    if ( not cache.has_section( subheading )):
        cache.add_section( subheading )
    cache.set( subheading, key, value )
    with open( cache_file, "w") as fp:
        cache.write(fp)

def replace_vars( build_str ):
    
    b = get_full_env()
    varlist = get_variables_build_string( build_str )
    keep_going = True

    for i in varlist:
        if extract_varname(i) not in b:
            print "Error: " + extract_varname(i) + " was never assigned a value."
            keep_going = False

    if not keep_going:

        # We want to list all the variables that aren't set
        print "Next time use `puptent check build' to list all unset variables."
        return False
    
    print varlist
    for i in varlist:
        print i
        build_str = build_str.replace( i, b[ extract_varname(i) ] )

    return build_str

def do_build( target ):
    print "thing"

#
# Operators
#
def op_target(name=""):

    # TODO: Filter out the . files
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

def op_add(filename=""):

    if ( filename == "" ):
        print "Error: No files specified to add. Use `puptent add file1` to add files."
        return
    
    target = get_current_target()
    if ( not target ):
        
        print "You can't add files until you've selected a target"
        return

    fp = open( os.path.join( get_config(), target ), "a" )
    
    # TODO: Allow for variable length arguments
    if ( not exist_file_current_target( filename )):        
        fp.write(filename + "\n")

def op_remove(filename=""):
    
    if ( filename == "" ):
        print "Error: No files specified to remove. Use `puptent remove file1' to remove files."
        return

    if ( not exist_file_current_target( filename )):
        
        print "File " + filename + " was not in the current target to remove"
        return

    tmp = tempfile.TemporaryFile()
    target = get_current_target()
    
    # Read all of the data in, skipping the file in question
    for line in open( os.path.join( get_config(), target )):
        if ( line.strip() == filename ):
            continue
        else:
            tmp.write( line )
    
    #Now write it back
    tmp.seek(0)
    target = open( os.path.join( get_config(), target ), "w" )
    target.writelines( tmp.readlines() )

def op_set( key="", value="" ):
    
    if ( key == "" ):
        print "Error: A key and value to be set must be specified. `puptent set key value'"
        return

    if ( value == "" ):
        print "Error: A key must have a value associated with it. `puptent set key value'"
        return

    load_and_set_cache( 'vars', key, value )

def op_build( target="" ):
    
    if ( target == "" ):
        print "Error: You must specify a target to build. `puptent build target'"
        return

    if ( not exist_target( target )):
        print "Error: The target " + target + " does not exist."
        return
        
    if ( not exist_build() ):
        print "Error: You must define a .build file in the .config directory!"
        return

    # TODO: expand this to do a build all if no target is specified
    # like I wanted to.

    do_build( target )
