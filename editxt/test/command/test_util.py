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
from mocker import Mocker, ANY
from AppKit import NSMakeRange, NSRange, NSTextStorage, NSTextView
#from Foundation import *
from editxt.test.util import eq_, TestConfig

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
    yield test, c(input="", output="")
    yield test, c(input="\r\n", output="\n")
    yield test, c(input="\n\r\n", output="\n\n")
    yield test, c(input="\r \n", output="\n \n")
    yield test, c(input="\r \n \u2028", output="\n \n \n")
    yield test, c(input="\r \r\n\n \u2028", output="\n \n\n \n")

def test_change_indentation():
    from editxt.document import TextDocument
    def test(c):
        if c.eol != "\n":
            c.input = c.input.replace("\n", c.eol)
            c.output = c.output.replace("\n", c.eol)
        result = []
        m = Mocker()
        tv = m.mock(NSTextView)
        reset = (c.new == "\t")
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
    c = TestConfig(old="  ", new="   ", size=4, sel=(0, 0))
    for mode in [
        const.NEWLINE_MODE_UNIX,
        const.NEWLINE_MODE_MAC,
        const.NEWLINE_MODE_WINDOWS,
        const.NEWLINE_MODE_UNICODE,
    ]:
        c = c(eol=const.EOLS[mode])
        yield test, c(old="  ", new="  ", input="", output="")
        yield test, c(old="\t", new="\t", input="", output="")
        c = c(old="  ", new="   ", size=3)
        yield test, c(input="", output="")
        yield test, c(input="  \n", output="   \n")
        yield test, c(input="  x\n", output="   x\n")
        yield test, c(input="   x\n", output="    x\n")
        yield test, c(input="    x\n", output="      x\n")
        yield test, c(input="    x    \n", output="      x    \n")
        yield test, c(input="  x\n    y\n", output="   x\n      y\n")
        c = c(old="  ", new="\t", size=3)
        yield test, c(input="", output="")
        yield test, c(input="  \n", output="\t\n")
        yield test, c(input="  x\n", output="\tx\n")
        yield test, c(input="   x\n", output="\t x\n")
        yield test, c(input="    x\n", output="\t\tx\n")
        yield test, c(input="    x    \n", output="\t\tx    \n")
        yield test, c(input="  x\n    y\n", output="\tx\n\t\ty\n", sel=(8, 2))
        yield test, c(input="  x\n    y\n", output="\tx\n\t\ty\n", sel=(6, 4))
        c = c(old="\t", new="   ", size=3)
        yield test, c(input="", output="")
        yield test, c(input="\t\n", output="   \n")
        yield test, c(input="\tx\n", output="   x\n")
        yield test, c(input="\t x\n", output="    x\n")
        yield test, c(input="\t\tx\n", output="      x\n")
        yield test, c(input="\t\tx\t\t\n", output="      x\t\t\n")
        yield test, c(input="\tx\n\t\ty\n", output="   x\n      y\n")

def test_calculate_indent_mode_and_size():
    TAB = const.INDENT_MODE_TAB
    SPACE = const.INDENT_MODE_SPACE
    program = """
'''
 x
 y
 z
'''

def foo(x=1, y=2):
    x = x or 1
    y = x or 2
    for i in range(x + y):
        n = i + x + y
        if i % 2 = 1:
            return y
    return x

if __name__ == "__main__":
    foo()
"""

    def test(mode, size, text):
        result = mod.calculate_indent_mode_and_size(text)
        eq_(result, (mode, size))

    yield test, None, None, "x\nx\nx\n"
    yield test, TAB, None, "x\n\tx\nx\n"
    yield test, SPACE, None, " x\nx\n"
    yield test, SPACE, 2, " x\n    \n  x\n"
    yield test, SPACE, 4, program
    yield test, SPACE, 4, program.replace(" foo()", "foo()")

    yield test, SPACE, 3, """
a
   b
   b
       c
       c
           d
           d
   b
       c
           d
"""
