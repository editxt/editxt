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
from __future__ import with_statement

import logging
import os
from contextlib import closing
from tempfile import gettempdir

from AppKit import *
from Foundation import *
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from test_editxt.util import TestConfig, untested, check_app_state

import editxt.constants as const
from editxt.controls.textview import TextView
from editxt.wraplines import WrapLinesController, wrap_selected_lines, wraplines

log = logging.getLogger("test_editxt.test_wraplines")


def test_WrapLinesController_wrap_():
    m = Mocker()
    cmd = m.replace(wrap_selected_lines)
    tv = m.mock(TextView)
    ctl = WrapLinesController.create_with_textview(tv)
    cmd(tv, ctl.opts)
    m.method(ctl.save_options)()
    m.method(ctl.cancel_)(None)
    with m:
        ctl.wrap_(None)

def test_wrap_selected_lines():
    def test(c):
        m = Mocker()
        opts = "<options>"
        tv = m.mock(TextView)
        ts = tv.textStorage() >> m.mock(NSTextStorage)
        wrap = m.replace(wraplines)
        iterlines = m.replace("editxt.wraplines.iterlines")
        text = tv.string() >> NSString.stringWithString_(c.text)
        sel = (0, len(text)) if c.sel is None else c.sel
        sel = text.lineRangeForRange_(tv.selectedRange() >> sel)
        eol = tv.doc_view.document.eol >> m.mock()
        lines = iterlines(text, sel) >> "<lines>"
        eol.join(wrap(lines, opts, tv) >> [c.result]) >> c.result
        tv.shouldChangeTextInRange_replacementString_(sel, c.result) >> True
        output = []
        def callback(range, text):
            output.append(text)
        expect(ts.replaceCharactersInRange_withString_(sel, c.result)).call(callback)
        tv.didChangeText()
        tv.setSelectedRange_((sel[0], len(c.result)))
        with m:
            wrap_selected_lines(tv, opts)
            eq_(c.result, output[0])
    c = TestConfig(col=30, ind=False, sel=None)
    yield test, c(text=u"Hello world", result=u"Hello world")
    yield test, c(text=u"Hello\nworld", result=u"Hello", sel=(0, 5))

