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
import objc
import os
import re
import time

import AppKit as ak
import Foundation as fn

import editxt.constants as const
from editxt.command.base import command, objc_delegate, SheetController
from editxt.command.parser import Choice, Int, CommandParser, Options
from editxt.command.util import has_selection, iterlines

log = logging.getLogger(__name__)

WHITESPACE = re.compile(r"[ \t]*")


@command(name='wrap', title="Hard Wrap...",
    hotkey=("\\", ak.NSCommandKeyMask | ak.NSShiftKeyMask),
    is_enabled=has_selection,
    arg_parser=CommandParser( # TODO test
        Int('wrap_column', default=const.DEFAULT_RIGHT_MARGIN),
        Choice(('indent', True), ('no-indent', False)),
    ))
def wrap_lines(textview, sender, args):
    if args is None:
        wrapper = WrapLinesController(textview)
        wrapper.begin_sheet(sender)
    else:
        wrap_selected_lines(textview, args)


@command(title="Hard Wrap At Margin",
    hotkey=("\\", ak.NSCommandKeyMask),
    arg_parser=CommandParser( # TODO test
        Choice(('indent', True), ('no-indent', False)), # TODO default to last used value
    ),
    is_enabled=has_selection)
def wrap_at_margin(textview, sender, args):
    opts = Options()
    opts.wrap_column = const.DEFAULT_RIGHT_MARGIN
    opts.indent = args.indent if args is not None else True
    wrap_selected_lines(textview, opts)


class WrapLinesController(SheetController):
    """Window controller for sort lines text command"""

    COMMAND = wrap_lines
    NIB_NAME = "WrapLines"
    OPTIONS_FACTORY = lambda self:Options(
        wrap_column=const.DEFAULT_RIGHT_MARGIN,
        indent=True,
    )

    @objc_delegate
    def wrap_(self, sender):
        wrap_selected_lines(self.textview, self.options)
        self.save_options()
        self.cancel_(sender)

def wrap_selected_lines(textview, options):
    text = textview.string()
    sel = text.lineRangeForRange_(textview.selectedRange())
    eol = textview.editor.document.eol
    lines = iterlines(text, sel)
    output = eol.join(wraplines(lines, options, textview))
    if textview.shouldChangeTextInRange_replacementString_(sel, output):
        textview.textStorage().replaceCharactersInRange_withString_(sel, output)
        textview.didChangeText()
        textview.setSelectedRange_((sel[0], len(output)))

def wraplines(lines, options, textview):
    width = options.wrap_column
    regexp = WHITESPACE
    if options.indent:
        token = re.escape(textview.editor.document.comment_token)
        if token:
            regexp = re.compile(r"^[ \t]*(?:%s *)?" % token)
    for frag in lines:
        frag = frag.rstrip()
        if frag:
            break
        yield ""
    else:
        yield ""
        raise StopIteration
    leading = ""
    indent = regexp.match(frag).group()
    comment = regexp is not WHITESPACE and bool(indent.strip())
    frag = regexp.sub("", frag, 1)
    if indent:
        firstlen = width - len(indent)
        if firstlen < 1:
            firstlen = 1
        line, frag = get_line(frag, lines, firstlen, regexp)
        yield indent + line
        if options.indent:
            width = firstlen
            leading = indent
    while True:
        while frag is not None:
            line, frag = get_line(frag, lines, width, regexp)
            yield leading + line if line else line
        for frag in lines:
            frag = regexp.sub("", frag.rstrip(), 1)
            yield leading if comment else ""
            if frag:
                break
        else:
            if line:
                yield ""
            break

def get_line(frag, lines, width, regexp, ws=" \t"):
    while True:
        while len(frag) < width:
            try:
                line = regexp.sub("", next(lines).rstrip(), 1)
            except StopIteration:
                return frag, None
            if not line:
                return frag, None
            frag = frag + " " + line if frag else line
        if len(frag) == width:
            return frag, ""
        for i in range(width, 0, -1):
            if frag[i] in ws:
                break
        else:
            fraglen = len(frag)
            i = width + 1
            while i < fraglen and frag[i] not in ws:
                i += 1
        line, frag = frag[:i].rstrip(), frag[i:].lstrip()
        if len(line) + len(WHITESPACE.split(frag, 1)[0]) < width:
            frag = line + " " + frag
            continue
        return line, frag
