# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
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
from copy import deepcopy

import docopt

import editxt
import editxt.platform as platform

log = logging.getLogger(__name__)

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'brief': {'format': '%(levelname).7s %(name)s - %(message)s'},
    },
    'handlers': {
        'console': {
            'class': 'editxt.platform.console_log_handler',
            'level': 'ERROR',
            'formatter': 'brief',
        },
    },
    'loggers': {
        'editxt': {'level': 'DEBUG'},
        'editxt.test': {'level': 'DEBUG'},
        'editxt.util': {'level': 'INFO'},
    },
    'root': {'handlers': ['console']},
    'disable_existing_loggers': False,
}


def main(argv=list(sys.argv)):
    logging_config = deepcopy(DEFAULT_LOGGING_CONFIG)
    try:
        if "--test" in argv or "--pdb" in argv:
            logging_config['handlers']['console']['level'] = 'DEBUG'

        use_pdb = "--pdb" in argv
        if use_pdb:
            argv.remove("--pdb")

        platform_ = "test" if "--test" in argv else "mac"
        platform.init(platform_, use_pdb)

        if "--test" in argv:
            from editxt.test.runner import TestApplication
            app = TestApplication(argv)
        else:
            logging.config.dictConfig(logging_config)
            from editxt.application import Application
            argv = [a for a in argv if not a.startswith("-psn")] # OS X < 10.9 hack
            argv = argv[1:] # drop program name
            doc = __doc__.replace('Profile directory.',
                'Profile directory [default: {}].'
                .format(Application.default_profile()))
            opts = docopt.docopt(doc, argv, version=editxt.__version__)
            app = Application(opts.get('--profile'))

        with app.logger() as errlog:
            from editxt.platform.main import run
            run(app, argv, errlog.unexpected_error, use_pdb)
    except Exception as err:
        exc_info = sys.exc_info()
        if not logging.root.handlers:
            logging.config.dictConfig(logging_config)
        log.error('unhandled error', exc_info=exc_info)
        sys.exit(1)
