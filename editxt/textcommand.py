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
import os
import re
from collections import defaultdict
from itertools import chain, izip, count

from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt.util import register_undo_callback

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Text command system interface

"""
The primary interface for loading text commands into EditXT is a module-level
function that returns a list of command functions provided by the module:

def load_commands():
    return [decorated_text_command, ...]
"""


def command(func=None, names=None, title=None, hotkey=None,
            is_enabled=None, parse_args=None, lookup_with_parse_args=False):
    """Text command decorator

    Text command signature: `text_command(textview, sender, args)`
    Both `sender` and `args` will be `None` in some contexts.

    :param names: One or more names that can be typed in the command bar to
       invoke the command. This can be a space-delimited string or a list of
       strings. Defaults to the decorated callable's `__name__`.
    :param title: The command title displayed in Text menu. Not in menu if None.
    :param hotkey: Preferred command hotkey tuple: `(<key char>, <key mask>)`.
        Ignored if title is None.
    :param is_enabled: A callable that returns a boolean value indicating if
        the command is enabled in the Text menu. Always enabled if None.
        Signature: `is_enabled(textview, sender)`.
    :param parse_args: A callable that takes a string and returns a tuple of
        arguments to be passed to the command as the `args` parameter.
        Use the default command parser, which simply splits the string,
        if `None`. Signature: `parse_args(command_text)`. May return
        `None` if arguments cannot be parsed or are not recognized.
    :param lookup_with_parse_args: If True, use the `parse_args` callable to
        lookup the command. The command's argument parser should return None
        if it receives a text string that cannot be executed.
    """
    if isinstance(names, basestring):
        names = names.split()
    def command_decorator(func):
        func.is_text_command = True
        func.names = names or [func.__name__]
        func.title = title
        func.hotkey = hotkey
        func.is_enabled = is_enabled or (lambda textview, sender: True)
        func.parse_args = parse_args or (lambda text: text.split())
        func.lookup_with_parse_args = lookup_with_parse_args
        return func
    if func is None:
        return command_decorator
    return command_decorator(func)


SEPARATOR = object()

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Built-in text commands

def load_commands():
    return dict(
        #document_menu_commands=[],

        # A list of text commands
        text_menu_commands=[
            show_command_bar,
            goto_line,
            comment_text,
            pad_comment_text,
            indent_lines,
            dedent_lines,
            wrap_at_margin,
            wrap_lines,
            sort_lines,
            reindent,
        ],

        # A dict of of NSResponder selectors mapped to callbacks
        #
        # Each callback should have the same signature as a text command.
        # The second and third arguments (sender, args) will always be None
        # when executed in this context.
        input_handlers={
            "insertTab:": indent_lines,
            "insertBacktab:": dedent_lines,
            "insertNewline:": insert_newline,
            "moveToBeginningOfLine:": move_to_beginning_of_line,
            "moveToLeftEndOfLine:": move_to_beginning_of_line,
            #"moveToBeginningOfLineAndModifySelection:":
            #    select_to_beginning_of_line,
            "deleteBackward:": delete_backward,
            #"deleteForward:": delete_forward,
        }
    )


@command(title=u"Command Bar", hotkey=(";", NSCommandKeyMask))
def show_command_bar(textview, sender, args):
    """Show the command bar"""
    from editxt import app
    editor = app.find_editor_with_document_view(textview.doc_view)
    if editor is None:
        NSBeep()
    else:
        editor.command.activate()


def parse_line_number(text):
    try:
        return int(text.strip())
    except (ValueError, TypeError):
        pass

@command(names='goto', title=u"Goto Line",
    parse_args=parse_line_number,
    lookup_with_parse_args=True)
def goto_line(textview, sender, args):
    """Jump to a line in the document"""
    if args is None:
        show_command_bar(textview, sender, None)
        return
    assert isinstance(args, (int, long)), 'invalid line number: %r' % (args,)
    textview.text_view.goto_line(args)


def has_selection(textview, sender):
    return textview.selectedRange().length > 0


@command(title=u"(Un)comment Selected Lines",
    hotkey=(",", NSCommandKeyMask),
    is_enabled=has_selection)
def comment_text(textview, sender, args):
    """Comment/uncomment the selected text region

    The region is uncommented if the first two lines start with comment
    characters. Otherwise, the region is commented.
    """
    _comment_text(textview, sender, args, False)

@command(title=u"(Un)comment + Space Selected Lines",
    hotkey=(",", NSCommandKeyMask | NSShiftKeyMask),
    is_enabled=has_selection)
def pad_comment_text(textview, sender, args):
    """Comment/uncomment + space the selected text region

    The region is uncommented if the first two lines start with comment
    characters. Otherwise, the region is commented. When commenting the
    region, each line is prefixed with an additional space if it does
    not begin with a space or tab character.
    """
    _comment_text(textview, sender, args, True)

def _comment_text(textview, sender, args, pad):
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
        pad,
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

def comment_line(text, token, indent_mode, indent_size, pad=False):
    if not pad:
        prefix = token
    elif indent_mode == const.INDENT_MODE_SPACE:
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

