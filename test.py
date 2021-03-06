#!/usr/bin/env python
"""
This script sets up an environment for my running my atari programs in hatari.

"""
import os
from os.path import *
import sys
from subprocess import call
import subprocess
from optparse import OptionParser
import shutil
import re
from urllib import urlretrieve
import zipfile
import base64
import platform
"""
When booting Hatari, it is much faster to do so if there is a disk inserted
in drive a. This is a base64 encode zip-file containing and empty .st file.
Since hatari can cope with disk images inside zip files, all that is needed
is to decode the base64 string and save it to disk. And pass the file to
hatari of course.
"""
zipped_empty_disk = "UEsDBBQAAgAIAKC0yESrFOmvngMAAADADQAMABwAZHVtbXlkaXNrLnN0VVQJAANryZRTZiyW" + \
                    "U3V4CwABBPYBAAAEFAAAAO3WMQ2AQBQFwcdPoMEDks4IDZLpCBKuOhJcQGYkbLV32mvfrlRN" + \
                    "qSPn0uesqfB/fQwRAAD8HwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA" + \
                    "AAAAAAAAAAAAAAAAAAwGc9UEsBAh4DFAACAAgAoLTIRKsU6a+eAwAAAMANAAwAGAAAAAAAAAA" + \
                    "AAKSBAAAAAGR1bW15ZGlzay5zdFVUBQADa8mUU3V4CwABBPYBAAAEFAAAAFBLBQYAAAAAAQAB" + \
                    "AFIAAADkAwAAAAA="


#HATARI_FLAGS = -c hatari.cfg -d .
#HATARI_FLAGS = --confirm-quit 0 -D -d .


esl = re.compile( "\/cygdrive\/([a-z])\/(.*)" )

def cyg2win(cygpath):
    m = esl.match( cygpath )
    return "%s:/%s"%( m.group(1), m.group(2))

class TestEnv(dict):

    def run_test( self,opts, args ):

        params = [ self.hatari ]
        params.extend( '--confirm-quit 0'.split(' ') )


        if opts.no_auto:
            dest_path = 'testenv/root'
        else:
            dest_path = 'testenv/root/auto'

        try:
            shutil.rmtree( dest_path )
        except:
            pass
        os.makedirs( dest_path )

        for filename in args:
            dest ='%s/%s' % (dest_path,filename)
            if os.path.isdir( filename ):
                shutil.copytree(filename, dest )
            else:
                shutil.copyfile( filename, dest )

        if opts.enable_debugger:
            params.extend(['-D', '--debug-except','all','--bios-intercept']) # ,'--parse','break.ini'])
            #params.extend( ['-W'])

        if os.path.exists( 'testenv/dummy.zip' ):
            params.extend( ['--disk-a', 'testenv/dummy.zip' ] )

        params.extend( ['--fast-boot','true', '--memsize','0','-d', 'testenv/root' ] )
        # params.extend( ['--frameskips', '1'] )
        params.extend( ['--machine', opts.machine, '--tos', self.tos[opts.machine]] )
        params.extend( ['--natfeats', 'true'])

        if 'more' in self:
            params.extend( self.more )

        try:
            print( ' '.join(params))
            call( params )

        except( KeyboardInterrupt ):
            pass
        except Exception as e:
            print(e)

    def __get__(self,key):
        return self[key]

    def __set__(self,key,value):
        self[key] = value


# unzip a file
def unzip(path):
    zfile = zipfile.ZipFile(path)
    for name in zfile.namelist():
        (dirname, filename) = os.path.split(name)
        if filename == '':
            # directory
            if not os.path.exists(dirname):
                os.mkdir(dirname)
        else:
            # file
            fd = open(name, 'w')
            fd.write(zfile.read(name))
            fd.close()
    zfile.close()

def dl_tos( ):
    if not os.path.exists( "ALL_TOS.ZIP"):
        print( "Downloading TOS ROM images..." )
        zip_url = "http://no-fragments.atari.org/no_fragments_14/TOOLS/WIN32/EMULATOR/ALL_TOS.ZIP"
        res = urlretrieve( zip_url, "ALL_TOS.ZIP" )
        if res:
            print( "Unpacking ROM images.")
            unzip( "ALL_TOS.ZIP")
    else:
        print( "TOS ROMs found." )

    unzip( "ALL_TOS.ZIP")


