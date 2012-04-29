# -*- coding: utf-8 -*-
# EditXT
# Copyright (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
import time

import objc
from AppKit import *
from Foundation import *

log = logging.getLogger("editxt.controls.tableview")


class TableView(NSOutlineView):
    # no longer in use?

    def initWithCoder_(self, coder):
        log.debug("TableView.initWithCoder_")
        self = super(TableView, self).initWithCoder_(coder)
        self.configureTracking()
        return self

    def initWithFrame_(self, frame):
        log.debug("TableView.initWithFrame_")
        self = super(TableView, self).initWithFrame_(frame)
        self.configureTracking()
        return self

    def awakeFromNib(self):
        self.configureTracking()
        self.windowAcceptsMouseEvents = self.window().acceptsMouseMovedEvents()

    def configureTracking(self):
        self._trackMouseEvents = True
        self.trackingTag = -1
        self.mouseRow = -1
        self.mouseCol = -1
        self.resetCursorRects()

    def dealloc(self):
        if self.trackingTag != -1:
            self.removeTrackingRect_(self.trackingTag)
            self.trackingTag = -1
        super(TableView, self).dealloc()

    def _get_windowAcceptsMouseEvents(self):
        value = getattr(self, "_windowAcceptsMouseEvents", None)
        if value is None:
            value = self.window().acceptsMouseMovedEvents()
            self._windowAcceptsMouseEvents = value
        return value
    def _set_windowAcceptsMouseEvents(self, value):
        self._windowAcceptsMouseEvents = value
    windowAcceptsMouseEvents = property(
        _get_windowAcceptsMouseEvents, _set_windowAcceptsMouseEvents)

    def trackMouseEvents(self):
        return self._trackMouseEvents

    def setTrackMouseEvents_(self, value):
        self._trackMouseEvents = value
        self.resetCursorRects()

    def viewWillMoveToSuperview_(self, view):
        if self.trackingTag != -1:
            # remove old tracking rects when we change superviews
            self.removeTrackingRect_(self.trackingTag)
            self.trackingTag = -1
            self.window().setAcceptsMouseMovedEvents_(self.windowAcceptsMouseEvents)
            self.window().removeMouseMovedResponder_(self)
        super(TableView, self).viewWillMoveToSuperview_(view)

    def viewDidMoveToSuperview(self):
        super(TableView, self).viewDidMoveToSuperview()
        self.resetCursorRects()

    def viewWillMoveToWindow_(self, window):
        if self.trackingTag != -1:
            self.removeTrackingRect_(self.trackingTag)
            self.trackingTag = -1
            self.window().setAcceptsMouseMovedEvents_(self.windowAcceptsMouseEvents)
            self.window().removeMouseMovedResponder_(self)
        super(TableView, self).viewWillMoveToWindow_(window)

    def viewDidMoveToWindow(self):
        super(TableView, self).viewDidMoveToWindow()
        self.resetCursorRects()

    def frameDidChange_(self, notification):
        self.resetCursorRects()

    def resetCursorRects(self):
        # stop any existing tracking
        if self.trackingTag != -1:
            self.removeTrackingRect_(self.trackingTag)
            self.trackingTag = -1
            self.window().setAcceptsMouseMovedEvents_(self.windowAcceptsMouseEvents)
            self.window().removeMouseMovedResponder_(self)

        # Add a tracking rect if our superview and window are ready
        if self.trackMouseEvents() and self.superview() and self.window():
            event = NSApp().currentEvent()
            if event is not None:
                mloc = self.convertPoint_fromView_(event.locationInWindow(), None)
                rect = self.bounds()
                inside = self.mouse_inRect_(mloc, rect)

                self.trackingTag = self.addTrackingRect_owner_userData_assumeInside_(
                    rect, self, 0, inside)
                if inside:
                    self.mouseEntered_(None)

    def mouseEntered_(self, event):
        self.windowAcceptsMouseEvents = self.window().acceptsMouseMovedEvents()
        self.window().setAcceptsMouseMovedEvents_(True)
        self.window().addMouseMovedResponder_(self)
        super(TableView, self).mouseEntered_(event)

    def mouseExited_(self, event):
        self.window().setAcceptsMouseMovedEvents_(self.windowAcceptsMouseEvents)
        self.window().removeMouseMovedResponder_(self)
        self.mouseMoved_(event)
        super(TableView, self).mouseExited_(event)

    def exitPreviousCell(self):
        if self.mouseRow != -1 and self.mouseCol != -1:
            col = self.tableColumns().objectAtIndex_(self.mouseCol)
            cell = col.dataCell()
            #self.delegate().tableView_willDisplayCell_forTableColumn_row_(self, cell, col, self.mouseRow)

            if isinstance(cell, HoverButtonCell):
                frame = self.frameOfCellAtColumn_row_(self.mouseCol, self.mouseRow)
                if cell.mouseExitedInvalidatesForFrame_(frame):
                    #cell.drawWithFrame_inView_(frame, self)
                    self.setNeedsDisplayInRect_(frame)
            self.mouseRow = -1
            self.mouseCol = -1

    def mouseDown_(self, event):
        cevent = event
        emask = NSLeftMouseDraggedMask | NSLeftMouseUpMask
        future = NSDate.distantFuture()
        while True:
            etype = cevent.type()
            point = self.convertPoint_fromView_(
                cevent.locationInWindow(), self.window().contentView())
            row = self.rowAtPoint_(point)
            col = self.columnAtPoint_(point)

            if row < 0 or col < 0:
                break # defer to standard mouseDown
            else:
                column = self.tableColumns().objectAtIndex_(col)
                cell = column.dataCell()

                if not isinstance(cell, HoverButtonCell):
                    break # defer to standard mouseDown

                # update cell according to the delegate
                #self.delegate().tableView_willDisplayCell_forTableColumn_row_(
                #    self, cell, column, row)
                cellFrame = self.frameOfCellAtColumn_row_(col, row)

            redraw = False
            finished = False
            if etype == NSLeftMouseDown:
                finished, redraw = cell.trackMouseAtPoint_invalidatesForFrame_redraw_(
                    point, cellFrame, redraw)
                finished = not finished
            elif etype == NSLeftMouseDragged:
                finished, redraw = cell.continueTrackingMouseAtPoint_invalidatesForFrame_redraw_(
                    point, cellFrame, redraw)
                finished = not finished
            elif etype == NSLeftMouseUp:
                redraw = cell.mouseUpAtPoint_invalidatesForFrame_(point, cellFrame)
                finished = True
            else:
                #raise NSException("Invalid event type: %s" % etype)
                log.error("Invalid event type: %s", etype)
                break

            if redraw:
                #cell.drawWithFrame_inView_(cellFrame, self)
                self.setNeedsDisplayInRect_(cellFrame)

            if finished: break

            cevent = self.window().nextEventMatchingMask_untilDate_inMode_dequeue_(
                emask, future, NSEventTrackingRunLoopMode, True)
            if cevent is None:
                break

        # if no events were processed, call the table view implemenation
        if cevent is event: super(TableView, self).mouseDown_(event)

    def mouseMoved_(self, event):
        point = self.convertPoint_fromView_(
            event.locationInWindow(), self.window().contentView())
        row = self.rowAtPoint_(point)
        col = self.columnAtPoint_(point)

        cellChange = self.mouseRow != row or self.mouseCol != col
        if cellChange: self.exitPreviousCell()

        if row >= 0 and col >= 0:
            column = self.tableColumns().objectAtIndex_(col)
            cell = column.dataCell()
            if isinstance(cell, HoverButtonCell):
                frame = self.frameOfCellAtColumn_row_(col, row)
                redraw = False

                # update the cell according to the delegate
                #self.delegate().tableView_willDisplayCell_forTableColumn_row_(self, cell, column, row)

                # process mouse entered if needed
                if cellChange:
                    redraw = cell.mouseEnteredInvalidatesForFrame_(frame)

                # adjusting because these numbers appear to be off slightly
                redraw = cell.mouseMoveToPoint_invalidatesForFrame_(point, frame) or redraw

                if redraw:
                    #cell.drawWithFrame_inView_(frame, self)
                    self.setNeedsDisplayInRect_(frame)

        self.mouseRow = row
        self.mouseCol = col
        # calling super would cause an infinite loop
        # since we're not registered as the first responder
