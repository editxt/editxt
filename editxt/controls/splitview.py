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

import AppKit as ak
import Foundation as fn
import objc

from editxt.util import load_image

log = logging.getLogger(__name__)


class ThinSplitView(ak.NSSplitView):
    """Thin resizable split view

    Note: this view does not support more than two subviews
    """
    
    resizeSlider = objc.IBOutlet()
    fixedSizeView = objc.IBOutlet()

    def awakeFromNib(self):
        # resizeOffset is set to a non-null (float) value representing the
        # distance between the click/drag location and the splitter handle
        # when the resizer is dragged. It is None when the slider is not
        # being dragged.
        self.resizeOffset = None
        self.setDelegate_(self)
        subviews = self.subviews()
        assert self.fixedSizeView in subviews, "fixedSizeView not found in subviews"
        assert len(subviews) == 2, "ThinSplitView supports exactly two subviews"
        self.animation_delegate = RedrawOnAnimationEndedDelegate.alloc().init(self)

    def dealloc(self):
        self.animation_delegate = None
        super(ThinSplitView, self).dealloc()

    def dividerThickness(self):
        return 1.0

    def drawDividerInRect_(self, rect):
        ak.NSColor.colorWithDeviceWhite_alpha_(0.75, 1).setFill()
        ak.NSBezierPath.fillRect_(rect)

    # delegate implementation ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def splitView_canCollapseSubview_(self, view, subview):
        return True

    def splitView_constrainMinCoordinate_ofSubviewAt_(self, view, min, offset):
        return 100.0 # min width

    def splitView_constrainMaxCoordinate_ofSubviewAt_(self, view, max, offset):
        size = self.bounds().size
        total = size.width if self.isVertical() else size.height
        return (total - 50.0) if total > 50.0 else (total / 2.0)

    def splitView_resizeSubviewsWithOldSize_(self, view, size):
        size = self.fixedSizeView.bounds().size
        thick = size.width if self.isVertical() else size.height
        self.setFixedSideThickness_(thick)

    # Sidebar resize handle area ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def resetCursorRects(self):
        super(ThinSplitView, self).resetCursorRects()
        if self.resizeSlider is not None:
            rect = self.frame()
            location = self.resizeSlider.frame()
            location.origin.y = rect.size.height - location.size.height
            self.addCursorRect_cursor_(location, ak.NSCursor.resizeLeftRightCursor())

    def mouseDown_(self, event):
        clickloc = event.locationInWindow()
        clickrec = self.hitTest_(clickloc)
        if clickrec is self.resizeSlider and clickrec is not None:
            frame = self.fixedSizeView.frame()
            self.resizeOffset = (frame.origin.x + frame.size.width) - clickloc.x
        else:
            self.resizeOffset = None
            super(ThinSplitView, self).mouseDown_(event)

    def mouseUp_(self, event):
        self.resizeOffset = None

    def mouseDragged_(self, event):
        if self.resizeOffset is None:
            super(ThinSplitView, self).mouseDragged_(event)
            return

        fn.NSNotificationCenter.defaultCenter().postNotificationName_object_(
            ak.NSSplitViewWillResizeSubviewsNotification, self)
        clickloc = event.locationInWindow()
        frame = self.fixedSizeView.frame()
        frame.size.width = clickloc.x + self.resizeOffset

        delegate = self.delegate()
        if delegate:
            if delegate.respondsToSelector_("splitView:constrainSplitPosition:ofSubviewAt:"):
                wid = delegate.splitView_constrainSplitPosition_ofSubviewAt_(self, frame.size.width, 0)
                frame.size.width = wid
            if delegate.respondsToSelector_("splitView:constrainMinCoordinate:ofSubviewAt:"):
                wid = delegate.splitView_constrainMinCoordinate_ofSubviewAt_(self, 0.0, 0)
                frame.size.width = max(wid, frame.size.width)
            if delegate.respondsToSelector_("splitView:constrainMaxCoordinate:ofSubviewAt:"):
                wid = delegate.splitView_constrainMaxCoordinate_ofSubviewAt_(self, 0.0, 0)
                frame.size.width = min(wid, frame.size.width)

        self.fixedSizeView.setFrame_(frame)
        self.adjustSubviews()

        fn.NSNotificationCenter.defaultCenter().postNotificationName_object_(
            ak.NSSplitViewDidResizeSubviewsNotification, self)

    # slider position get/set ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def fixedSideThickness(self):
        size = self.fixedSizeView.bounds().size
        if self.isVertical():
            return size.width
        return size.height

    def setFixedSideThickness_(self, value):
        dim, org = ("width", "x") if self.isVertical() else ("height", "y")
        div = self.dividerThickness()
        for i, view in enumerate(self.subviews()):
            rect = self.bounds()
            if view is self.fixedSizeView:
                thick = value
                origin = 0 if i == 0 else (getattr(rect.size, dim) - value)
            else:
                thick = getattr(rect.size, dim) - value - div
                origin = 0 if i == 0 else (value + div)
            setattr(rect.size, dim, thick)
            setattr(rect.origin, org, origin)
            view.setFrame_(rect)

    # slider animation ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def is_view_visible(self, index, min_thickness=0.0):
        view = self.subviews()[index]
        dim = "width" if self.isVertical() else "height"
        return getattr(view.bounds().size, dim) > min_thickness

    def show_view(self, index, thickness):
        view = self.subviews()[index]
        rect = view.frame()
        dim, org = ("width", "x") if self.isVertical() else ("height", "y")
        thick = getattr(rect.size, dim)
        if thick >= thickness:
            return
        if index == 1:
            setattr(rect.origin, org, getattr(rect.origin, org) - thickness)
        setattr(rect.size, dim, thickness)
        self._animate_view(view, rect, self.animation_delegate)

    def hide_view(self, index):
        view = self.subviews()[index]
        rect = view.frame()
        dim, org = ("width", "x") if self.isVertical() else ("height", "y")
        thick = getattr(rect.size, dim)
        if thick == 0.0:
            return
        if index == 1:
            setattr(rect.origin, org, getattr(rect.origin, org) + thick)
        setattr(rect.size, dim, 0.0)
        self._animate_view(view, rect)

    def _animate_view(self, view, rect, delegate=None):
        resize = fn.NSDictionary.dictionaryWithObjectsAndKeys_(
            view, ak.NSViewAnimationTargetKey,
            fn.NSValue.valueWithRect_(rect), ak.NSViewAnimationEndFrameKey,
            None,
        )
        anims = fn.NSArray.arrayWithObject_(resize)
        animation = ak.NSViewAnimation.alloc().initWithViewAnimations_(anims)
        animation.setDuration_(0.5)
        if delegate is not None:
            animation.setDelegate_(delegate)
        animation.startAnimation()


