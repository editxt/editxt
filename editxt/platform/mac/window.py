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
import os

import objc
import AppKit as ak
import Foundation as fn
from objc import super
from PyObjCTools import AppHelper

import editxt.constants as const
from editxt.events import eventize
from editxt.util import untested, representedObject, short_path, WeakProperty

from .alert import Alert
from .constants import ESCAPE
from .font import get_font_from_view
from .views.commandview import ContentSizedTextView, get_attributed_string

log = logging.getLogger(__name__)


class WindowController(ak.NSWindowController):

    # 2013-11-23 08:56:28.994 EditXTDev[47194:707] An instance 0x10675fc30 of
    # class _KVOList was deallocated while key value observers were still
    # registered with it. Observation info was leaked, and may even become
    # mistakenly attached to some other object. Set a breakpoint on
    # NSKVODeallocateBreak to stop here in the debugger.
    #window_ = WeakProperty()

    docsController = objc.IBOutlet()
    docsScrollview = objc.IBOutlet()
    docsView = objc.IBOutlet()
    mainView = objc.IBOutlet()
    splitView = objc.IBOutlet()
    plusButton = objc.IBOutlet()
    propsView = objc.IBOutlet()
    propsViewButton = objc.IBOutlet()

    def __new__(cls, window):
        wc = cls.alloc().initWithWindowNibName_("EditorWindow")
        wc.window_ = window
        wc.sheet_caller = None
        return wc

    @property
    def frame_string(self):
        return self.window().stringWithSavedFrame()
    @frame_string.setter
    def frame_string(self, value):
        self.window().setFrameFromString_(value)
        self.setShouldCascadeWindows_(False)

    @property
    def splitter_pos(self):
        return self.splitView.fixedSideThickness()
    @splitter_pos.setter
    def splitter_pos(self, value):
        self.splitView.setFixedSideThickness_(value)
        self.docsView.sizeLastColumnToFit()

    @property
    def properties_hidden(self):
        return (self.propsViewButton.state() == ak.NSOnState)
    @properties_hidden.setter
    def properties_hidden(self, value):
        if value:
            # REFACTOR eliminate boilerplate here (similar to toggle_properties_pane)
            self.propsViewButton.setState_(ak.NSOnState)
            tree_view = self.docsScrollview
            prop_view = self.propsView
            tree_rect = tree_view.frame()
            prop_rect = prop_view.frame()
            tree_rect.size.height += prop_rect.size.height - 1.0
            tree_rect.origin.y = prop_rect.origin.y
            tree_view.setFrame_(tree_rect)
            prop_rect.size.height = 0.0
            prop_view.setFrame_(prop_rect)

    def setDocument_(self, value):
        raise NotImplementedError("should never be called")

    def windowDidLoad(self):
        self.window_.window_did_load()
        self.window().setDelegate_(self)

    def characterEncodings(self):
        return fn.NSValueTransformer.valueTransformerForName_("CharacterEncodingTransformer").names

    def setCharacterEncodings_(self, value):
        pass

    def syntaxDefNames(self):
        return [d.name for d in self.window_.app.syntaxdefs]

    def setSyntaxDefNames_(self, value):
        pass

    def projects(self):
        return self.window_.projects

    def openDocument_(self, sender):
        self.window_.open_documents()

    def saveDocument_(self, sender):
        self.window_.save()

    def saveDocumentAs_(self, sender):
        self.window_.save_as()

    def revertDocumentToSaved_(self, sender):
        self.window_.reload_current_document()

    def newProject_(self, sender):
        self.window_.new_project()

    def togglePropertiesPane_(self, sender):
        self.window_.toggle_properties_pane()

    def doMenuCommand_(self, sender):
        self.window_.do_menu_command(sender)

    def doCommandBySelector_(self, selector):
        editor = self.window_.current_editor
        if editor is not None:
            # 'cancelOperation:' gets converted to 'cancel:'; convert it back
            sel = ESCAPE if selector == "cancel:" else selector
            if editor.do_command(sel):
                return
        super().doCommandBySelector_(selector)

    def validateUserInterfaceItem_(self, item):
        if item.action() == "doMenuCommand:":
            return self.window_.validate_menu_command(item)
        # TODO implement validation for commands in file menu, etc.
        return True

    def outlineViewSelectionDidChange_(self, notification):
        self.window_.selected_editor_changed()

    def outlineViewItemDidCollapse_(self, notification):
        representedObject(notification.userInfo()["NSObject"]).expanded = False

    def outlineViewItemDidExpand_(self, notification):
        representedObject(notification.userInfo()["NSObject"]).expanded = True

    def outlineView_shouldSelectItem_(self, outlineview, item):
        return self.window_.should_select_item(outlineview, item)

    def outlineView_willDisplayCell_forTableColumn_item_(self, view, cell, col, item):
        editor = cell.editor = representedObject(item)
        if col.identifier() == "name":
            cell.setImage_(editor.icon())

    def outlineView_shouldEditTableColumn_item_(self, view, col, item):
        return self.window_.should_edit_item(col, item)

    def outlineView_toolTipForCell_rect_tableColumn_item_mouseLocation_(
        self, view, cell, rect, col, item, mouseloc):
        return self.window_.tooltip_for_item(view, item), rect

    def setup_current_editor(self, editor):
        """Setup the current editor in the window

        :returns: True if the editor was setup, otherwise False.
        """
        main_view = self.mainView
        self._update_title(editor)
        if editor is not None:
            sel = self.selected_items
            if not sel or sel[0] is not editor:
                self.selected_items = [editor]
            if editor.main_view not in main_view.subviews():
                for subview in main_view.subviews():
                    subview.removeFromSuperview()
                editor.set_main_view_of_window(main_view, self.window())
                return True
        for subview in main_view.subviews():
            subview.removeFromSuperview()
        return False

    def is_current_view(self, editor_main_view):
        if editor_main_view is None:
            return False
        return editor_main_view.isDescendantOf_(self.mainView)

    @property
    def selected_items(self):
        return self.docsController.selected_objects
    @selected_items.setter
    def selected_items(self, items):
        self.docsController.selected_objects = items

    def on_dirty_status_changed(self, editor, dirty):
        self.setDocumentEdited_(dirty)
        self.docsView.item_needs_display(editor)

    def _update_title(self, editor):
        title = self.windowTitleForDocumentDisplayName_("")
        if editor is not None and editor.file_path and os.path.isabs(editor.file_path):
            url = fn.NSURL.fileURLWithPath_(editor.file_path)
        else:
            url = None
        self.window().setTitle_(title)
        self.window().setRepresentedURL_(url)

    def windowTitleForDocumentDisplayName_(self, name):
        editor = self.window_.current_editor
        if editor is not None:
            if editor.file_path is not None:
                return short_path(editor.file_path, editor)
            return editor.name or name
        return name

    def windowWillReturnUndoManager_(self, window):
        return self.window_.undo_manager

    def windowDidBecomeKey_(self, notification):
        self.window_.window_did_become_key(notification.object())

    def windowShouldClose_(self, window):
        return self.window_.should_close(window.close)

    def windowWillClose_(self, notification):
        self.window_.window_will_close()
        self.window().setDelegate_(None)

    def open_documents(self, directory, filename, open_paths_callback):
        panel = ak.NSOpenPanel.alloc().init()
        panel.setShowsHiddenFiles_(True)
        panel.setExtensionHidden_(False)
        panel.setAllowsMultipleSelection_(True)
        panel.setTreatsFilePackagesAsDirectories_(True)
        assert self.sheet_caller == None, "window cannot process two sheets at once"
        def callback(sheet, code):
            if code == ak.NSOKButton:
                paths = [url.path() for url in sheet.URLs()]
                open_paths_callback(paths)
            self.sheet_caller = None
        self.sheet_caller = SheetCaller.alloc().init(callback)
        panel.beginSheetForDirectory_file_modalForWindow_modalDelegate_didEndSelector_contextInfo_(
            directory, filename, self.window(),
            self.sheet_caller, "sheetDidEnd:returnCode:contextInfo:", 0)

    def save_document_as(self, directory, filename, save_with_path):
        panel = ak.NSSavePanel.alloc().init()
        panel.setShowsHiddenFiles_(True)
        panel.setExtensionHidden_(False)
        panel.setTreatsFilePackagesAsDirectories_(True)
        assert self.sheet_caller == None, "window cannot save two files at once"
        def callback(sheet, code):
            sheet.orderOut_(panel)
            if code == ak.NSOKButton:
                path = sheet.URL().path()
                save_with_path(path)
            self.sheet_caller = None
        self.sheet_caller = SheetCaller.alloc().init(callback)
        panel.beginSheetForDirectory_file_modalForWindow_modalDelegate_didEndSelector_contextInfo_(
            directory, filename, self.window(),
            self.sheet_caller, "sheetDidEnd:returnCode:contextInfo:", 0)

    def prompt_to_overwrite(self, file_path, save_with_path, save_as, diff_with_original):
        self.alert = alert = Alert.alloc().init()
        alert.setAlertStyle_(ak.NSInformationalAlertStyle)
        alert.setMessageText_("Replace “{}”?".format(file_path))
        alert.setInformativeText_("The file has been modified by another program.")
        alert.addButtonWithTitle_("Save As...")
        alert.addButtonWithTitle_("Replace")
        # may need to use .objectAtIndex_(1) instead of [1]
        # http://stackoverflow.com/questions/16627894/how-to-make-the-nsalerts-2nd-button-the-return-button
        alert.buttons()[1].setKeyEquivalent_(" ") # space bar -> replace
        diff = diff_with_original is not None
        if diff:
            alert.addButtonWithTitle_("Diff")
            alert.buttons()[2].setKeyEquivalent_("d")
        alert.addButtonWithTitle_("Cancel")
        def respond(response, end_alert):
            if response == ak.NSAlertFirstButtonReturn:
                end_alert()
                save_as()
            elif response == ak.NSAlertSecondButtonReturn:
                end_alert()
                save_with_path(file_path)
            elif diff and response == ak.NSAlertThirdButtonReturn:
                diff_with_original()
            else:
                end_alert()
                save_with_path(None)
        alert.beginSheetModalForWindow_withCallback_(self.window(), respond)

    def prompt_to_close(self, file_path, save_discard_or_cancel, save_as):
        self.alert = alert = Alert.alloc().init()
        alert.setAlertStyle_(ak.NSInformationalAlertStyle)
        message = "Do you want to save the changes made to the document “{}”?" \
                  .format(os.path.basename(file_path))
        alert.setMessageText_(message)
        alert.setInformativeText_("Your changes will be lost if you don’t save them.")
        alert.addButtonWithTitle_("Save" + ("..." if save_as else ""))
        alert.addButtonWithTitle_("Cancel")
        alert.addButtonWithTitle_("Don't Save")
        # may need to use .objectAtIndex_(2) instead of [2]
        # http://stackoverflow.com/questions/16627894/how-to-make-the-nsalerts-2nd-button-the-return-button
        alert.buttons()[2].setKeyEquivalent_(" ") # space bar -> don't save
        def respond(response, end_alert):
            if response == ak.NSAlertFirstButtonReturn:
                end_alert()
                save_discard_or_cancel(True) # save
            elif response == ak.NSAlertThirdButtonReturn:
                end_alert()
                save_discard_or_cancel(False) # discard
            else:
                end_alert()
                save_discard_or_cancel(None) # cancel
        alert.beginSheetModalForWindow_withCallback_(self.window(), respond)

    # outlineview datasource methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def outlineView_writeItems_toPasteboard_(self, view, items, pboard):
        real_items = [view.realItemForOpaqueItem_(item) for item in items]
        pairs = self.window_.get_id_path_pairs(real_items)
        ids = [p[0] for p in pairs]
        paths = [p[1] for p in pairs if p[1] is not None]
        if pairs:
            pboard.clearContents()
            pboard.setPropertyList_forType_(ids, const.DOC_ID_LIST_PBOARD_TYPE)
            if len(ids) == len(paths):
                assert pboard.writeObjects_([fn.NSURL.fileURLWithPath_(p) for p in paths])
                assert pboard.writeObjects_([fn.NSString.stringWithString_(p) for p in paths])
        return bool(pairs)

    DROP_ACTIONS = {
        ak.NSDragOperationCopy: const.COPY,
        ak.NSDragOperationGeneric: None,
    }

    def outlineView_acceptDrop_item_childIndex_(self, view, info, item, index):
        pboard = info.draggingPasteboard()
        parent = None if item is None else representedObject(item)
        # move unless modifier specifies copy or generic insert (copy unless present)
        action = self.DROP_ACTIONS.get(info.draggingSourceOperationMask(), const.MOVE)
        return self.window_.accept_drop(view, pboard, parent, index, action)

    def outlineView_validateDrop_proposedItem_proposedChildIndex_(self, view, info, item, index):
        return self.window_.validate_drop(view, info, item, index)

    # def outlineView_namesOfPromisedFilesDroppedAtDestination_forDraggedItems_(
    #   self, view, names, items):
    #   item = representedObject(item)
    #   raise NotImplementedError

    # the following are dummy implementations since we are using bindings (they
    # are required since we are using NSOutlineView's drag/drop datasource methods)
    # see: http://theocacao.com/document.page/130

    def outlineView_child_ofItem_(self, view, index, item):
        return None

    def outlineView_isItemExpandable_(self, view, item):
        return False

    def outlineView_numberOfChildrenOfItem_(self, view, item):
        return 0

    def outlineView_objectValueForTableColumn_byItem_(self, view, col, item):
        return None


