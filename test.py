#!/usr/bin/env python
"""
This script sets up an environment for my running my atari programs in hatari.

"""
import os
from os.path import exists
from subprocess import call
import subprocess
from optparse import OptionParser
import shutil
import re
from urllib import urlretrieve
import zipfile 
import base64

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
            params.extend(['-D', '--debug-except','all']) # ,'--parse','break.ini'])

        if os.path.exists( 'testenv/empty_dsk.zip' ):
            params.extend( ['--disk-a', 'testenv/empty_dsk.zip' ] )

        params.extend( ['--fast-boot','true', '--memsize','0','-d', 'testenv/root' ] )
        # params.extend( ['--frameskips', '1'] )
        params.extend( ['--machine', opts.machine, '--tos', self.tos[opts.machine]] )


        if 'params' in self:
            params.extend( self.params )

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


def setup_test_env( opts = []):
    print( "Setting up test environment..." )
    old_cwd = os.getcwd()

    if not os.path.exists( "testenv"):
        os.mkdir( "testenv" )

    os.chdir( "testenv" )

    # create disk image
    diskimgfile = open( "empty_dsk.zip","w")
    diskimgfile.write( base64.b64decode( zipped_empty_disk ) )
    diskimgfile.close()

    # download tosses
    dl_tos()

    os.chdir( old_cwd )

    system = os.uname()[0]
    env = TestEnv()

    # This needs to be done a better way. Maybe require hatari in system path?
    hatari_bins = [ 
                    '/Applications/Hatari.app/Contents/MacOS/Hatari',
                    '/Applications/Hatari_original.app/Contents/MacOS/Hatari',
                    '/cygdrive/c/Applications/hatari-1.7.0_windows/hatari.exe',
                  ]

    for path in hatari_bins:
        if exists(path):
            env.hatari = path
            break

    env.tos = {
                'st' : 'testenv/TOS/swedish/tos104se/tos104se.img',
                'ste' : 'testenv/TOS/swedish/tos162se/tos162se.img',
              }

    validate_env(env)

    return env



def validate_env( env ):
    # Just check if files are found.

    try:
        if not os.path.exists( env.hatari ):
            raise Exception()
    except Exception, e:
        print("\033[33mCould not find hatari binary (expected location: /Applications/Hatari.app).\033[0m")

    class TOSnotFoundException( Exception):
        pass

    try:
        for tosp in env.tos.values():
            if not os.path.exists( tosp ):
                raise TOSnotFoundException( tosp )
    except TOSnotFoundException, e:
        print("\033[33mCould not TOS file %s\033[0m" % e)
    except KeyError, e:
        print("\033[33mTOS files missing from environment\033[0m" )


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
    parser.add_option( "-D","--debug", dest="enable_debugger", action="store_true")
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
        env = setup_test_env( opts )
        save_env( env )
        print("atari test emulator environment setup complete.")
        exit(0)

    env = get_test_env( )
    if opts.setup:
    	save_env( env )

    env.run_test( opts, args )
