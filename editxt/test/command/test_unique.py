# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2016 Daniel Miller <millerdev@gmail.com>
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

from editxt.test.command import FakeTextView
from editxt.test.util import TestConfig, untested, check_app_state, test_app

import editxt.command.unique as mod
from testil import eq_
from editxt.test.test_commands import CommandTester

log = logging.getLogger(__name__)

TEXT = """
mocker
nose
editxt.test
editxt.test
editxt.command
editxt.command
editxt
editxt.command
editxt.command
editxt.platform
editxt.test
"""

UNIQUE = """
mocker
nose
editxt.test
editxt.command
editxt
editxt.platform
"""

def test_unique_command():
    def test(command, expected, selection=(0, 0), sel_after=None):
        tv = FakeTextView(TEXT, selection)
        do = CommandTester(mod.unique_lines, textview=tv)
        do(command)
        eq_(tv.text, expected, tv.text)
        if sel_after is not None:
            eq_(do.editor.selection, sel_after)

    yield test, "unique", UNIQUE
    yield test, "unique selection", \
        TEXT[:13] + UNIQUE[13:47] + TEXT[89:], (13, 76), (13, 34)
