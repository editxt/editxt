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
from editxt.test.util import TestConfig, untested, check_app_state

import editxt.constants as const
from editxt.controls.textview import TextView
from editxt.sortlines import SortLinesController, sortlines

log = logging.getLogger(__name__)


def test_SortLinesController_sort_():
    m = Mocker()
    sort = m.replace(sortlines, passthrough=False)
    tv = m.mock(TextView)
    slc = SortLinesController.create_with_textview(tv)
    sort(tv, slc.opts)
    m.method(slc.save_options)()
    m.method(slc.cancel_)(None)
    with m:
        slc.sort_(None)

def test_sortlines():
    text = u"""
ghi 1 2 012
abc 3 1 543
 de 2 1 945
jkl 4 1 246
    
"""
    def test(c):
        opts = TestConfig(
            sort_selection=c.opts._get("sel", False),
            reverse_sort=c.opts._get("rev", False),
            ignore_leading_ws=c.opts._get("ign", False),
            numeric_match=c.opts._get("num", False),
            regex_sort=c.opts._get("reg", False),
            search_pattern=c.opts._get("sch", ""),
            match_pattern=c.opts._get("mch", ""),
        )
        m = Mocker()
        tv = m.mock(TextView)
        ts = tv.textStorage() >> m.mock(NSTextStorage)
        text = tv.string() >> NSString.stringWithString_(c.text)
        if opts.sort_selection:
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
        if opts.sort_selection:
            tv.setSelectedRange_(sel)
        with m:
            sortlines(tv, opts)
            def ch(line):
                value = line.lstrip(" ")
                return value[0] if value else "|%i" % len(line)
            eq_(c.result, "".join(ch(line) for line in output[0].split("\n")), output[0])
    op = TestConfig()
    tlen = len(text)
    c = TestConfig(text=text, sel=(0, tlen), opts=op)
    yield test, c(result="|0|4dagj|0")
    yield test, c(result="|0|4adgj|0", opts=op(ign=True))
    yield test, c(result="dag|0", opts=op(sel=True), sel=(5, 32))
    yield test, c(result="adg|0", opts=op(sel=True, ign=True), sel=(5, 32))
    yield test, c(result="jgad|4|0|0", opts=op(rev=True))
    
    op = op(reg=True, sch=r"\d")
    yield test, c(result="|0|4dagj|0", opts=op(reg=False))
    yield test, c(result="gdaj|0|4|0", opts=op)
    yield test, c(result="dajg|0|4|0", opts=op(sch="(\d) (\d)", mch=r"\2\1"))
    # TODO test and implement numeric match (checkbox is currently hidden)
