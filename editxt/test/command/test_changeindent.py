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


import logging
import os
from contextlib import closing
from tempfile import gettempdir

from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, untested, check_app_state

import editxt.constants as const
from editxt.command.changeindent import ChangeIndentationController
from editxt.controls.textview import TextView
from editxt.document import TextDocumentView

log = logging.getLogger(__name__)


def test_ChangeIndentationController_load_options():
    m = Mocker()
    tv = m.mock(TextView)
    dv = tv.doc_view >> m.mock(TextDocumentView)
    mode = dv.indent_mode >> "<indent mode>"
    size = dv.indent_size >> "<indent size>"
    with m:
        ctl = ChangeIndentationController(tv) # calls load_options()
        opts = ctl.options
        eq_(opts.from_mode, mode)
        eq_(opts.from_size, size)
        eq_(opts.to_mode, mode)
        eq_(opts.to_size, size)
        
def test_ChangeIndentationController_save_options():
    m = Mocker()
    tv = m.mock(TextView)
    dv = tv.doc_view >> m.mock(TextDocumentView)
    with m.order():
        mode = dv.indent_mode >> "<indent mode>"
        size = dv.indent_size >> "<indent size>"
    with m:
        ctl = ChangeIndentationController(tv)
        ctl.save_options()

def test_ChangeIndentationController_execute_():
    m = Mocker()
    tv = m.mock(TextView)
    dv = m.mock(TextDocumentView)
    (tv.doc_view << dv).count(2)
    mode = dv.indent_mode >> "m"
    size = dv.indent_size >> "s"
    dv.change_indentation("m", "s", "m", "s", True)
    m.method(ChangeIndentationController.save_options)()
    m.method(ChangeIndentationController.cancel_)(None)
    with m:
        ctl = ChangeIndentationController(tv)
        ctl.execute_(None)
