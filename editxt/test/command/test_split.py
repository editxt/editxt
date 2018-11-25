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
from nose.tools import eq_
from editxt.test.test_commands import CommandTester
from editxt.test.util import gentest, test_app

import editxt.command.split as mod


def test_split_text():
    @gentest
    @test_app("editor*")
    def test(app, text, result, pattern=None, sel=None, call=False):
        command = ["split"]
        if pattern is not None:
            command.append(pattern)
        editor = app.windows[0].current_editor
        editor.document.text = text
        if sel is None:
            sel = (0, len(text))
        bar = CommandTester(mod.split_text, editor=editor, sel=sel)
        if call:
            mod.split_text(editor, None)
        else:
            bar(" ".join(command))
        eq_(editor.document.text, result)

    yield test(text="", result="\n")
    yield test(text="\n", result="\n")
    yield test(text="Hello world", result="Hello\nworld\n")
    yield test(text="Hello\nworld", result="Hello\nworld\n")
    yield test(text="Hello  world", result="Hello\nworld\n")
    yield test(text="Hi      world", result="Hi\nworld\n")
    yield test(text="  Hello world", result="  Hello\n  world\n")
    yield test(text="  Hello world\n", result="  Hello\n  world\n")
    yield test(text="  Hello world, hi\n", result="  Hello\n  world,\n  hi\n")
    yield test(text="abc def ghi\nmno pqr stu\n",
             result="abc\ndef\nghi\nmno\npqr\nstu\n")
    yield test(text="abc\n\ndef ghi", result="abc\ndef\nghi\n")
    yield test(text="abc\n\n def ghi", result="abc\ndef\nghi\n")
    yield test(text="abc\n \ndef ghi", result="abc\ndef\nghi\n")
    yield test(text="abc\n\n\ndef ghi", result="abc\ndef\nghi\n")

    yield test(text="abc def\nghi mno pqr\nstu vwx\n", sel=(8, 0),
             result="abc def\nghi\nmno\npqr\nstu vwx\n")
    yield test(text="abc def\nghi mno pqr\nstu vwx\n", sel=(13, 0),
             result="abc def\nghi\nmno\npqr\nstu vwx\n")
    yield test(text="abc def\nghi mno pqr\nstu vwx\n", sel=(12, 7),
             result="abc def\nghi\nmno\npqr\nstu vwx\n")
    yield test(text="abc def\nghi mno pqr\nstu vwx\n", sel=(12, 9),
             result="abc def\nghi\nmno\npqr\nstu\nvwx\n")

    yield test(text="Hello world", result="Hello \norld\n", pattern=r"'w'")

    yield test(text="abc def\nghi mno pqr\nstu vwx\n", sel=(8, 0),
             result="abc def\nghi\nmno\npqr\nstu vwx\n", call=True)
