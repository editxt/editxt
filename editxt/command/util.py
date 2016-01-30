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
from collections import Counter
from textwrap import dedent

import editxt.constants as const

log = logging.getLogger(__name__)


def has_selection(editor):
    return editor.text_view and editor.text_view.selectedRange().length > 0

def has_editor(editor):
    return editor is not None

def get_selection(editor=None):
    if editor is None or editor.document is None or \
            not editor.selection or editor.selection[1] == 0:
        return None
    return editor.document.text_storage[editor.selection]


#_line_splitter = re.compile("([^\n\r\u2028\u2029]*(?:%s)?)" % "|".join(
#    eol for eol in sorted(const.EOLS.values(), key=len, reverse=True)))

def iterlines(text, range=(0,)):
    """iterate over lines of text

    By default this function iterates over all lines in the given text.
    If the 'range' parameter (NSRange or tuple) is given, lines that
    intersect with that range will be yielded.
    """
    if not text:
        yield text
    else:
        if not hasattr(text, "iterlines"):
            from editxt.platform.text import Text
            text = Text(text)
        if len(range) == 2:
            range = (range[0], sum(range))
        yield from text.iterlines(*range)
        #if len(list(range)) == 2:
        #    range = (range[0], sum(range))
        #for line in _line_splitter.finditer(text, *range):
        #    if line.group():
        #        yield line.group()

# def expand_range(text, range):
#     """expand range to beginning of first selected line and end of last selected line"""
#     r = text.lineRangeForRange_(range)
#     if text[-2:] == u"\r\n":
#         r.length -= 2
#     elif text[-1] in u"\n\r\u2028":
#         r.length -= 1
#     return r


_newlines = re.compile("|".join(
    eol for eol in sorted(const.EOLS.values(), key=len, reverse=True)))

def normalize_newlines(text, eol):
    return _newlines.sub(eol, text)

def replace_newlines(textview, eol):
    sel = textview.selectedRange()
    text = textview.string()
    next = normalize_newlines(text, eol)
    if text == next:
        return
    range = (0, len(text))
    if textview.shouldChangeTextInRange_replacementString_(range, next):
        textview.textStorage().replaceCharactersInRange_withString_(range, next)
        textview.didChangeText()
        textview.setSelectedRange_(sel)


def markdoc(text, *args, header=True, **kw):
    """Render docstring as markdown

    :param header: When true (the default) make the first line a level-
    one heading (<h1>). Must be specified as keyword argument.
    """
    from editxt.platform.markdown import markdown
    if "\n" not in text:
        first = newline = ""
        rest = text
    else:
        first, newline, rest = text.partition("\n")
        if first.strip():
            if header:
                first = "# " + first
        else:
            first = "# " if header else ""
            newline = ""
    text = "".join([first, newline, dedent(rest)])
    return markdown(text, *args, **kw)


_indentation_regex = re.compile("([ \t]*)([^\r\n\u2028]*[\r\n\u2028]*)")

def change_indentation(textview, old_indent, new_indent, size):
    attr_change = (new_indent == "\t")
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
            next = "".join(fragments)
        range = (0, len(text))
        if textview.shouldChangeTextInRange_replacementString_(range, next):
            if attr_change:
                textview.editor.document.reset_text_attributes(size)
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


def calculate_indent_mode_and_size(text, sample_lines=256):
    """Calculate indent mode (tab or space) and size

    This uses a statistical calculation to determine the most likely
    indent size based on the first `N` lines in the given text where
    `N = sample_lines`. Lines containing only whitespace are ignored.

    :returns: A two-tuple: `(<indent_mode>, <indent_size>)`.
    `indent_mode` will be one of `editxt.constants.INDENT_MODE_SPACE`,
    `editxt.constants.INDENT_MODE_TAB` or `None`. `indent_size` will
    be the number of spaces per indent, or `None` if `indent_mode` is
    `editxt.constants.INDENT_MODE_TAB` or there are no lines indented
    more than one space.
    """
    last_size = None
    sizes = Counter()
    space = False
    mode = size = None
    for n, line in enumerate(iterlines(text)):
        if n >= sample_lines:
            break
        if not line.strip():
            continue
        if line.startswith(" "):
            space = True
            indent = len(line) - len(line.lstrip(" "))
            if indent != last_size:
                last_size = indent
                sizes[indent] += 1
        elif not space and line.startswith("\t"):
            return const.INDENT_MODE_TAB, None
    sizes.pop(1, None)
    bases = [] # list of minimum indent sizes
    for indent in sorted(sizes):
        if any(indent % b == 0 for b in bases):
            # stop when we find an indent width that is evenly
            # divisible by at least one base (minimum indent size)
            break
        bases.append(indent)
    if len(bases) == 1:
        size = bases[0]
    else:
        def rank(base):
            return sum(count
                for indent, count in sizes.items() if indent % base == 0)
        max_rank = 0
        for base in bases:
            if rank(base) > max_rank:
                max_rank = rank(base)
                size = base
    if space:
        mode = const.INDENT_MODE_SPACE
    return mode, size


def make_command_predicate(command):
    if len(command.names) == 1:
        prefix = command.name + " "
    else:
        prefix = tuple(n + " " for n in command.names)
    if command.lookup_with_arg_parser:
        def predicate(item, parser=command.arg_parser):
            return item.startswith(prefix) or parser.match(item.lstrip(" "))
    else:
        def predicate(item): return item.startswith(prefix)
    return predicate