def ff(file_name, stack):
    while len(stack) > 0:
        cdir = stack.pop()

        if not exists(cdir) or not isdir(cdir):
            continue
        # check files
        for entry in os.listdir(cdir):
            path = os.path.join(cdir, entry)
            if isfile(path):
                if entry == file_name:
                    return path
            elif isdir(path):
                if 'hatari' in entry or 'Hatari' in entry:
                    #print("found prospect %s"%path)
                    stack.append(path)
                else:
                    #print("traverse dir %s"%path)
                    stack = [path] + stack

    return None

def find_hatari():

    dirstack = []
    res = None

    if sys.platform == 'cygwin':
        dirstack.append("/cygdrive/c/Applications/")
        dirstack.append("/cygdrive/c/Program Files/")
        dirstack.append("/cygdrive/c/Program Files (x86)/")
        res = ff("hatari.exe", dirstack)
    elif sys.platform == 'darwin':
        dirstack.append("/Applications/")
        res = ff("hatari", dirstack)
    elif sys.platform == 'win32':
        dirstack.append("C:/Applications/")
        dirstack.append("C:/Program Files/")
        dirstack.append("C:/Program Files (x86)/")
        res = ff("hatari.exe", dirstack)
    else:
        print("Sorry, I don't know where to look for hatari on platform %s"%sys.platform)

    return res


def setup_test_env( opts = []):
    print( "Setting up test environment..." )
    old_cwd = os.getcwd()

    if not os.path.exists( "testenv"):
        os.mkdir( "testenv" )

    os.chdir( "testenv" )

    # create disk image
    diskimgfile = open( "dummy.zip","w")
    diskimgfile.write( base64.b64decode( zipped_empty_disk ) )
    diskimgfile.close()

    # download tosses
    dl_tos()

    os.chdir( old_cwd )

    env = TestEnv()

    hatari_exe = find_hatari()
    if not hatari_exe == None:
        print("Found hatari executable at %s"%hatari_exe)
        env.hatari = hatari_exe

    env.tos = {
                'st' : 'testenv/TOS/swedish/tos104se/tos104se.img',
                'ste' : 'testenv/TOS/swedish/tos162se/tos162se.img',
                #'ste' : 'testenv/TOS/swedish/tos206se/tos206se.img',
              }

    validate_env(env)

    return env



def validate_env( env ):
    # Just check if files are found.


    try:
        if not os.path.exists( env.hatari ):
            raise Exception()
    except Exception, e:
        print("\033[33mHatari executable was not be located.\033[m")
        raise

    class TOSnotFoundException( Exception):
        pass

    try:
        for tosp in env.tos.values():
            if not os.path.exists( tosp ):
                raise TOSnotFoundException( tosp )
    except TOSnotFoundException, e:
        print("\033[33mCould not TOS file %s\033[0m" % e)
        return None
    except KeyError, e:
        print("\033[33mTOS files missing from environment\033[0m" )
        return None


def get_test_env( ):
    import cPickle
    if os.path.exists( 'testenv/.testconf.data' ):
        infile = open( 'testenv/.testconf.data', 'rb')
        env = cPickle.load(infile)
    else:
        env = setup_test_env()
        save_env( env )
    return env


def save_env(env):
    import cPickle
    outfile = open( 'testenv/.testconf.data', 'wb')
    cPickle.dump( env, outfile, -1 )


if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option( "--setup", dest="setup", action="store_true" )
    parser.add_option( "--clean", dest="clean", action="store_true" )
    parser.add_option( "--toslang", dest="toslang", default="se" )
    parser.add_option( "--debug", dest="enable_debugger", action="store_true")
    parser.add_option( "-m","--machine", dest="machine", default="st")
    parser.add_option( "--no-auto", dest="no_auto", action="store_true", default=False )

    (opts,args) = parser.parse_args()

    if opts.clean:
        if os.path.exists( 'testenv' ):
            print( "Deleting test env" )
            shutil.rmtree('testenv')
        else:
            print("Test environment could not be found")
        exit(0)

    if opts.setup:
        try:
            env = setup_test_env( opts )
            save_env( env )
            print("atari test emulator environment setup complete.")
        except Exception, e: 
            print(e)
 
        exit(0)

    env = get_test_env( )
    if opts.setup:
    	save_env( env )

    env.run_test( opts, args )
