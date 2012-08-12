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

from AppKit import *
from Foundation import *
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
        scrollview, NSVerticalRuler)
    if textview is not None:
        lnv.textview = textview
    return lnv

def test_create():
    m = Mocker()
    sv = m.mock(NSScrollView)
    tv = m.mock(TextView)
    sv.documentView() >> tv
    not_class = m.replace(mod, 'NSNotificationCenter')
    notifier = not_class.defaultCenter() >> m.mock(NSNotificationCenter)
    notifier.addObserver_selector_name_object_(ANY, "invalidateRuleThickness",
        NSTextDidChangeNotification, tv)
    with m:
        lnv = create_lnv(scrollview=sv)
        eq_(lnv.lines, [])
        eq_(lnv.textview, tv)
        eq_(lnv.paragraph_style.alignment(), NSRightTextAlignment)

def test_requiredThickness():
    m = Mocker()
    lnv = create_lnv()
    m.method(lnv.calculate_thickness)()
    with m:
        lnv.requiredThickness()

def test_calculate_thickness():
    def test(c):
        m = Mocker()
        tv = m.mock(TextView)
        lnv = create_lnv(tv)
        estimate_line_count = m.method(lnv.estimate_line_count)
        ruleThickness = m.method(lnv.ruleThickness)
        lines = []
        font = None if c.font_is_none else m.mock(NSFont)
        (tv.textStorage() >> m.mock(NSTextStorage)).font() >> font
        if c.font_is_none:
            ruleThickness() >> c.result
        else:
            estimate_line_count(font) >> c.numlines
            cw = font.advancementForGlyph_(ord("0")).width >> 15
        with m:
            result = lnv.calculate_thickness()
            eq_(result, c.result)
            eq_(lnv.lines, lines)
    c = TestConfig(font_is_none=False)
    yield test, c(font_is_none=True, result=0)
    yield test, c(numlines=0, result=15 * 4)
    yield test, c(numlines=1, result=15 * 4)
    yield test, c(numlines=20, result=15 * 5)
    yield test, c(numlines=3000, result=15 * 7)

def test_line_number_at_char_index():
    def test(c):
        m = Mocker()
        tv = m.mock(TextView)
        lnv = create_lnv(tv)
        font = None if c.font_is_none else m.mock(NSFont)
        (tv.textStorage() >> m.mock(NSTextStorage)).font() >> font
        if not c.font_is_none:
            rect = m.mock(NSRect)
            rng = m.mock(NSRange)
            lm = tv.layoutManager() >> m.mock(NSLayoutManager)
            lm.defaultLineHeightForFont_(font) >> 10
            lm.lineFragmentRectForGlyphAtIndex_effectiveRange_(c.index, None) >> (rect, rng)
            rect.origin.y >> (10 * c.index)
        with m:
            result = lnv.line_number_at_char_index(c.index)
            eq_(result, c.result)
    c = TestConfig(font_is_none=False)
    yield test, c(font_is_none=True, index=0, result=0)
    yield test, c(index=0, result=1)


# - (void)calculateLines
# {
#     id              view;
#
#     view = [self clientView];
#
#     if ([view isKindOfClass:[NSTextView class]])
#     {
#         unsigned        index, numberOfLines, stringLength, lineEnd, contentEnd;
#         NSString        *text;
#         float         oldThickness, newThickness;
#
#         text = [view string];
#         stringLength = [text length];
#         [lineIndices release];
#         lineIndices = [[NSMutableArray alloc] init];
#
#         index = 0;
#         numberOfLines = 0;
#
#         do
#         {
#             [lineIndices addObject:[NSNumber numberWithUnsignedInt:index]];
#
#             index = NSMaxRange([text lineRangeForRange:NSMakeRange(index, 0)]);
#             numberOfLines++;
#         }
#         while (index < stringLength);
#
#         // Check if text ends with a new line.
#         [text getLineStart:NULL end:&lineEnd contentsEnd:&contentEnd forRange:NSMakeRange([[lineIndices lastObject] unsignedIntValue], 0)];
#         if (contentEnd < lineEnd)
#         {
#             [lineIndices addObject:[NSNumber numberWithUnsignedInt:index]];
#         }
#
#         oldThickness = [self ruleThickness];
#         newThickness = [self requiredThickness];
#         if (fabs(oldThickness - newThickness) > 1)
#         {
#             NSInvocation            *invocation;
#
#             // Not a good idea to resize the view during calculations (which can happen during
#             // display). Do a delayed perform (using NSInvocation since arg is a float).
#             invocation = [NSInvocation invocationWithMethodSignature:[self methodSignatureForSelector:@selector(setRuleThickness:)]];
#             [invocation setSelector:@selector(setRuleThickness:)];
#             [invocation setTarget:self];
#             [invocation setArgument:&newThickness atIndex:2];
#
#             [invocation performSelector:@selector(invoke) withObject:nil afterDelay:0.0];
#         }
#     }
# }


# def test_line_number_at_location():
#     lnv = create_lnv()
#     lnv.line_number_at_location # test for method presence