class SheetCaller(fn.NSObject):

    @objc.namedSelector(b"init:")
    def init(self, callback):
        self = super(SheetCaller, self).init()
        self.callback = callback
        return self

    @objc.typedSelector(b'v@:@ii')
    def sheetDidEnd_returnCode_contextInfo_(self, sheet, code, context):
        self.callback(sheet, code)


class EditorWindow(ak.NSWindow):
    pass
#    """NSWindow subclass that provides mouseMoved events to registered subviews"""
#
#    @property
#    def mouse_moved_responders(self):
#        try:
#            mmr = self._mouse_moved_responders
#        except AttributeError:
#            mmr = self._mouse_moved_responders = set()
#        return mmr
#
#    def add_mouse_moved_responder(self, responder):
#        self.mouse_moved_responders.add(responder)
#        self.setAcceptsMouseMovedEvents_(True)
#
#    def remove_mouse_moved_responder(self, responder):
#        self.mouse_moved_responders.discard(responder)
#        if not self.mouse_moved_responders:
#            self.setAcceptsMouseMovedEvents_(False)
#
#    def mouseMoved_(self, event):
#        super(EditorWindow, self).mouseMoved_(event)
#        for responder in self.mouse_moved_responders:
#            if responder is not self.firstResponder():
#                responder.mouseMoved_(event)


