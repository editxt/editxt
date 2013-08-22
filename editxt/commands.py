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
import re

from AppKit import *
from Foundation import *

import editxt.constants as const
from editxt.command.base import command
from editxt.command.parser import (Choice, Int, String, Regex, RegexPattern,
    VarArgs, CommandParser, Options, SubArgs, SubParser)
from editxt.command.util import has_selection, iterlines

from editxt.command.changeindent import reindent
from editxt.command.find import find
from editxt.command.sortlines import sort_lines
from editxt.command.wraplines import wrap_at_margin, wrap_lines

log = logging.getLogger(__name__)

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
            find,
            clear_highlighted_text,
            reload_config,
            set_variable,
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


@command(name='goto', title=u"Goto Line",
    arg_parser=CommandParser(Int("line")),
    lookup_with_arg_parser=True)
def goto_line(textview, sender, opts):
    """Jump to a line in the document"""
    if opts is None or opts.line is None:
        show_command_bar(textview, sender, None)
        return
    textview.goto_line(opts.line)


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


@command(title=u"Reload config")
def reload_config(textview, sender, args):
    from editxt import app
    app.config.reload()


@command(title="Clear highlighted text")
def clear_highlighted_text(textview, sender, args):
    textview.doc_view.finder.mark_occurrences("")


def set_docview_variable(textview, name, args):
    setattr(textview.doc_view.props, name, args.value)

def set_docview_indent_vars(textview, name, args):
    props = textview.doc_view.props
    setattr(props, "indent_size", args.size)
    setattr(props, "indent_mode", args.mode)

@command(name="set", arg_parser=CommandParser(SubParser("variable",
    SubArgs("highlight_selected_text",
        Choice(
            ("yes", True),
            ("no", False),
            name="value",
        ),
        setter=set_docview_variable),
    SubArgs("indent",
        Int("size", default=4), #lambda textview: app.config["indent_size"]),
        Choice(
            ("space", const.INDENT_MODE_SPACE),
            ("tab", const.INDENT_MODE_TAB),
            name="mode",
            #default=lambda textview: textview.doc_view.document.indent_mode)
        ),
        setter=set_docview_indent_vars),
    SubArgs("newline_mode",
        Choice(
            ("Unix unix LF lf \\n", const.NEWLINE_MODE_UNIX),
            ("Mac mac CR cr \\r", const.NEWLINE_MODE_MAC),
            ("Windows windows", const.NEWLINE_MODE_WINDOWS),
            ("Unicode unicode", const.NEWLINE_MODE_UNICODE),
            name="value",
            #default=lambda textview: textview.doc_view.newline_mode)
        ),
        setter=set_docview_variable,
    ),
    SubArgs("soft_wrap",
        Choice(
            ("yes on", const.WRAP_WORD),
            ("no off", const.WRAP_NONE),
            name="value",
            #default=lambda textview: textview.doc_view.wrap_mode
        ),
        setter=set_docview_variable),
)))
def set_variable(textview, sender, args):
    sub, opts = args.variable
    sub.data["setter"](textview, sub.name, opts)


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
