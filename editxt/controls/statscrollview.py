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
import logging

from AppKit import *
from Foundation import *

from editxt.controls.commandview import CommandView

log = logging.getLogger(__name__)


class StatusbarScrollView(NSScrollView):

    def initWithFrame_(self, frame):
        super(StatusbarScrollView, self).initWithFrame_(frame)
        rect = NSMakeRect(0, 0, 0, NSScroller.scrollerWidth())
        self.commandView = CommandView.alloc().initWithFrame_(rect)
        self.addSubview_(self.commandView)
        self.statusView = StatusView.alloc().initWithFrame_(rect)
        self.addSubview_(self.statusView)
        return self

    def tile(self):
        super(StatusbarScrollView, self).tile()
        content = self.contentView()
        status = self.statusView
        vscroll = self.verticalScroller()
        hscroll = self.horizontalScroller()
        if not (content and status and vscroll and hscroll):
            return

        scrollw = NSScroller.scrollerWidth()
        rect = self.bounds()
        # (status+hscroll) | content+vscroll)
        arect, brect = NSDivideRect(rect, None, None, scrollw, NSMaxYEdge)

        # vscroll | content
        crect, drect = NSDivideRect(brect, None, None, scrollw, NSMaxXEdge)
        vscroll.setFrame_(crect)

        if self.commandView:
            commandh = self.commandView.preferred_height
            # command | content
            crect, drect = NSDivideRect(drect, None, None, commandh, NSMaxYEdge)
            self.commandView.setHidden_(False)
            self.commandView.setFrame_(crect)
        else:
            self.commandView.setHidden_(True)

        ruler = self.verticalRulerView()
        if ruler:
            rulew = ruler.calculate_thickness()
            # ruler | content
            crect, drect = NSDivideRect(drect, None, None, rulew, NSMinXEdge)
            ruler.setFrame_(crect)
        else:
            rulew = 0
        svwidth = status.tileWithRuleWidth_(rulew)
        content.setFrame_(drect)

        # status | scrollers
        grect, hrect = NSDivideRect(arect, None, None, svwidth, NSMinXEdge)
        status.setFrame_(grect)
        hscroll.setFrame_(hrect)

    def tile_and_redraw(self):
        self.tile()
        self.setNeedsDisplay_(True)


class StatusView(NSView):

    def initWithFrame_(self, rect):
        super(StatusView, self).initWithFrame_(rect)
        font = NSFont.fontWithName_size_("Monaco", 9.0)
        for fname in ["linenumView", "columnView", "selectionView"]:
            field = NSTextField.alloc().initWithFrame_(NSZeroRect)
            field.setStringValue_("")
            field.setEditable_(False)
            field.setBackgroundColor_(NSColor.controlColor())
            field.setFont_(font)
            field.setAlignment_(NSRightTextAlignment)
            self.addSubview_(field)
            setattr(self, fname, field)
        return self

    def tileWithRuleWidth_(self, width):
        rect = self.bounds()
        width = width if width else 50
        arect, brect = NSDivideRect(rect, None, None, width, NSMinXEdge)
        self.linenumView.setFrame_(arect)
        crect, drect = NSDivideRect(brect, None, None, 50, NSMinXEdge)
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
            self.selectionView.setStringValue_(u"")
