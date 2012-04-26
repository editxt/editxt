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
import os
import sys

import objc
from PyObjCTools import AppHelper

import editxt
import editxt.hacks
from editxt.errorlog import ErrorLog

errlog = ErrorLog.log()
log = logging.getLogger("editxt")

def setup_logging():
    root = logging.getLogger('')
    format = logging.Formatter('%(name)s %(levelname)s - %(message)s')

    if "--test" in sys.argv or "--pdb" in sys.argv:
        console_level = logging.DEBUG
    else:
        console_level = logging.ERROR
    console = logging.StreamHandler()
    console.setLevel(console_level)
    console.setFormatter(format)
    root.addHandler(console)

    stream = logging.StreamHandler(errlog)
    stream.setLevel(logging.INFO)
    stream.setFormatter(format)
    root.addHandler(stream)

    logging.getLogger("editxt").setLevel(logging.DEBUG)
    logging.getLogger("editxt.util").setLevel(logging.INFO)
    logging.getLogger("test_editxt").setLevel(logging.DEBUG)

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
    setup_logging()
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
