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
import os
import re
from collections import defaultdict
from itertools import chain, izip, count

from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt.util import register_undo_callback

log = logging.getLogger("editxt.textcommand")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Text command system interface

"""
The primary interface for loading text commands into EditXT is a module-level
function that returns a list of command objects provided by the module:

def load_commands():
    return [
        TextCommandInstance(),
    ]
"""

class TextCommand(object):

    def title(self):
        """Return the title of this command (a unicode string)"""
        raise NotImplementedError()

    def preferred_hotkey(self):
        """Get the preferred hotkey for this text command

        Returns a tuple or None. If a tuple is returned it should contain two
        values: (<key string>, <modifier mask>). For more info see NSMenuItem
        setKeyEquivalent: and setKeyEquivalentModifierMask: in the Cocoa
        documentation.
        """
        return None # no hotkey by default

    def is_enabled(self, textview, sender):
        return True

    def execute(self, textview, sender):
        raise NotImplementedError()

    def tag(self):
        return self._TextCommandController__tag


SEPARATOR = object()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Built-in text commands

def load_commands():
    return dict(
        #document_menu_commands=[],

        # A list of TextCommand arguments
        text_menu_commands=[
            CommentText(),
            IndentLine(),
            DedentLine(),
            SortLines(),
            ChangeIndentation(),
        ],

        # A dict of of NSResponder selectors mapped to callbacks
        #
        # Each callback should have the same signature as TextCommand.execute
        # The second argument (sender) will always be None when executed in
        # this context.
        input_handlers={
            "insertTab:": tab_indent,
            "insertBacktab:": tab_dedent,
            "insertNewline:": insert_newline,
            "moveToBeginningOfLine:": move_to_beginning_of_line,
            "moveToLeftEndOfLine:": move_to_beginning_of_line,
            #"moveToBeginningOfLineAndModifySelection:":
            #    select_to_beginning_of_line,
            "deleteBackward:": delete_backward,
            #"deleteForward:": delete_forward,
        }
    )


class SelectionCommand(TextCommand):

    def is_enabled(self, textview, sender):
        return textview.selectedRange().length > 0


class CommentText(SelectionCommand):

    def title(self):
        return u"(Un)comment Selected Lines"

    def preferred_hotkey(self):
        return (",", NSCommandKeyMask)

    def execute(self, textview, sender):
        text = textview.string()
        sel = text.lineRangeForRange_(textview.selectedRange())
        comment_token = textview.doc_view.document.comment_token
        if is_comment_range(text, sel, comment_token):
            func = uncomment_line
        else:
            func = comment_line
        args = (
            comment_token,
            textview.doc_view.document.indent_mode,
            textview.doc_view.document.indent_size,
        )
        seltext = u"".join(func(line, *args) for line in iterlines(text, sel))
        if textview.shouldChangeTextInRange_replacementString_(sel, seltext):
            textview.textStorage().replaceCharactersInRange_withString_(sel, seltext)
            textview.setSelectedRange_((sel[0], len(seltext)))
            textview.didChangeText()

def is_comment_range(text, range, comment_token):
    comments = 0
    for i, line in enumerate(iterlines(text, range)):
        if i > 1:
            break
        if line.strip().startswith(comment_token):
            comments += 1
    return comments == 2 or (i < 1 and comments)

def comment_line(text, token, indent_mode, indent_size):
    if indent_mode == const.INDENT_MODE_SPACE:
        lentoken = len(token)
        prespace = len(text) - len(text.lstrip(u" "))
        if lentoken + 1 < indent_size and prespace:
            return token + text[lentoken:]
        elif lentoken < indent_size and prespace:
            prefix = token
        else:
            prefix = token + u" "
    else:
        prefix = token + u" "
    return prefix + text

def uncomment_line(text, token, indent_mode, indent_size):
    line = text
    nolead = text.lstrip()
    if nolead.startswith(token):
        lentoken = len(token)
        if nolead[lentoken] == u" ":
            lentoken += 1
        line = nolead[lentoken:]
        lentoken = len(text) - len(nolead)
        if lentoken > 0:
            line = text[:lentoken] + line
        if indent_mode == const.INDENT_MODE_SPACE:
            prespace = len(line) - len(line.lstrip(u" "))
            fillchars = indent_size - (prespace % indent_size)
            if fillchars != indent_size:
                line = u" " * fillchars + line
    return line


