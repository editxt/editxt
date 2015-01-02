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
from functools import partial

from editxt.test.test_commands import CommandTester
from editxt.test.util import (assert_raises, eq_, expect_beep, gentest,
    TestConfig, test_app)

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
    def test(command, focus, recent="DEBAC", prev=0, _config=CONFIG):
        with test_app(_config) as app:
            tapp = test_app(app)
            for doc in recent:
                app.windows[0].current_editor = tapp.get("editor(%s)" % doc)
            editor = app.windows[0].current_editor
            bar = CommandTester(mod.doc, editor=editor)
            if prev:
                bar("doc  previous %s" % prev)
            with expect_beep(focus is BEEP):
                bar(command)
                if focus is BEEP:
                    focus = recent[-1]
                state = _config.split()
                def f(item):
                    return (item + '*') if focus in item else item
                eq_(tapp.state, ' '.join([f(item) for item in state]))

    yield test("doc A", "A")
    yield test("doc E", "E")
    yield test("doc X", BEEP)

    yield test("doc", "A")
    yield test("doc  previous", "A")
    yield test("doc  previous 2", "B")
    yield test("doc  previous 3", "E")
    yield test("doc  previous 4", "D")
    yield test("doc  previous 5", BEEP)
    yield test("doc  next", BEEP)
    yield test("doc  next", "A", prev=2)
    yield test("doc  next", "C", prev=1)
    yield test("doc  up", "B")
    yield test("doc  up 2", "A")
    yield test("doc  up 3", "project")
    yield test("doc  up 4", BEEP)
    yield test("doc  down", "D")
    yield test("doc  down 2", "E")
    yield test("doc  down 3", BEEP)

    test = partial(test, recent=["/work/src/file"], _config="""
        window
            project(work:/work)
                editor(/work/src/file)
                editor(/work/dst/file)
            project(play:/play)
                editor(/play/file)
                editor(new)
    """)
    yield test("doc file::dst", "/work/dst/file")
    yield test("doc work", "work:/work")
    yield test("doc new", BEEP)
    yield test("doc play file", "/play/file")

def test_config_shortcuts():
    from editxt.config import config_schema
    eq_({f.default for f in config_schema()["shortcuts"].values()
                   if f.default.startswith("doc ")},
        {'doc  previous', 'doc  next', 'doc  up', 'doc  down'})
