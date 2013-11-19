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
import logging
import objc
from PyObjCTools import AppHelper, Debugging

from editxt.platform.mac.errors import install_exception_handler
# TODO move Cocoa specific part of valuetrans (all of it?) into platform.mac
from editxt.valuetrans import register_value_transformers

log = logging.getLogger(__name__)

def init(use_pdb):
    if use_pdb:
        objc.setVerbose(1)
        # make PyObjC use our exception handler
        Debugging.installExceptionHandler = install_exception_handler
    else:
        install_exception_handler()

    # HACK monkey-patch pyobc exception handler to use our logger
    Debugging.NSLog = lambda x, y=None: log.error(x if y is None else y)


def run(app, argv, unexpected_error_callback, use_pdb):
    # initialize class definitions
    import editxt.controls.cells
    import editxt.controls.linenumberview
    import editxt.controls.outlineview
    import editxt.controls.splitview
    import editxt.controls.textview
    import editxt.controls.window

    register_value_transformers()

    AppHelper.runEventLoop(argv, unexpected_error_callback, pdb=use_pdb)
