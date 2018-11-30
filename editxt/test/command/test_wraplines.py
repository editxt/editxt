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

from mocker import Mocker
from editxt.test.util import eq_, TestConfig, test_app

import editxt.command.base as base
import editxt.command.wraplines as mod
import editxt.constants as const
from editxt.command.wraplines import (WrapLinesController,
    wrap_selected_lines, wraplines)
from editxt.platform.text import Text

log = logging.getLogger(__name__)


def test_wrap_to_margin_guide():
    m = Mocker()
    editor = m.mock()
    wrap = m.replace(mod, 'wrap_selected_lines')
    wrap(editor, mod.Options(wrap_column=const.DEFAULT_RIGHT_MARGIN, indent=True))
    with m:
        mod.wrap_at_margin(editor, None)


def test_WrapLinesController_default_options():
    with test_app() as app:
        editor = base.Options(app=app)
        ctl = WrapLinesController(editor)
        eq_(ctl.options._target, mod.Options(
            wrap_column=const.DEFAULT_RIGHT_MARGIN,
            indent=True,
        ))


def test_WrapLinesController_wrap_():
    with test_app() as app:
        m = Mocker()
        editor = base.Options(app=app)
        cmd = m.replace(mod, 'wrap_selected_lines')
        ctl = WrapLinesController(editor)
        cmd(editor, ctl.options)
        m.method(ctl.save_options)()
        m.method(ctl.cancel_)(None)
        with m:
            ctl.wrap_(None)


def test_wrap_selected_lines():
    def test(c):
        m = Mocker()
        opts = "<options>"
        editor = m.mock()
        wrap = m.replace(mod, 'wraplines')
        iterlines = m.replace("editxt.command.wraplines.iterlines")
        text = Text(c.text)
        (editor.text << text).count(2)
        sel = (0, len(text)) if c.sel is None else c.sel
        sel = text.line_range(editor.selection >> sel)
        eol = editor.document.eol >> m.mock()
        tok = editor.document.comment_token >> "x"
        lines = iterlines(text, sel) >> "<lines>"
        eol.join(wrap(lines, opts, tok) >> [c.result]) >> c.result
        output = []

        def callback(text, range, select):
            output.append(text)
        (editor.put(c.result, sel, select=True) << True).call(callback)
        with m:
            wrap_selected_lines(editor, opts)
            eq_(c.result, output[0])
    c = TestConfig(col=30, ind=False, sel=None)
    yield test, c(text="Hello world", result="Hello world")
    yield test, c(text="Hello\nworld", result="Hello", sel=(0, 5))


