# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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
from editxt.test.test_commands import CommandTester
from editxt.test.util import assert_raises, eq_, gentest, TestConfig, test_app

import editxt.command.docnav as mod


def test_doc():
    CONFIG = """
        window
            project
                editor(A)
                editor(B)
                editor(C)
                editor(D)
                editor(E)
    """
    BEEP = object()
    @gentest
    def test(command, focus, recent="DEBAC", back=0):
        with test_app(CONFIG) as app:
            tapp = test_app(app)
            for doc in recent:
                app.windows[0].current_editor = tapp.get("editor(%s)" % doc)
            editor = app.windows[0].current_editor
            bar = CommandTester(mod.doc, editor=editor)
            bar(command)
            state = CONFIG.split()
            def f(item):
                return (item + '*') if focus in item else item
            eq_(tapp.state, ' '.join([f(item) for item in state]))

    yield test("doc", "A")
    yield test("doc back", "A")
    yield test("doc back 2", "B")
#    yield test("doc front", BEEP)
#    yield test("doc front", "A", back=2)
#    yield test("doc front", "C", back=1)
    yield test("doc up", "B")
    yield test("doc down", "D")
