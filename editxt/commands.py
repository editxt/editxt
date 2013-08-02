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
from editxt.commandparser import (Choice, Int, String, Regex, VarArgs,
    CommandParser, Options, SubArgs, SubParser)

log = logging.getLogger(__name__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Text command system interface

"""
The primary interface for loading text commands into EditXT is a module-level
function that returns a list of command functions provided by the module:

def load_commands():
    return [decorated_text_command, ...]
"""


def command(func=None, name=None, title=None, hotkey=None,
            is_enabled=None, arg_parser=None, lookup_with_arg_parser=False):
    """Text command decorator

    Text command signature: `text_command(textview, sender, args)`
    Both `sender` and `args` will be `None` in some contexts.

    :param name: A name that can be typed in the command bar to invoke the
        command. Defaults to the decorated callable's `__name__`.
    :param title: The command title displayed in Text menu. Not in menu if None.
    :param hotkey: Preferred command hotkey tuple: `(<key char>, <key mask>)`.
        Ignored if title is None.
    :param is_enabled: A callable that returns a boolean value indicating if
        the command is enabled in the Text menu. Always enabled if None.
        Signature: `is_enabled(textview, sender)`.
    :param arg_parser: An object inplementing the `CommandParser` interface.
        Defaults to `CommandParser(VarArgs("args"))`.
    :param lookup_with_arg_parser: If True, use the `arg_parser.parse` to
        lookup the command. The parser should return None if it receives
        a text string that cannot be parsed.
    """
    if isinstance(name, basestring):
        name = name.split()
    def command_decorator(func):
        func.is_text_command = True
        func.name = name[0] if name else func.__name__
        func.names = name or [func.__name__]
        func.title = title
        func.hotkey = hotkey
        func.is_enabled = is_enabled or (lambda textview, sender: True)
        func.arg_parser = arg_parser or CommandParser(VarArgs("args"))
        func.lookup_with_arg_parser = lookup_with_arg_parser
        return func
    if func is None:
        return command_decorator
    return command_decorator(func)

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


@command(arg_parser=CommandParser(
    Regex('pattern', replace=True, default=(re.compile(""), "")),
    Choice(('find-next next', 'find_next'),
        ('find-previous previous', 'find_previous'),
        ('replace-one one', 'replace_one'),
        ('replace-all all', 'replace_all'),
        ('replace-in-selection in-selection selection', 'replace_all_in_selection'),
        name='action'),
    Choice('regex literal-text word', name='search_type'),
    Choice(('wrap', True), ('no-wrap', False), name='wrap_around'),
), lookup_with_arg_parser=True)
def find(textview, sender, args):
    from editxt.findpanel import Finder, FindOptions
    assert args is not None, sender
    action = args.__dict__.pop('action')
    search_type = args.__dict__.pop('search_type')
    find, replace = args.__dict__.pop('pattern')
    opts = FindOptions(**args.__dict__)
    opts.find_text = find.pattern
    opts.replace_text = replace or ""
    opts.ignore_case = bool(find.flags & re.IGNORECASE)
    opts.match_entire_word = (search_type == 'word')
    opts.regular_expression = (search_type == "regex")
    finder = Finder(lambda:textview, opts)
    getattr(finder, action)(sender)


@command(name='sort', title=u"Sort Lines...",
    arg_parser=CommandParser(
        Choice(('selection', True), ('all', False)),
        Choice(('forward', False), ('reverse', True), name='reverse'),
        Choice(
            ('sort-leading-whitespace', False),
            ('ignore-leading-whitespace', True),
            name='ignore-leading-whitespace'),
        Regex('sort-regex', True),
    ))
def sort_lines(textview, sender, args):
    from editxt.sortlines import SortLinesController, sortlines
    if args is None:
        sorter = SortLinesController.create_with_textview(textview)
        sorter.begin_sheet(sender)
    else:
        sortlines(textview, args)


@command(name='wrap', title=u"Hard Wrap...",
    hotkey=("\\", NSCommandKeyMask | NSShiftKeyMask),
    is_enabled=has_selection,
    arg_parser=CommandParser( # TODO test
        Int('wrap_column'),
        Choice(('indent', True), ('no-indent', False)),
    ))
def wrap_lines(textview, sender, args):
    from editxt.wraplines import WrapLinesController, wrap_selected_lines
    if args is None:
        wrapper = WrapLinesController.create_with_textview(textview)
        wrapper.begin_sheet(sender)
    else:
        wrap_selected_lines(textview, args)


@command(title=u"Hard Wrap At Margin",
    hotkey=("\\", NSCommandKeyMask),
    is_enabled=has_selection)
def wrap_at_margin(textview, sender, args):
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


@command(title=u"Reload config")
def reload_config(textview, sender, args):
    from editxt import app
    app.config.reload()



def set_docview_variable(textview, name, args):
    setattr(textview.doc_view, name, args.value)

@command(name="set", arg_parser=CommandParser(SubParser("variable",
#    Variable("indent", [
#        Int("size", default=lambda textview: app.config["indent_size"])
#        Choice(
#            ("space", const.INDENT_MODE_SPACE),
#            ("tab", const.INDENT_MODE_TAB),
#            name="mode",
#            default=lambda textview: textview.doc_view.document.indent_mode)
#    ], lambda config:(config["indent.size"], config["indent.mode"])),
#    Variable("highlight_selected_text", [
#        Choice(
#            ("yes", True),
#            ("no", False),
#            name="value",
#            default=lambda textview:
#                           textview.doc_view.highlight_selected_text)
#    ], "highlight_selected_text.enabled"),
#    Variable("newline_mode", [
#        Choice(
#            ("space", const.INDENT_MODE_SPACE),
#            ("tab", const.INDENT_MODE_TAB),
#            name="value",
#            default=lambda textview: textview.doc_view.newline_mode)
#    ]),
    SubArgs("soft_wrap",
        Choice(
            ("on", const.WRAP_WORD),
            ("off", const.WRAP_NONE),
            name="value",
            ),#default=lambda textview: textview.doc_view.wrap_mode)
        setter=set_docview_variable
    ),
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