def test_wraplines():
    from editxt.command.util import iterlines

    def test(c):
        opts = TestConfig(wrap_column=c.wid, indent=c.ind)
        text = Text(c.text)
        sel = (0, len(c.text))
        ctok = c.comment if c.ind else None
        output = "\n".join(wraplines(iterlines(text, sel), opts, ctok))
        eq_(output, c.result)
    c = TestConfig(ind=False)
    yield test, c(text="", result="\n", wid=80)
    yield test, c(text="\n", result="\n", wid=80)
    yield test, c(text="Hello world", result="Hello\nworld\n", wid=1)
    yield test, c(text="Hello world", result="Hello\nworld\n", wid=4)
    yield test, c(text="Hello world", result="Hello\nworld\n", wid=5)
    yield test, c(text="Hello world", result="Hello\nworld\n", wid=6)
    yield test, c(text="Hello world", result="Hello\nworld\n", wid=10)
    yield test, c(text="Hello world", result="Hello world\n", wid=11)
    yield test, c(text="Hello\nworld", result="Hello\nworld\n", wid=10)
    yield test, c(text="Hello\nworld", result="Hello world\n", wid=11)
    yield test, c(text="  Hello world", result="  Hello\nworld\n", wid=6)
    yield test, c(text="  Hello world", result="  Hello\nworld\n", wid=7)
    yield test, c(text="  Hello world", result="  Hello\nworld\n", wid=8)
    yield test, c(text="  Hello world\n", result="  Hello\nworld\n", wid=6)
    yield test, c(text="\n  Hello world", result="\n  Hello\nworld\n", wid=6)
    yield test, c(text="Hello  world", result="Hello\nworld\n", wid=5)
    yield test, c(text="Hello  world", result="Hello\nworld\n", wid=6)
    yield test, c(text="Hello  world", result="Hello\nworld\n", wid=7)
    yield test, c(text="Hello  world", result="Hello\nworld\n", wid=8)
    yield test, c(text="Hello  world", result="Hello  world\n", wid=12)
    yield test, c(text="Hi      world", result="Hi\nworld\n", wid=7)
    yield test, c(text="Hi      world", result="Hi world\n", wid=8)
    yield test, c(text="Hi      world", result="Hi world\n", wid=9)
    yield test, c(text="Hi      my friend", result="Hi my\nfriend\n", wid=9)
    yield test, c(text="abc def ghi\nmno pqr stu\n",
                result="abc def\nghi mno\npqr stu\n", wid=7)

    yield test, c(text="      abc def ghi", result="      abc\ndef\nghi\n", wid=5)
    yield test, c(text="      abc def ghi", result="      abc\ndef\nghi\n", wid=6)
    yield test, c(text="      abc def ghi", result="      abc\ndef ghi\n", wid=7)
    yield test, c(text="abc\n\ndef ghi", result="abc\n\ndef\nghi\n", wid=6)
    yield test, c(text="abc\n\ndef ghi", result="abc\n\ndef ghi\n", wid=7)
    yield test, c(text="abc\n\ndef ghi", result="abc\n\ndef ghi\n", wid=8)
    yield test, c(text="abc\n\n def ghi", result="abc\n\ndef ghi\n", wid=8)
    yield test, c(text="abc\n \ndef ghi", result="abc\n\ndef\nghi\n", wid=6)
    yield test, c(text="abc\n \ndef ghi", result="abc\n\ndef ghi\n", wid=7)
    yield test, c(text="abc\n \ndef ghi", result="abc\n\ndef ghi\n", wid=8)
    yield test, c(text="abc\n\n\ndef ghi", result="abc\n\n\ndef ghi\n", wid=8)

    c = c(ind=True, comment="#")
    yield test, c(text="  Hello world", result="  Hello\n  world\n", wid=1)
    yield test, c(text="  Hello world", result="  Hello\n  world\n", wid=6)
    yield test, c(text="  Hello world", result="  Hello\n  world\n", wid=7)
    yield test, c(text="  Hello world", result="  Hello\n  world\n", wid=8)
    yield test, c(text="  Hello world\n", result="  Hello\n  world\n", wid=6)
    yield test, c(text="  Hello world, hi\n", result="  Hello\n  world,\n  hi\n", wid=9)
    yield test, c(text="  Hello world, hi\n", result="  Hello\n  world,\n  hi\n", wid=10)
    yield test, c(text="  Hello world, hi\n", result="  Hello\n  world, hi\n", wid=11)

    for comment in ("#", "//", "xxx"):
        def d(text, result, wid, **kw):
            ln = len(comment) - 1
            return c(
                text=text.replace("#", comment),
                result=result.replace("#", comment),
                wid=wid + ln,
                comment=comment,
                **kw
            )
        yield test, d(text="  # abc def", result="  # abc def\n", wid=11)
        yield test, d(text="  # abc def", result="  # abc\n  # def\n", wid=10)
        yield test, d(text="  # abc\n  # def\n", result="  # abc def\n", wid=11)
        yield test, d(text="  # abc\n  # def\n  # ghi\n",
                    result="  # abc def\n  # ghi\n", wid=11)
        yield test, d(text="  # abc\n  # def\n  # ghi\n",
                    result="  # abc\n  # def\n  # ghi\n", wid=10)
        yield test, d(text="  # abc\n\n  # def ---\n",
                    result="  # abc\n  # \n  # def ---\n", wid=11)
        yield test, d(text="  # abc\n\n\n  # def ---\n",
                    result="  # abc\n  # \n  # \n  # def ---\n", wid=11)