def test_wraplines():
    from editxt.wraplines import iterlines
    def test(c):
        m = Mocker()
        tv = m.mock(TextView)
        if c.ind:
            tv.doc_view.document.comment_token >> c.comment
        opts = TestConfig(wrap_column=c.wid, indent=c.ind)
        text = NSString.stringWithString_(c.text)
        sel = (0, len(c.text))
        if c._get("debug", False):
            import pdb; pdb.set_trace()
        with m:
            output = "\n".join(wraplines(iterlines(text, sel), opts, tv))
            eq_(c.result, output)
    c = TestConfig(wid=30, ind=False, sel=None, comment="#")
    yield test, c(text=u"Hello world", result=u"Hello\nworld\n", wid=1)
    yield test, c(text=u"Hello world", result=u"Hello\nworld\n", wid=4)
    yield test, c(text=u"Hello world", result=u"Hello\nworld\n", wid=5)
    yield test, c(text=u"Hello world", result=u"Hello\nworld\n", wid=6)
    yield test, c(text=u"Hello world", result=u"Hello\nworld\n", wid=10)
    yield test, c(text=u"Hello world", result=u"Hello world\n", wid=11)
    yield test, c(text=u"Hello\nworld", result=u"Hello\nworld\n", wid=10)
    yield test, c(text=u"Hello\nworld", result=u"Hello world\n", wid=11)
    yield test, c(text=u"  Hello world", result=u"  Hello\nworld\n", wid=6)
    yield test, c(text=u"  Hello world", result=u"  Hello\nworld\n", wid=7)
    yield test, c(text=u"  Hello world", result=u"  Hello\nworld\n", wid=8)
    yield test, c(text=u"  Hello world\n", result=u"  Hello\nworld\n", wid=6)
    yield test, c(text=u"\n  Hello world", result=u"\n  Hello\nworld\n", wid=6)
    yield test, c(text=u"Hello  world", result=u"Hello\nworld\n", wid=5)
    yield test, c(text=u"Hello  world", result=u"Hello\nworld\n", wid=6)
    yield test, c(text=u"Hello  world", result=u"Hello\nworld\n", wid=7)
    yield test, c(text=u"Hello  world", result=u"Hello\nworld\n", wid=8)
    yield test, c(text=u"Hello  world", result=u"Hello  world\n", wid=12)
    yield test, c(text=u"Hi      world", result=u"Hi\nworld\n", wid=7)
    yield test, c(text=u"Hi      world", result=u"Hi world\n", wid=8)
    yield test, c(text=u"Hi      world", result=u"Hi world\n", wid=9)
    yield test, c(text=u"Hi      my friend", result=u"Hi my\nfriend\n", wid=9)
    yield test, c(text=u"abc def ghi\nmno pqr stu\n",
                result=u"abc def\nghi mno\npqr stu\n", wid=7)

    yield test, c(text=u"      abc def ghi", result=u"      abc\ndef\nghi\n", wid=5)
    yield test, c(text=u"      abc def ghi", result=u"      abc\ndef\nghi\n", wid=6)
    yield test, c(text=u"      abc def ghi", result=u"      abc\ndef ghi\n", wid=7)
    yield test, c(text=u"abc\n\ndef ghi", result=u"abc\n\ndef\nghi\n", wid=6)
    yield test, c(text=u"abc\n\ndef ghi", result=u"abc\n\ndef ghi\n", wid=7)
    yield test, c(text=u"abc\n\ndef ghi", result=u"abc\n\ndef ghi\n", wid=8)
    yield test, c(text=u"abc\n\n def ghi", result=u"abc\n\ndef ghi\n", wid=8)
    yield test, c(text=u"abc\n \ndef ghi", result=u"abc\n\ndef\nghi\n", wid=6)
    yield test, c(text=u"abc\n \ndef ghi", result=u"abc\n\ndef ghi\n", wid=7)
    yield test, c(text=u"abc\n \ndef ghi", result=u"abc\n\ndef ghi\n", wid=8)
    yield test, c(text=u"abc\n\n\ndef ghi", result=u"abc\n\n\ndef ghi\n", wid=8)

    c = c(ind=True)
    yield test, c(text=u"  Hello world", result=u"  Hello\n  world\n", wid=1)
    yield test, c(text=u"  Hello world", result=u"  Hello\n  world\n", wid=6)
    yield test, c(text=u"  Hello world", result=u"  Hello\n  world\n", wid=7)
    yield test, c(text=u"  Hello world", result=u"  Hello\n  world\n", wid=8)
    yield test, c(text=u"  Hello world\n", result=u"  Hello\n  world\n", wid=6)
    yield test, c(text=u"  Hello world, hi\n", result=u"  Hello\n  world,\n  hi\n", wid=9)
    yield test, c(text=u"  Hello world, hi\n", result=u"  Hello\n  world,\n  hi\n", wid=10)
    yield test, c(text=u"  Hello world, hi\n", result=u"  Hello\n  world, hi\n", wid=11)

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
        yield test, d(text=u"  # abc def", result=u"  # abc def\n", wid=11)
        yield test, d(text=u"  # abc def", result=u"  # abc\n  # def\n", wid=10)
        yield test, d(text=u"  # abc\n  # def\n", result=u"  # abc def\n", wid=11)
        yield test, d(text=u"  # abc\n  # def\n  # ghi\n",
                    result=u"  # abc def\n  # ghi\n", wid=11)
        yield test, d(text=u"  # abc\n  # def\n  # ghi\n",
                    result=u"  # abc\n  # def\n  # ghi\n", wid=10)
        yield test, d(text=u"  # abc\n\n  # def ---\n",
                    result=u"  # abc\n  # \n  # def ---\n", wid=11)