def uncomment_line(text, token, indent_mode, indent_size, pad=False):
    line = text
    nolead = text.lstrip()
    if nolead.startswith(token):
        lentoken = len(token)
        if nolead[lentoken] == u" " and pad:
            lentoken += 1
        line = nolead[lentoken:]
        lentoken = len(text) - len(nolead)
        if lentoken > 0:
            line = text[:lentoken] + line
        if indent_mode == const.INDENT_MODE_SPACE and pad:
            prespace = len(line) - len(line.lstrip(u" "))
            fillchars = indent_size - (prespace % indent_size)
            if fillchars != indent_size:
                line = u" " * fillchars + line
    return line


@command(title=u"Indent Selected Lines",
    hotkey=("]", NSCommandKeyMask),
    is_enabled=has_selection)
def indent_lines(textview, sender, args):
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


@command(title=u"Un-indent Selected Lines", hotkey=("[", NSCommandKeyMask))
def dedent_lines(textview, sender, args):
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


@command(names='sort', title=u"Sort Lines...")
def sort_lines(textview, sender, args):
    from editxt.sortlines import SortLinesController
    sorter = SortLinesController.create_with_textview(textview)
    if args is None:
        sorter.begin_sheet(sender)
    else:
        raise NotImplementedError


@command(title=u"Hard Wrap...",
    hotkey=("\\", NSCommandKeyMask | NSShiftKeyMask),
    is_enabled=has_selection)
def wrap_lines(textview, sender, args):
    from editxt.wraplines import WrapLinesController
    WrapLinesController.create_with_textview(textview).begin_sheet(sender)


@command(title=u"Hard Wrap At Margin",
    hotkey=("\\", NSCommandKeyMask),
    is_enabled=has_selection)
def wrap_at_margin(textview, sender, args):
    from editxt.commandbase import Options
    from editxt.wraplines import WrapLinesController, wrap_selected_lines
    opts = Options()
    ctl = WrapLinesController.shared_controller()
    opts.wrap_column = const.DEFAULT_RIGHT_MARGIN
    opts.indent = ctl.opts.indent
    wrap_selected_lines(textview, opts)


@command(title=u"Change Indentation")
def reindent(textview, sender, args):
    from editxt.changeindent import ChangeIndentationController
    ctl = ChangeIndentationController.create_with_textview(textview)
    ctl.begin_sheet(sender)


_ws = re.compile(ur"([\t ]+)", re.UNICODE | re.MULTILINE)

def insert_newline(textview, sender, args):
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

def move_to_beginning_of_line(textview, sender, args):
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

#def move_to_beginning_of_line_and_modify_selection(textview, sender, args):

def delete_backward(textview, sender, args):
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
            elif delete < sel[0] - i:
                delete = 1
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
        self.lookup_full_commands = []
        self.input_handlers = {}
        self.editems = editems = {}
#         ntc = menu.itemAtIndex_(1) # New Text Command menu item
#         ntc.setTarget_(self)
#         ntc.setAction_("newTextCommand:")
#         etc = menu.itemAtIndex_(2).submenu() # Edit Text Command menu
        #self.load_commands()

    def lookup(self, alias):
        return self.commands.get(alias)

    def lookup_full_command(self, command_text):
        for command in self.lookup_full_commands:
            try:
                args = command.parse_args(command_text)
            except Exception:
                log.warn('cannot parse command: %s', command_text, exc_info=True)
                continue
            if args is not None:
                return command, args
        return None, None

    @classmethod
    def iter_command_modules(self):
        """Iterate text commands, yield (<command file path>, <command instance>)"""
        # load local (built-in) commands
        yield None, load_commands()

    def load_commands(self):
        for path, reg in self.iter_command_modules():
            for command in reg.get("text_menu_commands", []):
                self.add_command(command, path)
            self.input_handlers.update(reg.get("input_handlers", {}))

    def add_command(self, command, path):
        if command.title is not None:
            command.__tag = tag = self.tagger.next()
            hotkey, keymask = self.validate_hotkey(command.hotkey)
            item = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
                command.title, "performTextCommand:", hotkey)
            item.setKeyEquivalentModifierMask_(keymask)
            item.setTag_(tag)
            # HACK tag will not be the correct index if an item is ever removed
            self.menu.insertItem_atIndex_(item, tag)
            self.commands[tag] = command
        if command.lookup_with_parse_args:
            self.lookup_full_commands.insert(0, command)
        if command.names:
            for alias in command.names:
                if not isinstance(alias, basestring) or ' ' in alias:
                    log.warn('invalid command alias (%r) for %s loaded from %s',
                        alias, command, path)
                else:
                    self.commands[alias] = command

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
                command(textview, sender, None)
            except Exception:
                log.error("%s.execute failed", type(command).__name__, exc_info=True)

    def do_textview_command_by_selector(self, textview, selector):
        #log.debug(selector)
        callback = self.input_handlers.get(selector)
        if callback is not None:
            try:
                callback(textview, None, None)
                return True
            except Exception:
                log.error("%s failed", callback, exc_info=True)
        return False
