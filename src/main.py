# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
import logging
import logging.config
import os
import sys

import objc
from PyObjCTools import AppHelper

import editxt
import editxt.hacks
from editxt.errorlog import errlog

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
        'editxt.util': {'level': 'INFO'},
        'test_editxt': {'level': 'DEBUG'},
    },
    'root': {'handlers': ['console', 'logview']},
    'disable_existing_loggers': False,
}

def setup(nib_path=None):
    import editxt.application
    editxt.app = editxt.application.Application()

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

class CommandArgs(object):
    def __init__(self, argv):
        self.argv = list(argv)
    def pop(self, name, default=False):
        if name in self.argv:
            self.argv.remove(name)
            return True
        return default

def main():
    if "--test" in sys.argv or "--pdb" in sys.argv:
        DEFAULT_LOGGING_CONFIG['handlers']['console']['level'] = 'DEBUG'
    logging.config.dictConfig(DEFAULT_LOGGING_CONFIG)
    setup()
    argv = list(sys.argv)
    use_pdb = "--pdb" in argv
    if use_pdb:
        argv.remove("--pdb")
        objc.setVerbose(1)
    if "--test" in argv:
        import noserunner
        sys.exit(not noserunner.run(argv))
    else:
        AppHelper.runEventLoop(argv, errlog.unexpected_error, pdb=use_pdb)

if __name__ == '__main__':
    main()
