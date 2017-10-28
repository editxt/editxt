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
from editxt.test.util import eq_, gentest, Regex, test_app

import editxt.command.python as mod


def test_doc():
    @gentest
    def test(code, output, command="python", select=(0, 0)):
        with test_app("window project(/) editor*") as app:
            editor = app.windows[0].current_editor
            editor.document.text = code
            class textview:
                def selectedRange():
                    return select
            editor.text_view = textview
            bar = CommandTester(mod.python, editor=editor, output=True)
            bar(command)
            eq_(bar.output, output)

    yield test("1 + 1", "2\n")
    yield test("print(1 + 1)", "2\n")
    yield test("  2 + 2", "4\n")
    yield test("  print('hi')\n  2 + 2\n", "hi\n4\n")
    yield test("""
        def f(x):
            return x
        """,
        "no output"
    )
    yield test("""
        (1
            + 2)
        """,
        "3\n"
    )
    yield test("""
        (1
            + 2)
        # comment
        """,
        "3\n"
    )
    yield test("""
        x = 4
        y = 1;x + y
        """,
        "5\n"
    )
    yield test("""
        print "not with python 3"
        """,
        Regex("SyntaxError"),
    )
