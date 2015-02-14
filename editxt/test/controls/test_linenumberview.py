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
import os

import AppKit as ak
import Foundation as fn
from mocker import Mocker, expect, ANY
from nose.tools import *
from editxt.test.util import TestConfig, untested

import editxt.constants as const
import editxt.controls.linenumberview as mod
from editxt.controls.textview import TextView

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement TextDocumentView.pasteboard_data()
# """)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class MockScrollView(object):
    def documentView(self):
        return None

def create_lnv(textview=None, scrollview=None):
    if scrollview is None:
        scrollview = MockScrollView()
    lnv = mod.LineNumberView.alloc().initWithScrollView_orientation_(
        scrollview, ak.NSVerticalRuler)
    if textview is not None:
        lnv.textview = textview
    return lnv

def test_create():
    m = Mocker()
    sv = m.mock(ak.NSScrollView)
    tv = m.mock(TextView)
    sv.documentView() >> tv
    not_class = m.replace(fn, 'NSNotificationCenter')
    notifier = not_class.defaultCenter() >> m.mock(fn.NSNotificationCenter)
    notifier.addObserver_selector_name_object_(ANY, "invalidateRuleThickness",
        ak.NSTextDidChangeNotification, tv)
    with m:
        lnv = create_lnv(scrollview=sv)
        eq_(lnv.textview, tv)
        eq_(lnv.paragraph_style.alignment(), ak.NSRightTextAlignment)

def test_calculate_thickness():
    def test(c):
        m = Mocker()
        tv = m.mock(TextView)
        lnv = create_lnv(tv)
        ruleThickness = m.method(lnv.ruleThickness)
        ruleThickness() >> 200
        (tv.editor.line_numbers << []).count(0, 1)
        font = tv.font() >> m.mock(ak.NSFont)
        cw = font.advancementForGlyph_(ord("8")).width >> 15
        with m:
            result = lnv.calculate_thickness(c.numlines)
            eq_(result, c.result)
    c = TestConfig(font_is_none=False)
    yield test, c(numlines=0, result=int(15 * 4.7))
    yield test, c(numlines=1, result=int(15 * 4.7))
    yield test, c(numlines=20, result=int(15 * 4.7))
    yield test, c(numlines=200, result=int(15 * 5.7))
    yield test, c(numlines=3000, result=int(15 * 6.7))
