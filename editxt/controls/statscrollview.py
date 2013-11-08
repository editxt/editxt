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

import AppKit as ak
import Foundation as fn

from editxt.controls.commandview import CommandView

log = logging.getLogger(__name__)


class StatusbarScrollView(ak.NSScrollView):

    def initWithFrame_(self, frame):
        super(StatusbarScrollView, self).initWithFrame_(frame)
        rect = fn.NSMakeRect(0, 0, 0, ak.NSScroller.scrollerWidth())
        self.commandView = CommandView.alloc().initWithFrame_(rect)
        self.addSubview_(self.commandView)
        self.statusView = StatusView.alloc().initWithFrame_(rect)
        self.addSubview_(self.statusView)
        try:
            self.setScrollerStyle_(ak.NSScrollerStyleOverlay)
            self.setVerticalScrollElasticity_(ak.NSScrollElasticityAllowed)
            self.setHorizontalScrollElasticity_(ak.NSScrollElasticityAllowed)
            self.setAutohidesScrollers_(True)
            self.can_overlay_scrollers = True
        except AttributeError:
            self.can_overlay_scrollers = False
        return self

    def tile(self):
        super(StatusbarScrollView, self).tile()
        content = self.contentView()
        status = self.statusView
        vscroll = self.verticalScroller()
        hscroll = self.horizontalScroller()
        if not (content and status and vscroll and hscroll):
            return

        scrollw = ak.NSScroller.scrollerWidth()
        rect = self.bounds()
        # (status+hscroll) | (content+vscroll)
        arect, brect = fn.NSDivideRect(rect, None, None, scrollw, fn.NSMaxYEdge)

        max_command_height = int(brect.size.height * 0.8)
        command = self.commandView
        if command and command.preferred_height > max_command_height:
            # uncommon case: command view is very tall
            # put command view under main vertical scroller
            # command | (content+vscroll)
            crect, drect = fn.NSDivideRect(brect, None, None, max_command_height, fn.NSMaxYEdge)

            # HACK adjust size for this scroller's border
            crect.origin.x -= 1
            crect.size.width += 2

            command.setHidden_(False)
            command.setFrame_(crect)

            # vscroll | content
            crect, erect = fn.NSDivideRect(drect, None, None, scrollw, fn.NSMaxXEdge)
            vscroll.setFrame_(crect)
            if not self.can_overlay_scrollers:
                drect = erect
        else:
            # common case: command view is short
            # put command view inside (to right of) main vertical scroller

            # vscroll | content
            crect, drect = fn.NSDivideRect(brect, None, None, scrollw, fn.NSMaxXEdge)
            vscroll.setFrame_(crect)
            if self.can_overlay_scrollers:
                drect = brect

            if command:
                commandh = command.preferred_height
                # command | content
                crect, drect = fn.NSDivideRect(drect, None, None, commandh, fn.NSMaxYEdge)
                command.setHidden_(False)
                command.setFrame_(crect)
            else:
                command.setHidden_(True)

        ruler = self.verticalRulerView()
        if ruler:
            rulew = ruler.calculate_thickness()
            # ruler | content
            crect, drect = fn.NSDivideRect(drect, None, None, rulew, fn.NSMinXEdge)
            ruler.setFrame_(crect)
        else:
            rulew = 0
        svwidth = status.tileWithRuleWidth_(rulew)
        content.setFrame_(drect)

        # status | scrollers
        grect, hrect = fn.NSDivideRect(arect, None, None, svwidth, fn.NSMinXEdge)
        status.setFrame_(grect)
        hscroll.setFrame_(hrect)
        if self.can_overlay_scrollers \
                and self.scrollerStyle() != ak.NSScrollerStyleOverlay:
            self.setScrollerStyle_(ak.NSScrollerStyleOverlay)
        self.setNeedsDisplay_(True)

    def tile_and_redraw(self):
        self.tile()


class StatusView(ak.NSView):

    def initWithFrame_(self, rect):
        super(StatusView, self).initWithFrame_(rect)
        font = ak.NSFont.fontWithName_size_("Monaco", 9.0)
        for fname in ["linenumView", "columnView", "selectionView"]:
            field = ak.NSTextField.alloc().initWithFrame_(fn.NSZeroRect)
            field.setStringValue_("")
            field.setEditable_(False)
            field.setBackgroundColor_(ak.NSColor.controlColor())
            field.setFont_(font)
            field.setAlignment_(ak.NSRightTextAlignment)
            self.addSubview_(field)
            setattr(self, fname, field)
        return self

    def tileWithRuleWidth_(self, width):
        rect = self.bounds()
        width = width if width else 50
        arect, brect = fn.NSDivideRect(rect, None, None, width, fn.NSMinXEdge)
        self.linenumView.setFrame_(arect)
        crect, drect = fn.NSDivideRect(brect, None, None, 50, fn.NSMinXEdge)
        crect.origin.x -= 1
        crect.size.width += 1
        self.columnView.setFrame_(crect)
        drect.origin.x -= 1
        drect.size.width = 51
        self.selectionView.setFrame_(drect)
        return arect.size.width + crect.size.width + drect.size.width - 2

    def updateLine_column_selection_(self, line, col, sel):
        self.linenumView.setIntValue_(line)
        self.columnView.setIntValue_(col)
        if sel > 0:
            self.selectionView.setIntValue_(sel)
        else:
            self.selectionView.setStringValue_("")
