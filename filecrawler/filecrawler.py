#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import codecs
import io
import tempfile

from .libs.process import Process

try:
    from .config import Configuration
except (ValueError, ImportError) as e:
    raise Exception('You may need to run filecrawler from the root directory (which includes README.md)', e)


import sys, datetime, time, os, requests, socket
from .util.color import Color
from .util.logger import Logger
from .util.tools import Tools


class FileCrawler(object):

    def main(self):
        ''' Either performs action based on arguments, or starts attack scanning '''

        self.dependency_check()

        Configuration.initialize()

        self.run()

    def dependency_check(self):
        ''' Check that required programs are installed '''
        required_apps = []
        optional_apps = []
        missing_required = False
        missing_optional = False

        for app in required_apps:
            if not Process.exists(app):
                missing_required = True
                Color.pl('{!} {R}error: required app {O}%s{R} was not found' % app)

        for app in optional_apps:
            if not Process.exists(app):
                missing_optional = True
                Color.pl('{!} {O}warning: recommended app {R}%s{O} was not found' % app)

        if missing_required:
            Color.pl('{!} {R}required app(s) were not found, exiting.{W}')
            sys.exit(-1)

        if missing_optional:
            Color.pl('{!} {O}recommended app(s) were not found')
            Color.pl('{!} {O}filecrawler may not work as expected{W}')

    def run(self):

        try:

            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            Logger.pl('{+} {C}start time {O}%s{W}' % timestamp)

            # Execute the specific actions
            Configuration.module.run()

        except Exception as e:
            Color.pl("\n{!} {R}Error: {O}%s" % str(e))
            if Configuration.verbose > 0 or True:
                Color.pl('\n{!} {O}Full stack trace below')
                from traceback import format_exc
                Color.p('\n{!}    ')
                err = format_exc().strip()
                err = err.replace('\n', '\n{W}{!} {W}   ')
                err = err.replace('  File', '{W}{D}File')
                err = err.replace('  Exception: ', '{R}Exception: {O}')
                Color.pl(err)
        except KeyboardInterrupt as e:
            raise e

        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        Logger.pl('{+} {C}End time {O}%s{W}' % timestamp)
        Logger.pl(' ')

    def print_banner(self):
        """ Displays ASCII art of the highest caliber.  """
        Color.pl(Configuration.get_banner())

    # Used to supress libmagic error 'lhs/off overflow 4294967295 0'
    # https://bugs.astron.com/view.php?id=426
    #  This code will suppress any child process stderr output
    @staticmethod
    def redirect_stderr():
        new = os.dup(2)  # Create a copy of stderr (new)
        sys.stderr = io.TextIOWrapper(os.fdopen(new, 'wb'))
        _file = tempfile.TemporaryFile(mode='w+t')
        os.dup2(_file.fileno(), 2)  # Redirect stdout into tmp


def run():
    # Explicitly changing the stdout encoding format
    if sys.stdout.encoding is None:
        # Output is redirected to a file
        sys.stdout = codecs.getwriter('latin-1')(sys.stdout)

    FileCrawler.redirect_stderr()

    o = FileCrawler()
    o.print_banner()

    try:
        o.main()

    except Exception as e:
        Color.pl('\n{!} {R}Error:{O} %s{W}' % str(e))

        if Configuration.verbose > 0 or True:
            Color.pl('\n{!} {O}Full stack trace below')
            from traceback import format_exc
            Color.p('\n{!}    ')
            err = format_exc().strip()
            err = err.replace('\n', '\n{W}{!} {W}   ')
            err = err.replace('  File', '{W}{D}File')
            err = err.replace('  Exception: ', '{R}Exception: {O}')
            Color.pl(err)

        Color.pl('\n{!} {R}Exiting{W}\n')

    except KeyboardInterrupt:
        Color.pl('\n{!} {O}interrupted, shutting down...{W}')

    Tools.exit_gracefully(2)