class IndentLine(SelectionCommand):

    name = "tabIndent"

    def title(self):
        return u"Indent Selected Lines"

    def preferred_hotkey(self):
        return ("]", NSCommandKeyMask)

    def execute(self, textview, sender):
        tab_indent(textview, sender)


class DedentLine(TextCommand):

    name = "tabDedent"

    def title(self):
        return u"Un-indent Selected Lines"

    def preferred_hotkey(self):
        return ("[", NSCommandKeyMask)

    def execute(self, textview, sender):
        tab_dedent(textview, sender)


class SortLines(TextCommand):

    name = "sortLines"

    def title(self):
        return u"Sort Lines"

    def preferred_hotkey(self):
        return None

    def execute(self, textview, sender):
        from editxt.sortlines import SortLinesController
        SortLinesController.create_with_textview(textview).begin_sheet(sender)


class ChangeIndentation(TextCommand):

    name = "changeIndentation"

    def title(self):
        return u"Change Indentation"

    def preferred_hotkey(self):
        return None

    def execute(self, textview, sender):
        from editxt.changeindent import ChangeIndentationController
        ctl = ChangeIndentationController.create_with_textview(textview)
        ctl.begin_sheet(sender)


def tab_indent(textview, sender):
    indent_mode = textview.doc_view.document.indent_mode
    if indent_mode == const.INDENT_MODE_TAB:
        istr = u"\t"
    else:
        istr = u" " * textview.doc_view.document.indent_size
    sel = textview.selectedRange()
    text = textview.string()
    if sel.length == 0:
        size = len(istr)
        if size == 1:
            seltext = istr
        else:
            line_start = text.lineRangeForRange_(sel).location
            seltext = istr[:size - (sel.location - line_start) % size]
        select = False
    else:
        def indent(line):
            if line.strip():
                return istr + line
            return line.lstrip(u" \t")
        sel = text.lineRangeForRange_(sel)
        seltext = u"".join(indent(line) for line in iterlines(text, sel))
        select = True
    if textview.shouldChangeTextInRange_replacementString_(sel, seltext):
        textview.textStorage().replaceCharactersInRange_withString_(sel, seltext)
        textview.didChangeText()
        if select:
            textview.setSelectedRange_((sel[0], len(seltext)))
        else:
            textview.scrollRangeToVisible_((sel[0] + len(seltext), 0))

def tab_dedent(textview, sender):
    def dedent(line, spt=textview.doc_view.document.indent_size):
        if not line.strip():
            return line.lstrip(u" \t")
        if line.startswith(u"\t"):
            return line[1:]
        remove = 0
        linelen = len(line)
        for i in xrange(spt):
            if i < linelen and line[i] == u" ":
                remove += 1
            else:
                break
        return line[remove:]
    text = textview.string()
    sel = text.lineRangeForRange_(textview.selectedRange())
    seltext = u"".join(dedent(line) for line in iterlines(text, sel))
    if len(seltext) != sel.length:
        if textview.shouldChangeTextInRange_replacementString_(sel, seltext):
            textview.textStorage().replaceCharactersInRange_withString_(sel, seltext)
            textview.setSelectedRange_((sel[0], len(seltext)))
            textview.didChangeText()

_ws = re.compile(ur"([\t ]+)", re.UNICODE | re.MULTILINE)

def insert_newline(textview, sender):
    eol = textview.doc_view.document.eol
    sel = textview.selectedRange()
    text = textview.string()
    if sel.location > 0:
        i = text.rfind(eol, 0, sel[0])
        i = 0 if i < 0 else (i + len(eol))
        indent = _ws.match(text, i)
        if indent:
            eol += indent.group()[:sel[0]-i]
        if i != sel[0]:
            wslead = _ws.match(text, sel[0])
            if wslead:
                sel[1] += len(wslead.group())
    if textview.shouldChangeTextInRange_replacementString_(sel, eol):
        textview.textStorage().replaceCharactersInRange_withString_(sel, eol)
        textview.didChangeText()
        textview.scrollRangeToVisible_((sel[0] + len(eol), 0))

