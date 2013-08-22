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
from mocker import Mocker, ANY
from AppKit import NSMakeRange, NSRange, NSTextStorage, NSTextView
#from Foundation import *
from editxt.test.util import TestConfig

import editxt.constants as const
import editxt.command.util as mod
from editxt.command.parser import ArgumentError, CommandParser, Int, Options

def test_replace_newlines():
    def test(c):
        result = []
        m = Mocker()
        tv = m.mock(NSTextView)
        tv.string() >> c.input
        sel = tv.selectedRange() >> m.mock(NSRange)
        if c.input != c.output:
            rng = NSMakeRange(0, len(c.input))
            tv.shouldChangeTextInRange_replacementString_(rng, ANY) >> True
            ts = tv.textStorage() >> m.mock(NSTextStorage)
            ts.replaceCharactersInRange_withString_(rng, c.output)
            tv.didChangeText()
            tv.setSelectedRange_(sel)
        with m:
            mod.replace_newlines(tv, c.eol)
    c = TestConfig(eol=const.EOLS[const.NEWLINE_MODE_UNIX])
    yield test, c(input=u"", output=u"")
    yield test, c(input=u"\r\n", output=u"\n")
    yield test, c(input=u"\n\r\n", output=u"\n\n")
    yield test, c(input=u"\r \n", output=u"\n \n")
    yield test, c(input=u"\r \n \u2028", output=u"\n \n \n")
    yield test, c(input=u"\r \r\n\n \u2028", output=u"\n \n\n \n")

def test_change_indentation():
    from editxt.document import TextDocument
    def test(c):
        if c.eol != u"\n":
            c.input = c.input.replace(u"\n", c.eol)
            c.output = c.output.replace(u"\n", c.eol)
        result = []
        m = Mocker()
        tv = m.mock(NSTextView)
        reset = (c.new == u"\t")
        if c.old != c.new or reset:
            tv.string() >> c.input
            rng = NSMakeRange(0, len(c.input))
            tv.shouldChangeTextInRange_replacementString_(rng, c.output) >> True
            if reset:
                doc = tv.doc_view.document >> m.mock(TextDocument)
                doc.reset_text_attributes(c.size)
            if c.input != c.output:
                sel = tv.selectedRange() >> NSRange(*c.sel)
                ts = tv.textStorage() >> m.mock(NSTextStorage)
                ts.replaceCharactersInRange_withString_(rng, c.output)
                if sel.location > len(c.output):
                    sel = NSRange(len(c.output), 0)
                elif sel.location + sel.length > len(c.output):
                    sel = NSRange(sel.location, len(c.output) - sel.location)
                tv.setSelectedRange_(sel)
            tv.didChangeText()
        with m:
            mod.change_indentation(tv, c.old, c.new, c.size)
    c = TestConfig(old=u"  ", new=u"   ", size=4, sel=(0, 0))
    for mode in [
        const.NEWLINE_MODE_UNIX,
        const.NEWLINE_MODE_MAC,
        const.NEWLINE_MODE_WINDOWS,
        const.NEWLINE_MODE_UNICODE,
    ]:
        c = c(eol=const.EOLS[mode])
        yield test, c(old=u"  ", new=u"  ", input=u"", output=u"")
        yield test, c(old=u"\t", new=u"\t", input=u"", output=u"")
        c = c(old=u"  ", new=u"   ", size=3)
        yield test, c(input=u"", output=u"")
        yield test, c(input=u"  \n", output=u"   \n")
        yield test, c(input=u"  x\n", output=u"   x\n")
        yield test, c(input=u"   x\n", output=u"    x\n")
        yield test, c(input=u"    x\n", output=u"      x\n")
        yield test, c(input=u"    x    \n", output=u"      x    \n")
        yield test, c(input=u"  x\n    y\n", output=u"   x\n      y\n")
        c = c(old=u"  ", new=u"\t", size=3)
        yield test, c(input=u"", output=u"")
        yield test, c(input=u"  \n", output=u"\t\n")
        yield test, c(input=u"  x\n", output=u"\tx\n")
        yield test, c(input=u"   x\n", output=u"\t x\n")
        yield test, c(input=u"    x\n", output=u"\t\tx\n")
        yield test, c(input=u"    x    \n", output=u"\t\tx    \n")
        yield test, c(input=u"  x\n    y\n", output=u"\tx\n\t\ty\n", sel=(8, 2))
        yield test, c(input=u"  x\n    y\n", output=u"\tx\n\t\ty\n", sel=(6, 4))
        c = c(old=u"\t", new=u"   ", size=3)
        yield test, c(input=u"", output=u"")
        yield test, c(input=u"\t\n", output=u"   \n")
        yield test, c(input=u"\tx\n", output=u"   x\n")
        yield test, c(input=u"\t x\n", output=u"    x\n")
        yield test, c(input=u"\t\tx\n", output=u"      x\n")
        yield test, c(input=u"\t\tx\t\t\n", output=u"      x\t\t\n")
        yield test, c(input=u"\tx\n\t\ty\n", output=u"   x\n      y\n")
