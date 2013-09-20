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
from __future__ import with_statement

import logging
import os
import re
from contextlib import closing
from tempfile import gettempdir

from AppKit import *
from Foundation import *
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import TestConfig, untested, check_app_state

import editxt.command.base as base
import editxt.command.sortlines as mod
import editxt.constants as const
from editxt.command.sortlines import SortLinesController, SortOptions, sortlines
from editxt.command.parser import RegexPattern
from editxt.controls.textview import TextView
from editxt.test.command.test_base import replace_history
from editxt.test.test_commands import CommandTester

log = logging.getLogger(__name__)

TEXT = u"""
ghi 1 2 012
abc 3 1 543
 de 2 1 945
Jkl 4 1 246
    
"""

def test_sort_command():
    def test(command, expected):
        m = Mocker()
        tv = FakeTextView(TEXT)
        do = CommandTester(mod.sort_lines, textview=tv)
        with m:
            do(command)
            eq_(sort_result(tv.text), unicode(expected), TEXT)

    yield test, "sort", "|0gadJ|4|0"
    yield test, "sort all", "|0|4dagJ|0"
    yield test, "sort all   match-case", "|0|4dJag|0"

def test_SortLinesController_default_options():
    with replace_history() as history:
        ctl = SortLinesController(None)
        for name, value in SortOptions.DEFAULTS.iteritems():
            eq_(getattr(ctl.options, name), value, name)

def test_SortLinesController_load_options():
    def test(hist, opts):
        with replace_history() as history:
            history.append("sort", hist)
            ctl = SortLinesController(None)
            eq_(ctl.options._target, SortOptions(**opts))

    yield test, "sort", {}
    yield test, "sort all", {"selection": False}
    yield test, "sort  rev ignore-leading ignore-case /(\d+)([a-z]+)/\2\1/i", {
        "reverse": True,
        "ignore_leading_whitespace": True,
        "ignore_case": True,
        "search_pattern": RegexPattern("(\d+)([a-z]+)"),
        "match_pattern": "\2\1",
    }
    yield test, "sort /(\d+)([a-z]+)/\2\1/i", {
        "search_pattern": RegexPattern("(\d+)([a-z]+)"),
        "match_pattern": "\2\1",
    }

def test_SortLinesController_sort_():
    m = Mocker()
    sort = m.replace(mod, 'sortlines')
    tv = m.mock(TextView)
    with replace_history() as history:
        slc = SortLinesController(tv)
        sort(tv, slc.options)
        m.method(slc.save_options)()
        m.method(slc.cancel_)(None)
        with m:
            slc.sort_(None)

def test_sortlines():
    optmap = [
        ("sel", "selection"),
        ("rev", "reverse"),
        ("ign", "ignore_leading_whitespace"),
        ("icase", "ignore_case"),
        ("num", "numeric_match"),
        ("reg", "regex_sort"),
        ("sch", "search_pattern"),
        ("mch", "match_pattern"),
    ]
    def test(c):
        opts = SortOptions(**{opt: c.opts[abbr]
            for abbr, opt in optmap if abbr in c.opts})
        m = Mocker()
        tv = m.mock(TextView)
        ts = tv.textStorage() >> m.mock(NSTextStorage)
        text = tv.string() >> NSString.stringWithString_(c.text)
        if opts.selection:
            sel = tv.selectedRange() >> c.sel
            sel = text.lineRangeForRange_(sel)
        else:
            sel = c.sel
        tv.shouldChangeTextInRange_replacementString_(sel, ANY) >> True
        output = []
        def callback(range, text):
            output.append(text)
        expect(ts.replaceCharactersInRange_withString_(sel, ANY)).call(callback)
        tv.didChangeText()
        if opts.selection:
            tv.setSelectedRange_(sel)
        with m:
            sortlines(tv, opts)
            eq_(sort_result(output[0]), unicode(c.result), output[0])
    op = TestConfig()
    tlen = len(TEXT)
    c = TestConfig(text=TEXT, sel=(0, tlen), opts=op)
    yield test, c(result="|0|4dagJ|0")
    yield test, c(result="|0|4adgJ|0", opts=op(ign=True))
    yield test, c(result="|0|4dJag|0", opts=op(icase=False))
    yield test, c(result="|0|4Jadg|0", opts=op(icase=False, ign=True))
    yield test, c(result="dag|0", opts=op(sel=True), sel=(5, 32))
    yield test, c(result="adg|0", opts=op(sel=True, ign=True), sel=(5, 32))
    yield test, c(result="Jgad|4|0|0", opts=op(rev=True))
    
    op = op(reg=True, sch=r"\d")
    yield test, c(result="|0|4dagJ|0", opts=op(reg=False))
    yield test, c(result="gdaJ|0|4|0", opts=op)
    yield test, c(result="daJg|0|4|0", opts=op(sch="(\d) (\d)", mch=r"\2\1"))
    # TODO test and implement numeric match (checkbox is currently hidden)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# test helpers

def sort_result(value):
    def ch(line):
        value = line.lstrip(" ")
        return value[0] if value else "|%i" % len(line)
    return "".join(ch(line) for line in value.split("\n"))

class FakeTextView(object):

    def __init__(self, text, sel=NSMakeRange(0, 0)):
        self.text = text
        self.sel = sel

    def selectedRange(self):
        return self.sel

    def setSelectedRange_(self, sel):
        self.sel = sel

    def string(self):
        return NSString.alloc().initWithString_(self.text)

    def shouldChangeTextInRange_replacementString_(self, rng, str):
        return True

    def textStorage(self):
        return self

    def replaceCharactersInRange_withString_(self, rng, string):
        end = rng[0] + rng[1]
        self.text = self.text[:rng[0]] + string + self.text[end:]

    def didChangeText(self):
        pass
