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
import re

import AppKit as ak
import Foundation as fn

import editxt.constants as const
from editxt.command.base import command, CommandError
from editxt.command.parser import (Choice, DynamicList, File, Float, FontFace,
    Int, String, Regex, RegexPattern, VarArgs, CommandParser, Options, SubArgs,
    SubParser)
from editxt.command.util import has_editor, has_selection, iterlines
from editxt.platform.app import beep
from editxt.platform.events import call_later
from editxt.platform.font import DEFAULT_FONT, get_font
from editxt.util import user_path

from editxt.command.ag import ag
from editxt.command.blame import blame
from editxt.command.changeindent import reindent
from editxt.command.diff import diff
from editxt.command.docnav import doc as docnav
from editxt.command.find import find
from editxt.command.githuburl import github_url
from editxt.command.grab import grab
from editxt.command.openfile import open_
from editxt.command.pathfind import pathfind
from editxt.command.python import python
from editxt.command.sortlines import sort_lines
from editxt.command.unique import unique_lines
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
            unique_lines,
            reindent,
            find,
            ag,
            blame,
            diff,
            github_url,
            grab,
            open_,
            pathfind,
            python,
            clear_highlighted_text,
            docnav,
            reload_config,
            set_variable,
            help,
            debug,
        ],

        # A dict of of NSResponder selectors mapped to callbacks
        #
        # Each callback should have the same signature as a text command.
        # The second argument (args) will always be None when executed
        # in this context.
        input_handlers={
            "insertTab:": indent_lines,
            "insertBacktab:": dedent_lines,
            "insertNewline:": insert_newline,
            "moveToBeginningOfLine:": move_to_beginning_of_line,
            "moveToLeftEndOfLine:": move_to_beginning_of_line,
            "moveToBeginningOfLineAndModifySelection:": select_to_beginning_of_line,
            "moveToLeftEndOfLineAndModifySelection:": select_to_beginning_of_line,
            #"moveToEndOfLine:": move_to_end_of_line,
            #"moveToRightEndOfLine:": move_to_end_of_line,
            #"moveToEndOfLineAndModifySelection:": select_to_end_of_line,
            #"moveToRightEndOfLineAndModifySelection:": select_to_end_of_line,
            "deleteBackward:": delete_backward,
            #"deleteForward:": delete_forward,
        }
    )


@command(title="Command Bar", hotkey=(";", ak.NSCommandKeyMask),
         is_enabled=has_editor)
def show_command_bar(editor, args):
    """Show the command bar"""
    window = editor.project.window
    if window is None:
        beep()
    else:
        window.command.activate(text=args or "")


@command(name='goto', title="Goto Line",
    arg_parser=CommandParser(Int("line")),
    lookup_with_arg_parser=True)
def goto_line(editor, opts):
    """Jump to a line in the document"""
    if opts is None or opts.line is None:
        show_command_bar(editor, None)
        return
    editor.goto_line(opts.line)


@command(title="(Un)comment Selected Lines",
    hotkey=(",", ak.NSCommandKeyMask),
    is_enabled=has_selection)
def comment_text(editor, args):
    """Comment/uncomment the selected text region

    The region is uncommented if the first two lines start with comment
    characters. Otherwise, the region is commented.
    """
    _comment_text(editor, args, False)

@command(title="(Un)comment + Space Selected Lines",
    hotkey=(",", ak.NSCommandKeyMask | ak.NSShiftKeyMask),
    is_enabled=has_selection)
def pad_comment_text(editor, args):
    """Comment/uncomment + space the selected text region

    The region is uncommented if the first two lines start with comment
    characters. Otherwise, the region is commented. When commenting the
    region, each line is prefixed with an additional space if it does
    not begin with a space or tab character.
    """
    _comment_text(editor, args, True)

def _comment_text(editor, args, pad):
    textview = editor.text_view
    text = textview.string()
    sel = text.lineRangeForRange_(textview.selectedRange())
    comment_token = editor.document.comment_token
    if not comment_token:
        return
    if is_comment_range(text, sel, comment_token):
        func = uncomment_line
    else:
        func = comment_line
    args = (
        comment_token,
        editor.document.indent_mode,
        editor.document.indent_size,
        pad,
    )
    seltext = "".join(func(line, *args) for line in iterlines(text, sel))
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
        prespace = len(text) - len(text.lstrip(" "))
        if lentoken + 1 < indent_size and prespace:
            return token + text[lentoken:]
        elif lentoken < indent_size and prespace:
            prefix = token
        else:
            prefix = token + " "
    else:
        prefix = token + " "
    return prefix + text

