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
import re

import objc
import AppKit as ak
import Foundation as fn

from editxt import app
from editxt.util import untested

log = logging.getLogger(__name__)


class LineNumberView(ak.NSRulerView):

    def initWithScrollView_orientation_(self, scrollview, orientation):
        super(LineNumberView, self).initWithScrollView_orientation_(scrollview, orientation)
        self.textview = scrollview.documentView()
        self.lines = []
        self.paragraph_style = ps = ak.NSParagraphStyle.defaultParagraphStyle().mutableCopy()
        self.paragraphStyle = ps
        ps.setAlignment_(ak.NSRightTextAlignment)
        self.line_count = 1

        # [[NSNotificationCenter defaultCenter]
        #     addObserver:self
        #     selector:@selector(textDidChange:)
        #     name:NSTextStorageDidProcessEditingNotification
        #     object:[(NSTextView *)aView textStorage]];

        # subscribe to text edit notifications
        fn.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "invalidateRuleThickness", ak.NSTextDidChangeNotification,
            self.textview)
        return self

    def denotify(self):
        fn.NSNotificationCenter.defaultCenter().removeObserver_(self)

    # Line Counting ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @untested
    def estimate_line_count(self, font):
        if "not in word wrap mode": # TODO detect word wrap mode
            tv = self.textview
            line_height = tv.layoutManager().defaultLineHeightForFont_(font)
            min_count = int(round(tv.bounds().size.height / line_height))
            return self.update_line_count(min_count)
        else:
            raise NotImplementedError("word-wrap line counting not implementedd")
            # http://developer.apple.com/documentation/Cocoa/Conceptual/TextLayout/Tasks/CountLines.html

    @untested
    def update_line_count(self, value):
        lc = self.line_count
        if lc < value:
            self.line_count = lc = value
        return lc

    def line_number_at_char_index(self, index):
        font = self.textview.textStorage().font()
        if font is None:
            return 0
        lm = self.textview.layoutManager()
        line_height = lm.defaultLineHeightForFont_(font)
        lrect, range = lm.lineFragmentRectForGlyphAtIndex_effectiveRange_(index, None)
        return int(round(lrect.origin.y / line_height)) + 1

    # Rule thickness and drawing ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def calculate_thickness(self):
        font = self.textview.textStorage().font()
        if font is not None:
            charwidth = font.advancementForGlyph_(ord("0")).width
            lines = self.estimate_line_count(font)
            return int((len(str(lines)) + 3) * charwidth)
        return self.ruleThickness()

    def requiredThickness(self):
        return self.calculate_thickness()

    @untested
    def invalidateRuleThickness(self):
        thickness = self.calculate_thickness()
        # TODO do not call setNeedsDisplayInRect_ if the (exact) number of lines did not change
        self.setNeedsDisplayInRect_(self.frame())
        if thickness > self.ruleThickness():
            self.setRuleThickness_(int(thickness))
            self.scrollView().tile()

    @untested
    def drawHashMarksAndLabelsInRect_(self, rect):
        """Draw the line numbers

        There is a bug (in Cocoa on OS X 10.6 ?) which causes a region of the
        ruler to be skipped when scrolling very quickly (flick the mouse wheel
        as fast as possible, then observe the line numbers). This bug can be
        reproduced in the Xcode editor.

        Another bug causes the ruler to (initially) move in the wrong direction
        if the text view's textContainerInset().height is set larger than zero.
        """
        tv = self.textview
        font = tv.textStorage().font()
        if font is None:
            return
        lm = tv.layoutManager()
        lineHeight = tv.layoutManager().defaultLineHeightForFont_(font)
        offset = (tv.textContainerInset().height - 1) \
            - self.scrollView().documentVisibleRect().origin.y
        top = fn.NSMakePoint(0, rect.origin.y - offset)
        bot = fn.NSMakePoint(0, rect.origin.y - offset + rect.size.height)
        topGlyph = lm.glyphIndexForPoint_inTextContainer_(top, tv.textContainer())
        botGlyph = lm.glyphIndexForPoint_inTextContainer_(bot, tv.textContainer())
        drawWidth = self.baselineLocation() + self.requiredThickness() - (lineHeight / 2)
        drawRect = fn.NSMakeRect(0, 0, drawWidth, lineHeight)
        attr = {
            ak.NSFontAttributeName: font,
            ak.NSParagraphStyleAttributeName: self.paragraphStyle,
        }
        i = topGlyph
        line = max(0, int(top.y)) // int(lineHeight) + 1
        # TODO handle word-wrap mode line counting (when that feature is implemented)

        while i <= botGlyph:
            lrect, range = lm.lineFragmentRectForGlyphAtIndex_effectiveRange_(i, None)
            text = fn.NSString.stringWithString_(str(line))
            drawRect.origin.y = lrect.origin.y + offset
            text.drawInRect_withAttributes_(drawRect, attr)
            line += 1
            i += range.length
        last = tv.textStorage().length() - 1
        if i >= last and tv.string()[last] in "\n\r":
            # draw last line number when the last character is newline
            text = fn.NSString.stringWithString_(str(line))
            drawRect.origin.y = lrect.origin.y + offset + lineHeight
            text.drawInRect_withAttributes_(drawRect, attr)
            self.update_line_count(line + 1)
        else:
            self.update_line_count(line)
