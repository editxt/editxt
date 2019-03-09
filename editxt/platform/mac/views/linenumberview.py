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

from editxt.platform.mac.events import call_later
from editxt.platform.mac.views.util import font_smoothing
from editxt.util import noraise

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

    @objc.python_method
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
                call_later(0, self.setNeedsDisplay_, True)
        return value

    def invalidateRuleThickness(self):
        self.calculate_thickness(display=False)
        self.setNeedsDisplay_(True)

    @noraise
    def drawRect_(self, rect):
        # draw background and border line
        view = self.textview
        colors = view.margin_params
        half_char = view.textContainerInset().height
        line_pos = round(rect.size.width - half_char)

        colors.margin_color.set()
        ak.NSRectFill(fn.NSMakeRect(
            rect.origin.x,
            rect.origin.y,
            line_pos,
            rect.size.height
        ))
        colors.background_color.set()
        ak.NSRectFill(fn.NSMakeRect(
            rect.origin.x + line_pos,
            rect.origin.y,
            rect.size.width - line_pos,
            rect.size.height
        ))
        colors.line_color.set()
        ak.NSRectFill(fn.NSMakeRect(
            rect.origin.x + line_pos,
            rect.origin.y,
            1.0,
            rect.size.height
        ))
        self.draw_line_numbers(rect, colors.line_number_color)
        self._display_skipped_rect_if_necessary(rect)

    @objc.python_method
    def char_index_at_point(self, point, adjust_x=True):
        view_point = self.convertPoint_toView_(point, self.textview)
        return self.textview.char_index_at_point(view_point, adjust_x)

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
        y_offset = view.textContainerOrigin().y + layout.defaultBaselineOffsetForFont_(font)
        first_char = self.char_index_at_point(rect.origin)

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
            if char_index < first_char and y_pos:
                continue
            rects, n = char_rects((char_index, 0), null_range, container, None)
            if not n:
                continue
            y_pos = convert_point(rects[0].origin, view).y + y_offset
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

    @objc.python_method
    def _display_skipped_rect_if_necessary(self, rect):
        """HACK fix line number drawing on High Sierra

        Some regions of the ruler view are not redrawn on scroll,
        resulting in garbled line numbers.
        """
        new_y = self.convertPoint_toView_(self.bounds().origin, self.textview).y
        old_y = getattr(self, "old_y", None)
        self.old_y = new_y
        if old_y is not None:
            delta_y = abs(new_y - old_y)
            if delta_y > rect.size.height:
                skipped_height = delta_y - rect.size.height
                if rect.origin.y == 0:
                    skipped_top = rect.size.height
                else:
                    skipped_top = rect.origin.y - skipped_height
                skipped_rect = (
                    (rect.origin.x, skipped_top),
                    (rect.size.width, skipped_height),
                )
                self.setNeedsDisplayInRect_(skipped_rect)

    @noraise
    def mouseDown_(self, event):
        super().mouseDown_(event)
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        char_index = self.char_index_at_point(point)
        self.original_selection = self.textview.selectedRange()
        self.mouse_down_char_index = char_index
        self.mouse_dragged = False

    @noraise
    def mouseDragged_(self, event):
        super().mouseDragged_(event)
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        if not ak.NSPointInRect(point, self.frame()):
            view_point = self.convertPoint_toView_(point, self.textview)
            doc_rect = self.scrollView().documentVisibleRect()
            if not ak.NSPointInRect(view_point, doc_rect):
                self.textview.setSelectedRange_(self.original_selection)
                return
            char_index = self.char_index_at_point(point, False)
        else:
            char_index = self.char_index_at_point(point)
            if self.mouse_down_char_index != char_index:
                length = self.textview.textStorage().length()
                if char_index == length - 1:
                    # dragged to or beyond last line
                    lines = self.textview.editor.line_numbers
                    if lines.end and lines.newline_at_end:
                        char_index = lines.end
        self.textview.setSelectedRange_((
            min(self.mouse_down_char_index, char_index),
            abs(self.mouse_down_char_index - char_index)
        ))
        self.mouse_dragged = True

    @noraise
    def mouseUp_(self, event):
        super().mouseUp_(event)
        point = self.convertPoint_fromView_(event.locationInWindow(), None)
        if not ak.NSPointInRect(point, self.frame()):
            view_point = self.convertPoint_toView_(point, self.textview)
            doc_rect = self.scrollView().documentVisibleRect()
            if not ak.NSPointInRect(view_point, doc_rect):
                self.textview.setSelectedRange_(self.original_selection)
                return
        elif not self.mouse_dragged:
            view = self.textview
            font = view.font()
            layout = view.layoutManager()
            line_height = layout.defaultLineHeightForFont_(font)

            char_index = self.char_index_at_point(point)
            point2 = ak.NSPoint(point.x, point.y + line_height)
            char_index2 = self.char_index_at_point(point2)
            length = view.textStorage().length()
            mods = event.modifierFlags() & ak.NSDeviceIndependentModifierFlagsMask
            extend_selection = mods == ak.NSShiftKeyMask

            if char_index == char_index2 and char_index >= length - 1:
                # clicked below last line
                if extend_selection:
                    start = self.original_selection[0]
                    rng = (start, length - start)
                else:
                    rng = (length, 0)
            else:
                lines = view.editor.line_numbers
                line = lines[char_index]
                try:
                    next_index = lines.index_of(line + 1)
                except ValueError:
                    next_index = length
                start = min(char_index, next_index)
                length = abs(next_index - char_index)
                if extend_selection:
                    orig = self.original_selection
                    if orig[0] < start:
                        # beginning of original to end of clicked line
                        length = length + start - orig[0]
                        start = orig[0]
                    elif sum(orig) > start + length:
                        # beginning of clicked line to end of original
                        length = sum(orig) - start
                    elif start <= orig[0] and (start + length) > sum(orig):
                        # beginning of clicked line to end of original on same line
                        length = sum(orig) - start
                rng = (start, length)
            view.setSelectedRange_(rng)
        self.original_selection = None
        self.mouse_down_char_index = None
        self.mouse_dragged = None
