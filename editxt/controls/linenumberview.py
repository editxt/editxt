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
from objc import super

from editxt.platform.mac.views.util import font_smoothing

log = logging.getLogger(__name__)


class LineNumberView(ak.NSRulerView):

    def initWithScrollView_orientation_(self, scrollview, orientation):
        super(LineNumberView, self).initWithScrollView_orientation_(scrollview, orientation)
        self.textview = scrollview.documentView()
        self.paragraph_style = ps = ak.NSParagraphStyle.defaultParagraphStyle().mutableCopy()
        ps.setAlignment_(ak.NSRightTextAlignment)
        self.line_count = 1

        # subscribe to text edit notifications
        fn.NSNotificationCenter.defaultCenter().addObserver_selector_name_object_(
            self, "invalidateRuleThickness", ak.NSTextDidChangeNotification,
            self.textview)
        return self

    def denotify(self):
        fn.NSNotificationCenter.defaultCenter().removeObserver_(self)

    def calculate_thickness(self, min_count=0, display=True):
        if not min_count:
            min_count = len(self.textview.editor.line_numbers)
        lines = self.line_count
        if lines < min_count:
            self.line_count = lines = min_count
        font = self.textview.font()
        charwidth = font.advancementForGlyph_(ord("8")).width
        value = int(max(len(str(lines)) + 2.7, 4.7) * charwidth)
        if value > self.ruleThickness():
            self.setRuleThickness_(value)
            if display:
                from editxt.platform.events import call_later
                call_later(0, self.setNeedsDisplay_, True)
        return value

    def invalidateRuleThickness(self):
        self.calculate_thickness(display=False)
        self.setNeedsDisplay_(True)

    def drawRect_(self, rect):
        # draw background and border line
        view = self.textview
        ignore, line_color, margin_color, line_number_color = view.margin_params
        half_char = view.textContainerInset().height
        line_pos = round(rect.size.width - half_char)

        margin_color.set()
        ak.NSRectFill(fn.NSMakeRect(
            rect.origin.x,
            rect.origin.y,
            line_pos,
            rect.size.height
        ))
        ak.NSColor.whiteColor().set()
        ak.NSRectFill(fn.NSMakeRect(
            rect.origin.x + line_pos,
            rect.origin.y,
            rect.size.width - line_pos,
            rect.size.height
        ))
        line_color.set()
        ak.NSRectFill(fn.NSMakeRect(
            rect.origin.x + line_pos,
            rect.origin.y,
            1.0,
            rect.size.height
        ))
        self.draw_line_numbers(rect, line_number_color)

    @font_smoothing
    def draw_line_numbers(self, rect, color):
        """Draw the line numbers

        There is a bug (in Cocoa on OS X 10.6 ?) which causes a region of the
        ruler to be skipped when scrolling very quickly (flick the mouse wheel
        as fast as possible, then observe the line numbers). This bug can be
        reproduced in the Xcode editor.

        Another bug causes the ruler to (initially) move in the wrong direction
        if the text view's textContainerInset().height is set larger than zero.
        """
        view = self.textview
        font = view.font()
        layout = view.layoutManager()
        container = view.textContainer()
        line_height = layout.defaultLineHeightForFont_(font)
        y_min = rect.origin.y - line_height
        y_max = rect.origin.y + rect.size.height + line_height
        half_char = view.textContainerInset().height
        lines = view.editor.line_numbers
        null_range = (ak.NSNotFound, 0)
        convert_point = self.convertPoint_fromView_
        char_rects = layout.rectArrayForCharacterRange_withinSelectedCharacterRange_inTextContainer_rectCount_

        view_y = self.convertPoint_toView_(rect.origin, view).y
        visible_rect = self.scrollView().contentView().bounds()
        view_rect = fn.NSMakeRect(0, view_y, visible_rect.size.width, rect.size.height)
        y_offset = view.textContainerOrigin().y + layout.defaultBaselineOffsetForFont_(font)

        glyph_range = layout.glyphRangeForBoundingRect_inTextContainer_(
                            view_rect, container)
        if glyph_range.location == 0 and view_rect.origin.y > 0:
            glyph_range = layout.glyphRangeForBoundingRect_inTextContainer_(
                            visible_rect, container)
        first_char = layout.characterIndexForGlyphAtIndex_(glyph_range.location)

        draw_width = rect.size.width - half_char * 3
        draw_rect = fn.NSMakeRect(0, 0, draw_width, 0)
        attr = {
            ak.NSFontAttributeName: font,
            ak.NSParagraphStyleAttributeName: self.paragraph_style,
            ak.NSForegroundColorAttributeName: color,
        }

        # draw line numbers
        y_pos = None
        for line, char_index in lines.iter_from(first_char):
            if char_index < first_char:
                continue
            rects, n = char_rects((char_index, 0), null_range, container, None)
            if not n:
                continue
            y_pos = (convert_point(rects[0].origin, view).y + y_offset)
            if y_pos < y_min:
                continue
            if y_pos > y_max:
                break
            draw_rect.origin.y = y_pos
            text = fn.NSString.stringWithString_(str(line))
            text.drawWithRect_options_attributes_(draw_rect, 0, attr)

        if y_pos is not None:
            if y_pos >= y_min and lines.newline_at_end and line + 1 == len(lines):
                line += 1
                draw_rect.origin.y = y_pos + line_height
                text = fn.NSString.stringWithString_(str(line))
                text.drawWithRect_options_attributes_(draw_rect, 0, attr)
            if line > self.line_count:
                self.calculate_thickness(line)
