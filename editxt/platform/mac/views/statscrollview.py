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
from objc import super

from editxt.platform.mac.overlaywindow import OverlayWindow

log = logging.getLogger(__name__)

NSScrollerStyleLegacy = getattr(ak, "NSScrollerStyleLegacy", 0)
NSScrollerStyleOverlay = getattr(ak, "NSScrollerStyleOverlay", 1)


class StatusbarScrollView(ak.NSScrollView):

    def initWithFrame_(self, frame):
        super(StatusbarScrollView, self).initWithFrame_(frame)
        rect = fn.NSMakeRect(0, 0, 0, ak.NSScroller.scrollerWidth())
        self.status_view = StatusView.alloc().initWithFrame_(rect)
        scroller_style = getattr(self, "scrollerStyle", lambda:NSScrollerStyleLegacy)()
        if scroller_style == NSScrollerStyleOverlay:
            self.overlay_bounds = rect
            self.can_overlay_scrollers = True
        else:
            self.can_overlay_scrollers = False
            self.addSubview_(self.status_view)
        return self

    def tile(self):
        super(StatusbarScrollView, self).tile()
        content = self.contentView()
        status = self.status_view
        vscroll = self.verticalScroller()
        hscroll = self.horizontalScroller()
        if not (content and status and vscroll and hscroll):
            return

        scrollw = ak.NSScroller.scrollerWidth()
        rect = self.bounds()
        if self.can_overlay_scrollers:
            # content view is entire bounds
            crect = rect
        else:
            # (status+hscroll) | (content+vscroll)
            arect, brect = fn.NSDivideRect(rect, None, None, scrollw, fn.NSMaxYEdge)
            # vscroll | content
            vscroll_rect, crect = fn.NSDivideRect(brect, None, None, scrollw, fn.NSMaxXEdge)

        ruler = self.verticalRulerView()
        if ruler:
            ruler.calculate_thickness()
            rulew = ruler.requiredThickness()
            # ruler | content
            rule_rect, crect = fn.NSDivideRect(crect, None, None, rulew, fn.NSMinXEdge)
        else:
            rulew = 0
        status_size = status.tile_with_ruler_width(
            rulew, uniform=self.can_overlay_scrollers)

        if self.can_overlay_scrollers:
            if self.overlay is not None:
                # Set overlay rect in this view's coordinate system.
                # This avoids overlay resize redraw flash when the
                # overlay window was sized to self.bounds()
                self.overlay_bounds = fn.NSMakeRect(
                    rect.size.width - status_size.width - scrollw,
                    rect.size.height - status_size.height,
                    *status_size)
                self.overlay.updateSize()
                status.setFrame_(fn.NSMakeRect(0, 0, *status_size))
        else:
            # status | scrollers
            status_rect, hrect = fn.NSDivideRect(
                arect, None, None, status_size.width, fn.NSMinXEdge)
            if ruler:
                ruler.setFrame_(rule_rect)
            content.setFrame_(crect)
            vscroll.setFrame_(vscroll_rect)
            hscroll.setFrame_(hrect)
            status.setFrame_(status_rect)
            self.setNeedsDisplay_(True)

    def setBackgroundColor_(self, color):
        super().setBackgroundColor_(color)
        self.status_view.setBackgroundColor_(color)

    @property
    def overlay(self):
        window = self.window()
        if window is None:
            return None
        try:
            overlay = window.__overlay
        except AttributeError:
            overlay = window.__overlay = OverlayWindow.alloc().initWithView_(self)
        if self.status_view not in overlay.contentView().subviews():
            self.status_view.setAutoresizingMask_(
                ak.NSViewMinXMargin | ak.NSViewMaxYMargin)
            overlay.contentView().setSubviews_([self.status_view])
        return overlay

    def viewWillMoveToWindow_(self, new_window):
        super().viewWillMoveToWindow_(new_window)
        if not self.can_overlay_scrollers:
            return
        old_window = self.window()
        if old_window is not None:
            try:
                overlay = old_window.__overlay
            except AttributeError:
                return
            if self.status_view in overlay.contentView().subviews():
                self.status_view.removeFromSuperview()

    def viewDidMoveToWindow(self):
        if self.can_overlay_scrollers and self.overlay is not None:
            self.overlay.attachToView_(self)

    def drawRect_(self, rect):
        # Super strange fix for bug that caused sluggish line number
        # redrawing (scroll view was invalidating entire line number
        # view on each drawRect_ call) after switching to another
        # application and then back again when command view was active.
        return super(StatusbarScrollView, self).drawRect_(rect)
        # How the this fix was found:
        #
        # Used cProfile to count the methods being called before and
        # after triggering the bug. Noticed that `LineNumberView.
        # draw_line_numbers` was called at the normal rate before and
        # after, but `editor.line_numbers.iter_from` was called many
        # more times after the bug was invoked. Added a `print(rect)`
        # statement to the `LineNumberView.drawRect_` verify this.
        #
        # Then made a tool to override all methods of this class to
        # print their method signature on each call. Noticed that the
        # bug went away when this tool was in use. Used a binary search
        # to narrow down which method override "fixed" the bug. The
        # debugging tool can be found in notes.txt; search for
        # "AOPython".


class StatusView(ak.NSView):

    def initWithFrame_(self, rect):
        super(StatusView, self).initWithFrame_(rect)
        font = ak.NSFont.labelFontOfSize_(9.0)
        self.fields = []
        for fname in ["linenumView", "columnView", "selectionView"]:
            field = StatusField.alloc().initWithFrame_(fn.NSZeroRect)
            field.setStringValue_("")
            field.setEditable_(False)
            field.setFont_(font)
            field.setAlignment_(ak.NSRightTextAlignment)
            self.addSubview_(field)
            setattr(self, fname, field)
            self.fields.append(field)
        return self

    def tile_with_ruler_width(self, width, uniform=False):
        """Tile subviews with vertical ruler width

        :param width: The width of the line number ruler view.
        :param uniform: Use uniform widths for all subviews if true.
        When false, resize line number view with the same width as the
        ruler.
        :returns: Size of the tiled status view.
        """
        # TODO minimum width based on font size rather than constant 50
        if uniform:
            rwidth = max(width, 50)
            x = 0
            y = -1
        else:
            rwidth = width + 1
            x = -1
            y = -1
        width = max(width, 50)
        height = ak.NSScroller.scrollerWidth() + 1
        line_rect = fn.NSMakeRect(x, y, rwidth, height)
        col_rect = fn.NSMakeRect(x + rwidth - 1, y, width, height)
        sel_rect = fn.NSMakeRect(x + rwidth + width - 2, y, width, height)
        self.linenumView.setFrame_(line_rect)
        self.columnView.setFrame_(col_rect)
        self.selectionView.setFrame_(sel_rect)
        return fn.NSMakeSize(rwidth + width * 2 - 2, height - 1)

    def updateLine_column_selection_(self, line, col, sel):
        self.linenumView.setIntValue_(line)
        self.columnView.setIntValue_(col)
        if sel > 0:
            self.selectionView.setIntValue_(sel)
        else:
            self.selectionView.setStringValue_("")

    def setBackgroundColor_(self, color):
        for field in self.fields:
            field.setBackgroundColor_(color)


class StatusField(ak.NSTextField):

    pass
    #from editxt.platform.mac.views.util import font_smoothing as _smoothing
    #drawRect_ = _smoothing(ak.NSTextField.drawRect_)
