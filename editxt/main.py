# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2012 Daniel Miller <millerdev@gmail.com>
#
# This file is part of EditXT, a programmer's text editor for Mac OS X,
# which can be found at http://editxt.org/.
#
# EditXT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# EditXT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with EditXT.  If not, see <http://www.gnu.org/licenses/>.
"""
EditXT - Programmers text editor

Usage:
    xt [--profile=DIR]
    xt -h | --help
    xt --version

Options:
    -h --help       Show this help screen.
    --version       Show version.
    --profile=DIR   Profile directory.
"""
import logging.config
import os
import sys

import docopt
import objc
from PyObjCTools import AppHelper

import editxt
import editxt.hacks
from editxt.errorlog import errlog

docopt.exit = sys.exit # Fix for Python 2
log = logging.getLogger(__name__)

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'brief': {'format': '%(levelname).7s %(name)s - %(message)s'},
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'brief',
        },
        'logview': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'brief',
            'stream': 'ext://editxt.errorlog.errlog',
        },
    },
    'loggers': {
        'editxt': {'level': 'DEBUG'},
        'editxt.test': {'level': 'DEBUG'},
        'editxt.util': {'level': 'INFO'},
    },
    'root': {'handlers': ['console', 'logview']},
    'disable_existing_loggers': False,
}


def run(app, argv, use_pdb):
    # TODO move into PyObjC-specific application init
    # initialize class definitions
    import editxt.controls.cells
    import editxt.controls.linenumberview
    import editxt.controls.outlineview
    import editxt.controls.splitview
    import editxt.controls.textview
    import editxt.controls.window
    import editxt.application
    import editxt.editor
    import editxt.project
    import editxt.document
    import editxt.findpanel

    AppHelper.runEventLoop(argv, errlog.unexpected_error, pdb=use_pdb)


def main(argv=sys.argv[1:]):
    try:
        if "--test" in argv or "--pdb" in argv:
            DEFAULT_LOGGING_CONFIG['handlers']['console']['level'] = 'DEBUG'

        use_pdb = "--pdb" in argv
        if use_pdb:
            argv.remove("--pdb")
            objc.setVerbose(1)

        if "--test" in argv:
            from editxt.test.runner import TestApplication
            app = TestApplication(argv)
        else:
            logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
            from editxt.application import Application
            doc = __doc__.replace('Profile directory.',
                'Profile directory [default: {}].'
                .format(Application.default_profile()))
            opts = docopt.docopt(doc, argv, version=editxt.__version__)
            app = Application(opts['--profile'])

        editxt.app = app
        run(app, argv, use_pdb)
    except Exception as err:
        if len(logging.root.handlers) == 0:
            logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
        log.error('unhandled error', exc_info=True)
        sys.exit(1)