def uncomment_line(text, token, indent_mode, indent_size, pad=False):
    line = text
    nolead = text.lstrip()
    if nolead.startswith(token):
        lentoken = len(token)
        if nolead[lentoken] == " " and pad:
            lentoken += 1
        line = nolead[lentoken:]
        lentoken = len(text) - len(nolead)
        if lentoken > 0:
            line = text[:lentoken] + line
        if indent_mode == const.INDENT_MODE_SPACE and pad:
            prespace = len(line) - len(line.lstrip(" "))
            fillchars = indent_size - (prespace % indent_size)
            if fillchars != indent_size:
                line = " " * fillchars + line
    return line


@command(title="Indent Selected Lines",
    hotkey=("]", ak.NSCommandKeyMask),
    is_enabled=has_selection)
def indent_lines(editor, args):
    indent_mode = editor.document.indent_mode
    if indent_mode == const.INDENT_MODE_TAB:
        istr = "\t"
    else:
        istr = " " * editor.document.indent_size
    textview = editor.text_view
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
            return line.lstrip(" \t")
        sel = text.lineRangeForRange_(sel)
        seltext = "".join(indent(line) for line in iterlines(text, sel))
        select = True
    if textview.shouldChangeTextInRange_replacementString_(sel, seltext):
        textview.textStorage().replaceCharactersInRange_withString_(sel, seltext)
        textview.didChangeText()
        if select:
            editor.selection = (sel[0], len(seltext))
        else:
            textview.scrollRangeToVisible_(editor.selection)


@command(title="Un-indent Selected Lines", hotkey=("[", ak.NSCommandKeyMask))
def dedent_lines(editor, args):
    def dedent(line, spt=editor.document.indent_size):
        if not line.strip():
            return line.lstrip(" \t")
        if line.startswith("\t"):
            return line[1:]
        remove = 0
        linelen = len(line)
        for i in range(spt):
            if i < linelen and line[i] == " ":
                remove += 1
            else:
                break
        return line[remove:]
    textview = editor.text_view
    text = textview.string()
    sel = text.lineRangeForRange_(textview.selectedRange())
    seltext = "".join(dedent(line) for line in iterlines(text, sel))
    if len(seltext) != sel.length:
        if textview.shouldChangeTextInRange_replacementString_(sel, seltext):
            textview.textStorage().replaceCharactersInRange_withString_(sel, seltext)
            textview.setSelectedRange_((sel[0], len(seltext)))
            textview.didChangeText()


@command(title="Reload config", is_enabled=has_editor)
def reload_config(editor, args):
    editor.app.reload_config()


@command(title="Clear highlighted text")
def clear_highlighted_text(editor, args):
    editor.finder.mark_occurrences("")


def set_editor_variable(editor, name, args):
    setattr(editor.proxy, name, args.value)

def set_editor_font(editor, name, args):
    font = get_font(args.face, args.size, args.smooth)
    setattr(editor.proxy, name, font)

def _default_font_attribute(name):
    def default(editor=None):
        font = DEFAULT_FONT if editor is None else editor.font
        return getattr(font, name)
    return default

def _default_highlight_selected_text(editor=None):
    return True if editor is None else not editor.highlight_selected_text

def set_project_variable(editor, command_name, args):
    assert len(args) == 1, repr(args)
    for name, value in args:
        setattr(editor.project.proxy, name, value)

def _default_project_path(editor=None):
    if editor is None or editor.project is None or editor.project.path is None:
        return None
    return user_path(editor.project.path)

def set_document_variable(editor, command_name, args):
    assert len(args) == 1, repr(args)
    for name, value in args:
        setattr(editor.document, name, value)

def _default_comment_token(editor=None):
    if editor is None:
        return None
    return editor.document.syntaxdef.comment_token

def set_editor_syntaxdef(editor, command_name, args):
    set_editor_variable(editor, "syntaxdef", args)

def _get_languages(editor):
    return [] if editor is None else editor.app.syntax_factory.definitions

def _default_language(editor=None):
    if editor is None or editor.project is None:
        return None
    return editor.document.syntaxdef.name