def move_to_beginning_of_line(textview, sender):
    eol = textview.doc_view.document.eol
    sel = textview.selectedRange()
    text = textview.string()
    if sel[0] > 0:
        i = text.rfind(eol, 0, sel[0])
        i = 0 if i < 0 else (i + len(eol))
    else:
        i = 0
    new = (i, 0)
    wslead = _ws.match(text, i)
    if wslead:
        new = (wslead.end(), 0)
    if new[0] == sel[0]:
        new = (i, 0)
    textview.setSelectedRange_(new)
    textview.scrollRangeToVisible_(new)

#def move_to_beginning_of_line_and_modify_selection(textview, sender):

def delete_backward(textview, sender):
    if textview.doc_view.document.indent_mode == const.INDENT_MODE_TAB:
        textview.deleteBackward_(sender)
        return
    sel = textview.selectedRange()
    if sel.length == 0:
        if sel.location == 0:
            return
        text = textview.string()
        i = sel[0]
        while i > 0 and text[i - 1] == u" ":
            i -= 1
        delete = sel[0] - i
        if delete < 1:
            delete = 1
        elif delete > 1:
            i = text.lineRangeForRange_((i, 0))[0]
            size = textview.doc_view.document.indent_size
            maxdel = (sel[0] - i) % size
            if maxdel == 0:
                maxdel = size
            if delete > maxdel:
                delete = maxdel
        sel = (sel[0] - delete, delete)
    if textview.shouldChangeTextInRange_replacementString_(sel, u""):
        textview.textStorage().replaceCharactersInRange_withString_(sel, u"")
        textview.didChangeText()
        textview.scrollRangeToVisible_((sel[0], 0))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Other text-mangling functions (and useful odds and ends)

# def expand_range(text, range):
#     """expand range to beginning of first selected line and end of last selected line"""
#     r = text.lineRangeForRange_(range)
#     if text[-2:] == u"\r\n":
#         r.length -= 2
#     elif text[-1] in u"\n\r\u2028":
#         r.length -= 1
#     return r


_line_splitter = re.compile(u"([^\n\r\u2028]*(?:%s)?)" % "|".join(
    eol for eol in sorted(const.EOLS.values(), key=len, reverse=True)))

def iterlines(text, range=(0,)):
    """iterate over lines of text

    By default this function iterates over all lines in the give text. If the
    'range' parameter (NSRange or tuple) is given, lines within that range will
    be yielded.
    """
    if not text:
        yield text
    else:
        if range != (0,):
            range = (range[0], sum(range))
        for line in _line_splitter.finditer(text, *range):
            if line.group():
                yield line.group()


_newlines = re.compile("|".join(
    eol for eol in sorted(const.EOLS.values(), key=len, reverse=True)))

def replace_newlines(textview, eol):
    sel = textview.selectedRange()
    text = textview.string()
    next = _newlines.sub(eol, text)
    if text == next:
        return
    range = (0, len(text))
    if textview.shouldChangeTextInRange_replacementString_(range, next):
        textview.textStorage().replaceCharactersInRange_withString_(range, next)
        textview.didChangeText()
        textview.setSelectedRange_(sel)


_indentation_regex = re.compile(u"([ \t]*)([^\r\n\u2028]*[\r\n\u2028]*)")

def change_indentation(textview, old_indent, new_indent, size):
    attr_change = (new_indent == u"\t")
    text_change = (old_indent != new_indent)
    if attr_change or text_change:
        text = next = textview.string()
        if text_change:
            #next = text.replace(old_indent, new_indent)
            # TODO detect comment characters at the beginning of a line and
            # replace indentation beyond the comment characters
            fragments = []
            for match in _indentation_regex.finditer(text):
                ws, other = match.groups()
                if ws:
                    fragments.append(ws.replace(old_indent, new_indent))
                fragments.append(other)
            next = u"".join(fragments)
        range = (0, len(text))
        if textview.shouldChangeTextInRange_replacementString_(range, next):
            if attr_change:
                textview.doc_view.document.reset_text_attributes(size)
            if text_change and text != next:
                sel = textview.selectedRange()
                textview.textStorage().replaceCharactersInRange_withString_(range, next)
                if sel[0] + sel[1] > len(next):
                    if sel[0] > len(next):
                        sel = (len(next), 0)
                    else:
                        sel = (sel[0], len(next) - sel[0])
                textview.setSelectedRange_(sel)
            textview.didChangeText()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextCommandController

