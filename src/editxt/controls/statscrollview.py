# -*- coding: utf-8 -*-
# EditXT
# Copywrite (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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


log = logging.getLogger("editxt.controls.statscrollview")


class StatusbarScrollView(NSScrollView):

    def initWithFrame_(self, frame):
        super(StatusbarScrollView, self).initWithFrame_(frame)
        rect = NSMakeRect(0, 0, 0, NSScroller.scrollerWidth())
        self.statusView = StatusView.alloc().initWithFrame_(rect)
        self.addSubview_(self.statusView)
        return self

    def tile(self):
        super(StatusbarScrollView, self).tile()
        cv = self.contentView()
        sv = self.statusView
        vs = self.verticalScroller()
        hs = self.horizontalScroller()
        if cv and sv and vs and hs:
            scrollw = NSScroller.scrollerWidth()
            rect = self.bounds()
            arect, brect = NSDivideRect(rect, None, None, scrollw, NSMaxYEdge) # (status+scrollers) | (ruler+content+vscroller)
            crect, drect = NSDivideRect(brect, None, None, scrollw, NSMaxXEdge) # vscroller | (ruler+content)
            vs.setFrame_(crect)
            rv = self.verticalRulerView()
            if rv:
                rulew = rv.calculate_thickness()
                erect, frect = NSDivideRect(drect, None, None, rulew, NSMinXEdge) # ruler | content
                rv.setFrame_(erect)
                cv.setFrame_(frect)
            else:
                cv.setFrame_(drect)
                rulew = 0
            svwidth = sv.tileWithRuleWidth_(rulew)
            grect, hrect = NSDivideRect(arect, None, None, svwidth, NSMinXEdge) # status | scrollers
            sv.setFrame_(grect)
            arect, brect = NSDivideRect(hrect, None, None, scrollw, NSMaxXEdge) # vscroller | hscroller
            hs.setFrame_(hrect)


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