def set_editor_indent_vars(editor, name, args):
    proxy = editor.proxy
    setattr(proxy, "indent_size", args.size)
    setattr(proxy, "indent_mode", args.mode)

@command(name="set", arg_parser=CommandParser(SubParser("variable",
    SubArgs("comment_token",
        String("comment_token", default=_default_comment_token),
        setter=set_document_variable),
    SubArgs("font",
        FontFace("face", default=_default_font_attribute("face")),
        Float("size", default=_default_font_attribute("size")),
        Choice(
            ("smooth", True),
            ("jagged", False),
            name="smooth",
            default=_default_font_attribute("smooth"),
        ),
        setter=set_editor_font),
    SubArgs("highlight_selected_text",
        Choice(
            ("yes", True),
            ("no", False),
            name="value",
            default=_default_highlight_selected_text,
        ),
        setter=set_editor_variable),
    SubArgs("indent",
        Int("size", default=lambda editor=None: 4 if editor is None else editor.indent_size),
        Choice(
            ("space", const.INDENT_MODE_SPACE),
            ("tab", const.INDENT_MODE_TAB),
            name="mode",
            default=(lambda editor=None:
                        const.INDENT_MODE_SPACE if editor is None
                        else editor.indent_mode)
        ),
        setter=set_editor_indent_vars),
    SubArgs("language",
        DynamicList("value", _get_languages, "name", default=_default_language),
        setter=set_editor_syntaxdef),
    SubArgs("newline_mode",
        Choice(
            ("Unix unix LF lf \\n", const.NEWLINE_MODE_UNIX),
            ("Mac mac CR cr \\r", const.NEWLINE_MODE_MAC),
            ("Windows windows", const.NEWLINE_MODE_WINDOWS),
            ("Unicode unicode", const.NEWLINE_MODE_UNICODE),
            name="value",
            #default=lambda editor=None: const.NEWLINE_MODE_UNIX if editor is None
            #                            else editor.newline_mode)
        ),
        setter=set_editor_variable,
    ),
    SubArgs("project_path",
        File("path", directory=True, default=_default_project_path),
        setter=set_project_variable,
        is_enabled=has_editor),
    SubArgs("soft_wrap",
        Choice(
            ("yes on", const.WRAP_WORD),
            ("no off", const.WRAP_NONE),
            name="value",
            default=(lambda editor=None: const.WRAP_WORD
                if editor is None or editor.soft_wrap == const.WRAP_NONE
                else const.WRAP_NONE)
        ),
        setter=set_editor_variable),
    SubArgs("updates_path_on_file_move",
        Choice(
            ("yes", True),
            ("no", False),
            name="value",
            default=lambda editor=None:
                True if editor is None else editor.updates_path_on_file_move,
        ),
        setter=set_editor_variable),
)), is_enabled=has_editor)
def set_variable(editor, args):
    if args.variable is None:
        raise CommandError("nothing set")
    else:
        sub, opts = args.variable
        sub.data["setter"](editor, sub.name, opts)


@command(arg_parser=CommandParser(
    String("command", default="") # TODO auto-complete commands?
), is_enabled=has_editor)
def help(editor, opts):
    """Command Help

    Commands modify text, open new documents, change application state,
    etc. Commands are invoked from the Command menu, from the command
    bar, or with hotkeys.

    ## Discover and learn about commands

    - Auto-complete - press the Tab key to show the auto-complete menu.
    - Argument tips - command argument tips are displayed in a lighter
      color following the command and arguments that have already been
      typed in the command bar.
    - Command help - use command help to get more detailed instructions
      for invoking a command. Command help can be accessed through the
      Help menu or by pressing the F1 key.
    """
    editor.project.window.command.show_help(opts.command if opts else "")



def _default_cprofile_delay(editor=None):
    if 'cprofile' in globals() and cprofile.stop_profile is not None:
        return 'stop'
    return '5'