class TextCommandController(object):

    def __init__(self, menu):
        self.tagger = count()
        self.menu = menu
        self.commands = commands = {}
        self.commands_by_path = bypath = defaultdict(list)
        self.input_handlers = {}
        self.editems = editems = {}
#         ntc = menu.itemAtIndex_(1) # New Text Command menu item
#         ntc.setTarget_(self)
#         ntc.setAction_("newTextCommand:")
#         etc = menu.itemAtIndex_(2).submenu() # Edit Text Command menu
        #self.load_commands()

    @classmethod
    def iter_command_modules(self):
        """Iterate text commands, yield (<command file path>, <command instance>)"""
        # load local (built-in) commands
        from editxt.textcommand import load_commands as load_locals
        yield None, load_locals()

    def load_commands(self):
        for path, reg in self.iter_command_modules():
            for command in reg.get("text_menu_commands", []):
                self.add_command(command, path)
            self.input_handlers.update(reg.get("input_handlers", {}))

    def add_command(self, command, path):
        command.__tag = tag = self.tagger.next()
        hotkey, keymask = self.validate_hotkey(command.preferred_hotkey())
        item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            command.title(), "performTextCommand:", hotkey)
        item.setKeyEquivalentModifierMask_(keymask)
        item.setTag_(tag)
        # HACK tag will not be the correct index if an item is ever removed
        self.menu.insertItem_atIndex_(item, tag)
        self.commands[tag] = command

    def validate_hotkey(self, value):
        if value is not None:
            assert len(value) == 2, "invalid hotkey tuple: %r" % (value,)
            # TODO check if a hot key is already in use; ignore if it is
            return value
        return u"", 0

    def is_textview_command_enabled(self, textview, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                return command.is_enabled(textview, sender)
            except Exception:
                log.error("%s.is_enabled failed", type(command).__name__, exc_info=True)
        return False

    def do_textview_command(self, textview, sender):
        command = self.commands.get(sender.tag())
        if command is not None:
            try:
                command.execute(textview, sender)
            except Exception:
                log.error("%s.execute failed", type(command).__name__, exc_info=True)

    def do_textview_command_by_selector(self, textview, selector):
        #log.debug(selector)
        callback = self.input_handlers.get(selector)
        if callback is not None:
            try:
                callback(textview, None)
                return True
            except Exception:
                log.error("%s failed", callback, exc_info=True)
        return False

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# OLD TextCommandController

# class TextCommandController(object):
#
#     def commandIterator(self):
#         """Iterate text commands, yield (<command file path>, <command instance>)"""
#         # load local (built-in) commands
#         for command in loadCommands():
#             name = getattr(command, "name", None)
#             if name is not None:
#                 self.namedCommands[name] = command
#             yield None, command
#         # load user commands
# #         bypath = self.commandsByPath
# #         tcpath = self.userCommandPath()
# #         for filename in sorted(os.listdir(tcpath)):
# #             if filename.endswith(".py"):
# #                 path = os.path.join(tcpath, filename)
# #                 mod =  {}
# #                 try:
# #                     execfile(path, mod)
# #                     for command in mod["loadCommands"]():
# #                         bypath[path].append(command)
# #                         yield path, command
# #                 except Exception:
# #                     log.error("cannot load text command module: %s", filename, exc_info=True)
#
#     def __init__(self, menu):
#         super(TextCommandController, self).init()
#         self.menu = menu
#         self.namedCommands = {}
#         self.commands = commands = {}
#         self.commandsByPath = bypath = defaultdict(list)
#         self.editems = editems = {}
#         ntc = menu.itemAtIndex_(1) # New Text Command menu item
#         ntc.setTarget_(self)
#         ntc.setAction_("newTextCommand:")
#         etc = menu.itemAtIndex_(2).submenu() # Edit Text Command menu
#         for ident, (path, command) in enumerate(self.commandIterator()):
#             command._tag = ident
#             item = self.createMenuItemForCommand_(command)
#             menu.insertItem_atIndex_(item, ident)
#             commands[ident] = command
#             if path is not None:
#                 editem = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
#                     command.title(), "editTextCommand:", u"")
#                 editem.setTarget_(self)
#                 editem.setTag_(ident)
#                 etc.addItem_(editem)
#                 editems[ident] = path
#         return self
#
#     def createMenuItemForCommand_(self, command):
#         hotkey, keymask = self.validateHotkey_(command.preferred_hotkey())
#         item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
#             command.title(), "performTextCommand:", hotkey)
#         item.setKeyEquivalentModifierMask_(keymask)
#         item.setTag_(command._tag)
#         return item
#
#     def userCommandPath(self):
#         sdc = NSDocumentController.sharedDocumentController()
#         aspath = sdc.appSupportPath()
#         if not os.path.exists(aspath):
#             os.mkdir(aspath)
#         tcpath = os.path.join(aspath, "TextCommands")
#         if not os.path.exists(tcpath):
#             os.mkdir(tcpath)
#         return tcpath
#
#     def newTextCommand_(self, sender):
#         sdc = NSDocumentController.sharedDocumentController()
#         project = sdc.currentProject
#         rcpath = NSBundle.mainBundle().resourcePath()
#         temp = os.path.join(rcpath, "mytextcommand.py")
#         doc = project.openDocumentWithPath_(temp)
#         if doc is None:
#             doc = project.newDocument()
#         tcpath = self.userCommandPath()
#         url = NSURL.fileURLWithPath_(os.path.join(tcpath, "mytextcommand.py"))
#         doc.setFileURL_(url)
#         doc.registerSaveHook_(self.onSaveTextCommand_)
#
#     def editTextCommand_(self, editem):
#         # get text command info from menu tag
#         path = self.editems.get(editem.tag())
#         if path is not None and os.path.exists(path):
#             sdc = NSDocumentController.sharedDocumentController()
#             project = sdc.currentProject
#             doc = project.openDocumentWithPath_(path)
#             if doc is not None:
#                 doc.registerSaveHook_(self.onSaveTextCommand_)
#
#     def onSaveTextCommand_(self, doc):
#         url = doc.fileURL()
#         if url is not None:
#             path = url.path()
#             # get commands that are about to be reloaded
#             oldcommands = list(self.commandsByPath[path])
#
#             # reload command module
#             newcommands = []
#             mod =  {}
#             try:
#                 execfile(path, mod)
#                 for command in mod["loadCommands"]():
#                     newcommands.append(command)
#             except Exception:
#                 log.error("cannot load text command module: %s", filename, exc_info=True)
#
#             # replace existing commands in menu as needed
#             offset = max(self.commands) + 1
#             addcommands = []
#             for i, newcmd in enumerate(newcommands):
#                 if i < len(oldcommands):
#                     oldcmd = oldcommands[i]
#                     index = oldcmd.tag()
#                 else:
#                     addcommands.append(newcmd)
#                     continue
#                 newcmd._tag = oldcmd.tag()
#                 hotkey, keymask = self.validateHotkey_(newcmd.preferred_hotkey())
#                 item = self.menu.itemAtIndex_(oldcmd.tag())
#                 item.setTitle_(newcmd.title())
#                 item.setKeyEquivalent_(hotkey)
#                 item.setKeyEquivalentModifierMask_(keymask)
#                 item.setTag_(oldcmd.tag())
#                 self.commands[oldcmd.tag()] = newcmd
#
#             # put new commands in menu as needed
#             offset = max(self.commands) + 1
#             for ident, command in enumerate(addcommands):
#                 ident = ident + offset
#                 command._tag = ident
#                 item = self.createMenuItemForCommand_(command)
#                 self.menu.insertItem_atIndex_(item, ident)
#                 self.commands[ident] = command
#
#     def validateHotkey_(self, keytup):
#         if keytup is not None:
#             assert len(keytup) == 2, "invalid hotkey tuple: %r" % (keytup,)
#             # TODO check if a hot key is already in use; ignore if it is
#             return keytup
#         return u"", 0
#
#     def validateTextCommand_forTextView_(self, menuitem, textview):
#         command = self.commands.get(menuitem.tag())
#         if command is not None:
#             try:
#                 return command.is_enabled(textview, menuitem)
#             except Exception:
#                 log.error("%s.is_enabled failed", type(command).__name__, exc_info=True)
#         return False
#
#     def performTextCommand_forTextView_(self, sender, textview):
#         command = self.commands.get(sender.tag())
#         if command is not None:
#             try:
#                 command.execute(textview, sender)
#             except Exception:
#                 log.error("%s.execute failed", type(command).__name__, exc_info=True)
#
#     def performNamedCommand_forTextView_(self, name, textview):
#         self.performTextCommand_forTextView_(self.namedCommands[name], textview)