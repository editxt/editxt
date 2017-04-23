# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2016 Daniel Miller <millerdev@gmail.com>
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
import AppKit as ak
import objc
from objc import super

SHOULD_RESIZE = "should_resize"


class DualView(ak.NSView):

    @objc.namedSelector(
        b"init:topView:bottomView:topHeight:bottomHeight:minCollapse:flexTop:offsetRect:")
    def init(self, rect, top_view, bottom_view, top_height, bottom_height,
             min_collapse=0.2, flex_top=True, offset_rect=ak.NSZeroRect):
        """Initialize view with two subviews, top and bottom

        :param rect: The initial frame rect for this view.
        :param top_view: The view to display at the top of this view.
        :param bottom_view: The view to display at the bottom of this
        view.
        :param top_height: A function returning the preferred height of
        the top view. It should return zero if the top view is hidden.
        :param bottom_height: A function returning the preferred height
        of the bottom view. It should return zero if the bottom view is
        hidden.
        :param min_collapse: The minimum fraction of this view's
        height that should be consumed by the flexible view (see
        `flex_top`) unless that view requests a height of zero.
        :param flex_top: Expand or collapse the top view to consume the
        extra space or accommodate as much of the bottom view as
        possible if this is `True` (the default) and the sum of the
        heights of both top and bottom views does not equal the height
        of this view. If this is `False` flex the bottom view.
        :param offset_rect: Rect used to adjust subview offsets.
        """
        super(DualView, self).initWithFrame_(rect)
        self.top = top_view
        self.top_height = top_height
        self.top.setAutoresizingMask_(ak.NSViewWidthSizable
            | (ak.NSViewHeightSizable if flex_top else ak.NSViewMinYMargin))
        self.bottom = bottom_view
        self.bottom_height = bottom_height
        self.bottom.setAutoresizingMask_(ak.NSViewWidthSizable
            | (ak.NSViewMaxYMargin if flex_top else ak.NSViewHeightSizable))
        self.flex_top = flex_top
        self.min_collapse = min_collapse
        self.addSubview_(self.top)
        self.addSubview_(self.bottom)
        self.setAutoresizesSubviews_(True)
        self.setAutoresizingMask_(ak.NSViewWidthSizable | ak.NSViewHeightSizable)
        self.subview_offset_rect = offset_rect
        self._resize_subviews()
        return self

    def dealloc(self):
        self.top = None
        self.top_height = None
        self.bottom = None
        self.bottom_height = None
        super().dealloc()

    def setHidden_(self, value):
        if not value:
            self.top.setHidden_(not self.top_height())
            self.bottom.setHidden_(not self.bottom_height())
        return super(DualView, self).setHidden_(value)

    def should_resize(self):
        """Notify this view's superview that this view wants to be resized

        This is intended to be called when subviews want to be resized.

        The superview may observe SHOULD_RESIZE notifications posted
        by this view to know when to resize its subviews.
        """
        self.shouldResize_(None)

    def shouldResize_(self, ignored):
        ak.NSNotificationCenter.defaultCenter() \
            .postNotificationName_object_(SHOULD_RESIZE, self)
        self._resize_subviews()

    def _resize_subviews(self):
        """Resize subviews within the bounds of this view"""
        rect = self.bounds()
        top_height = self.top_height()
        bottom_height = self.bottom_height()
        offset = self.subview_offset_rect
        if not bottom_height:
            rect.size.width += offset.size.width
            rect.size.height += offset.size.height
            rect.origin.x += offset.origin.x
            rect.origin.y += offset.origin.y
            self.top.setHidden_(False)
            self.top.setFrame_(rect)
            self.bottom.setHidden_(True)
            return
        if not top_height:
            rect.size.width += offset.size.width
            rect.size.height += offset.size.height
            rect.origin.x += offset.origin.x
            rect.origin.y += offset.origin.y
            self.bottom.setHidden_(False)
            self.bottom.setFrame_(rect)
            self.top.setHidden_(True)
            return
        if top_height + bottom_height > rect.size.height:
            min_height = int(rect.size.height * self.min_collapse)
            if self.flex_top:
                if bottom_height > rect.size.height - min_height:
                    top_height = min_height
                else:
                    top_height = rect.size.height - bottom_height
            elif top_height > rect.size.height - min_height:
                top_height = rect.size.height - min_height
        elif self.flex_top:
            top_height = rect.size.height - bottom_height
        assert top_height < rect.size.height, (top_height, rect.size.height)
        top_rect, bottom_rect = ak.NSDivideRect(
            rect, None, None, top_height, ak.NSMaxYEdge)
        top_rect.size.width += offset.size.width
        top_rect.size.height += offset.size.height
        top_rect.origin.x += offset.origin.x
        top_rect.origin.y += offset.origin.y
        bottom_rect.size.width += offset.size.width
        bottom_rect.size.height += offset.size.height
        bottom_rect.origin.x += offset.origin.x
        bottom_rect.origin.y += offset.origin.y
        self.top.setHidden_(False)
        self.top.setFrame_(top_rect)
        self.bottom.setHidden_(False)
        self.bottom.setFrame_(bottom_rect)

    @objc.python_method
    def become_subview_of(self, view, focus=None):
        view.addSubview_(self)
        if focus:
            assert view.window() is not None, "cannot focus view: %r" % (focus,)
            view.window().makeFirstResponder_(focus)