@command(name='debug', arg_parser=CommandParser(SubParser("action",
    SubArgs("cprofile",
        String("delay", default=_default_cprofile_delay),
        Int("run_seconds", default=5),
        File("path", directory=True, default=_default_project_path),
    ),
    SubArgs("mem-profile"),
    SubArgs("error"),
    SubArgs("unhandled-error"),
    SubArgs("exec", VarArgs("command", String("command", default=""))),
)), is_enabled=has_editor)
def debug(editor, opts):
    """Debugging commands

    - cprofile: profile python code with cProfile. Arguments are:
      - delay: number of seconds to delay start of profile or "stop"
        to stop in-progress profile.
      - run_seconds: number of seconds to run profile (run
        indefinitely until stopped if 0).
      - path: directory in which to write profile output.
    - mem-profile: write memory profile in EditXT Log.
    - error: raise an error immediately.
    - error: raise an unhandled error immediately.
    - exec: execute a python expression. `app` and `editor` are locals
      that can be referenced by the expression.
    """
    if opts.action is None:
        raise CommandError("please specify a sub command")
    sub, args = opts.action
    if sub.name == "cprofile":
        cprofile(editor, args.delay, args.run_seconds, args.path)
    if sub.name == "mem-profile":
        editor.document.app.open_error_log()
        mem_profile()
    elif sub.name == "error":
        raise Exception("raised by debug command")
    elif sub.name == "unhandled-error":
        class DebugError(BaseException): pass
        raise DebugError("raised by debug command")
    elif sub.name == "exec":
        command = " ".join(args.command)
        return str(eval(command, {"app": editor.app, "editor": editor}))


def cprofile(editor, delay, run_seconds, path):
    """Start cProfile after delay for run_seconds

    :param delay: Number of seconds to delay before starting profile.
    Once this delay is expired, the profile will start and its output
    file will be created in the given directory (`path`). Stop running
    profile if this value is `"stop"` or there is a profile in progress.
    :param run_seconds: Number of seconds to run profile. Run until next
    cprofile command if zero.
    :param path: A directory path in which to write profile output.
    """
    import os
    from cProfile import Profile
    from datetime import datetime
    from pstats import Stats
    from os.path import expanduser, join
    if delay == "stop" or cprofile.stop_profile is not None:
        if cprofile.stop_profile is not None:
            cprofile.stop_profile()
        return
    try:
        delay = int(delay)
    except ValueError:
        editor.message("bad delay: {!r}".format(delay), msg_type=const.ERROR)
        return
    profile = Profile()
    filename = None
    def start_profile():
        if profile is None:
            return
        nonlocal filename
        filename = join(
            expanduser(path),
            "profile-{:%Y%m%dT%H%M%S}.txt".format(datetime.now()),
        )
        with open(filename, "w", encoding="utf8") as fh:
            fh.write("in progress...")
        log.info("starting profile %s", filename)
        profile.enable()
    def stop_profile():
        cprofile.stop_profile = None
        nonlocal profile
        if filename is None:
            # cancel before start
            profile = None
            return
        profile.disable()
        log.info("stopped profile %s", filename)
        with open(filename, "w", encoding="utf8") as fh:
            try:
                stats = Stats(profile, stream=fh)
            except Exception as err:
                fh.write("{}: {}".format(type(err).__name__, err))
            else:
                stats.sort_stats("ncalls")
                stats.print_stats()
                stats.sort_stats("cumtime")
                stats.print_stats()
                stats.sort_stats("tottime")
                stats.print_stats()
    call_later(delay, start_profile)
    cprofile.stop_profile = stop_profile
    if run_seconds > 0:
        def auto_stop():
            if cprofile.stop_profile is not None:
                cprofile.stop_profile()
        call_later(delay + run_seconds, auto_stop)

cprofile.stop_profile = None


def mem_profile():
    import gc
    from collections import defaultdict
    from datetime import datetime
    def rep(obj, count):
        return '%-30s %10s    %s' % (obj.__name__, count, obj)
    objs = defaultdict(lambda:0)
    for obj in gc.get_objects():
        objs[type(obj)] += 1
    ones = sum(1 for o in objs.items() if o[1] == 1)
    objs = (o for o in objs.items() if o[1] > 1)
    objs = sorted(objs, key=lambda v:(-v[1], v[0].__name__))
    names = (rep(*o) for o in objs)
    log.info('%s gc objects:\n%s\nsingletons                     %10s',
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '\n'.join(names), ones)


_ws = re.compile(r"([\t ]+)", re.UNICODE | re.MULTILINE)