class RedrawOnAnimationEndedDelegate(fn.NSObject):

    @objc.namedSelector(b"init:")
    def init(self, view):
        super(RedrawOnAnimationEndedDelegate, self).init()
        self.view = view
        return self

    def animationDidEnd_(self, animation):
        self.view.setNeedsDisplay_(True)

    def animationDidStop_(self, animation):
        self.view.setNeedsDisplay_(True)


# TODO fix MailStyle...View covers SliderImageView when resizing the splitview too small (to the left)
# TODO combine MailStyle...View and SliderImageView into a single view -
#    Draw the left, center, and right sides of the view independently
# TODO fix bug: SliderImageView cannot collapse/uncollapse its splitview

from editxt.util import load_image

class SliderImageView(ak.NSImageView):

    splitView = objc.IBOutlet()

    def awakeFromNib(self):
        self.setImage_(load_image("docsbar-sizer.png"))

    def mouseDown_(self, event):
        self.splitView.mouseDown_(event)

    def mouseDragged_(self, event):
        self.splitView.mouseDragged_(event)


class MailStyleFunctioBarBackgroundView(ak.NSImageView):

    def initWithFrame_(self, frame):
        super(MailStyleFunctioBarBackgroundView, self).initWithFrame_(frame)
        self.bgimage = load_image("docsbar-blank.png")
        return self

    def drawRect_(self, rect):
        img = self.bgimage
        rct = fn.NSMakeRect(0, 0, img.size().width, img.size().height)
        img.drawInRect_fromRect_operation_fraction_(
            self.bounds(), rct, ak.NSCompositeSourceAtop, 1.0)
        super(MailStyleFunctioBarBackgroundView, self).drawRect_(rect)