class OutputPanel(ak.NSPanel):

    handle_close = None

    class events:
        close = eventize.attr("handle_close")

    def __new__(cls, command, text, rect=None):
        self = cls.alloc().init_(rect)
        self.command = command
        self.text = text
        eventize(self)
        return self

    def init_(self, rect):
        if rect is None:
            rect = ak.NSMakeRect(100, 100, 400, 300)
        style = (
            ak.NSHUDWindowMask | ak.NSUtilityWindowMask |
            ak.NSTitledWindowMask | ak.NSClosableWindowMask |
            ak.NSResizableWindowMask | ak.NSNonactivatingPanelMask
        )
        self = super().initWithContentRect_styleMask_backing_defer_(
            rect, style, ak.NSBackingStoreBuffered, True)
        frame = self.frame()
        self.textview = textview = ContentSizedTextView.alloc().initWithFrame_(frame)
        textview.setEditable_(False)
        textview.setSelectable_(True)
        textview.setLinkTextAttributes_({
            ak.NSCursorAttributeName: ak.NSCursor.pointingHandCursor()
        })
        textview.setDelegate_(self)

        self.scroller = scroller = ak.NSScrollView.alloc().initWithFrame_(frame)
        scroller.setHasHorizontalScroller_(False)
        scroller.setHasVerticalScroller_(True)
        scroller.setAutohidesScrollers_(True)
        scroller.setAutoresizingMask_(
            ak.NSViewWidthSizable | ak.NSViewHeightSizable)
        container = textview.textContainer()
        #size = scroller.contentSize()
        container.setContainerSize_(
            ak.NSMakeSize(frame.size.width, const.LARGE_NUMBER_FOR_TEXT))
        container.setWidthTracksTextView_(True)
        textview.setHorizontallyResizable_(False)
        textview.setAutoresizingMask_(
            ak.NSViewWidthSizable | ak.NSViewHeightSizable)
        scroller.setDocumentView_(textview)
        self.setContentView_(scroller)

        self.setBecomesKeyOnlyIfNeeded_(True)
        self.setReleasedWhenClosed_(True)
        self.setHidesOnDeactivate_(False)
        self.setLevel_(ak.NSNormalWindowLevel)
        self.spinner = None
        self.app = None
        return self

    def dealloc(self):
        if self.app is not None and self in self.app.panels:
            self.app.panels.remove(self)
            self.app = None
        self.textview = None
        self.scroller = None
        self.spinner = None
        self.command = None
        super().dealloc()

    def show(self, window):
        self.app = app = window.app
        if self not in app.panels:
            app.panels.append(self)
        point = window.wc.window().frame().origin
        self.orderFront_(window)

    def append_message(self, message, textview=None, msg_type=const.INFO):
        if not message:
            return
        font = get_font_from_view(textview, self.app)
        text = get_attributed_string(message, msg_type, font.font)
        self.textview.font_smoothing = font.smooth
        self.textview.append_text(text)

    def is_waiting(self, waiting=None):
        if waiting is not None:
            self.waiting = waiting
            if waiting:
                if self.spinner is None:
                    rect = ak.NSMakeRect(
                        self.textview.frame().size.width - 18,  # right
                        2,   # top
                        16,  # width
                        16,  # height
                    )
                    self.spinner = ak.NSProgressIndicator.alloc().initWithFrame_(rect)
                    self.spinner.setControlSize_(ak.NSSmallControlSize)
                    self.spinner.setStyle_(ak.NSProgressIndicatorSpinningStyle)
                    self.textview.addSubview_(self.spinner)
                elif self.spinner.isHidden():
                    self.spinner.setHidden_(False)
                self.spinner.startAnimation_(self)
            elif self.spinner is not None:
                self.spinner.setHidden_(True)
                self.spinner.stopAnimation_(self)
        return getattr(self, "waiting", False)

    @property
    def text(self):
        return self.textview.textStorage()

    @text.setter
    def text(self, value):
        self.textview.textStorage().setAttributedString_(value)

    def textView_clickedOnLink_atIndex_(self, textview, link, index):
        event = ak.NSApp.currentEvent()
        meta = bool(event.modifierFlags() & ak.NSCommandKeyMask)
        return self.command.handle_link(str(link), meta)

    def close(self):
        if self.handle_close is not None:
            self.handle_close()
        return super().close()