def insert_newline(editor, args):
    textview = editor.text_view
    eol = rep = editor.document.eol
    sel = editor.selection
    text = editor.document.text_storage
    if sel[0] > 0:
        string = text.string()
        prev_eol = text.rfind(eol, 0, sel[0])
        line_start = 0 if prev_eol < 0 else (prev_eol + len(eol))
        if line_start != sel[0]:
            indent = _ws.match(string, line_start, sel[0])
            if indent:
                rep += indent.group()
            wslead = _ws.match(string, sel[0])
            if wslead and not sel[1]:
                sel[1] += len(wslead.group())
    if textview.shouldChangeTextInRange_replacementString_(sel, rep):
        text[sel] = rep
        textview.didChangeText()
        textview.scrollRangeToVisible_(editor.selection)

def find_beginning_of_line(editor, selection=None):
    eol = editor.document.eol
    sel = selection or editor.selection
    text = editor.document.text_storage
    if sel[0] > 0:
        i = text.rfind(eol, 0, sel[0])
        i = 0 if i < 0 else (i + len(eol))
    else:
        i = 0
    wslead, end = i, len(text)
    while wslead < end and text[wslead] in ' \t':
        wslead += 1
    return wslead if wslead != i and wslead != sel[0] else i

def move_to_beginning_of_line(editor, args):
    new = (find_beginning_of_line(editor), 0)
    editor.selection = new
    editor.text_view.scrollRangeToVisible_(new)

def select_to_beginning_of_line(editor, args):
    sel = editor.selection
    start = sel[0]
    end = sum(sel)
    i = find_beginning_of_line(editor)
    if i > start:
        j = find_beginning_of_line(editor, (i, 0))
        assert j <= start, (sel, i, j)
        if j < start:
            new = (j, end - j)
        elif i <= end:
            # all whitespace at beginning of line is selected
            new = (i, end - i)
        else:
            new = (j, max(i, end) - j)
    else:
        new = (i, end - i)
    editor.selection = new
    editor.text_view.scrollRangeToVisible_(new)

# Not using this because NSTextView provides no easy way to set
# the selection anchor after setting selection with setSelectedRange...
# Shift+Left Arrow after Shift+End modified left end of selection.
#def find_end_of_line(editor, selection=None):
#    eol = editor.document.eol
#    sel = selection or editor.selection
#    text = editor.document.text_storage
#    i = sel[0]
#    end = len(text)
#    if eol == "\r\n" and i and i < end and text[i] == '\n' and text[i-1] == '\r':
#        # special case move to start of CRLF if in middle
#        i -= 1
#    else:
#        eols = const.NEWLINE_CHARS
#        while i < end and text[i] not in eols:
#            i += 1
#    return i
#
#def move_to_end_of_line(editor, args):
#    new = (find_end_of_line(editor), 0)
#    editor.selection = new
#    editor.text_view.scrollRangeToVisible_(new)
#
#def select_to_end_of_line(editor, args):
#    sel = editor.selection
#    end_sel = sum(sel)
#    end = find_end_of_line(editor, (end_sel, 0))
#    if end < end_sel:
#        # selection ended in the middle of CRLF; move to beginning of CRLF
#        if sel[0] > end:
#            new = (end, 0)
#        else:
#            new = (sel[0], end - sel[0])
#    else:
#        new = (sel[0], end - sel[0])
#    editor.selection = new
#    editor.text_view.scrollRangeToVisible_(new)

def delete_backward(editor, args):
    textview = editor.text_view
    if editor.document.indent_mode == const.INDENT_MODE_TAB:
        textview.deleteBackward_(None)
        return
    sel = textview.selectedRange()
    if sel.length == 0:
        if sel.location == 0:
            return
        text = textview.string()
        i = sel[0]
        while i > 0 and text[i - 1] == " ":
            i -= 1
        delete = sel[0] - i
        if delete < 1:
            delete = 1
        elif delete > 1:
            i = text.lineRangeForRange_((i, 0))[0]
            size = editor.document.indent_size
            maxdel = (sel[0] - i) % size
            if maxdel == 0:
                maxdel = size
            if delete > maxdel:
                delete = maxdel
            elif delete < sel[0] - i:
                delete = 1
        sel = (sel[0] - delete, delete)
    if textview.shouldChangeTextInRange_replacementString_(sel, ""):
        textview.textStorage().replaceCharactersInRange_withString_(sel, "")
        textview.didChangeText()
        textview.scrollRangeToVisible_(editor.selection)
