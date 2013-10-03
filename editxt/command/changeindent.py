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

import editxt.constants as const
from editxt.command.base import command, objc_delegate, SheetController
#from editxt.command.parser import Choice, Regex, CommandParser, Options

log = logging.getLogger(__name__)


@command(title="Change Indentation")
def reindent(textview, sender, args):
    ctl = ChangeIndentationController(textview)
    ctl.begin_sheet(sender)


class ChangeIndentationController(SheetController):
    """Window controller for sort lines text command"""

    COMMAND = reindent
    NIB_NAME = "ChangeIndentation"

    def load_options(self):
        """load current indent mode from textview"""
        opts = self.options
        view = self.textview.doc_view
        opts.from_mode = opts.to_mode = view.indent_mode
        opts.from_size = opts.to_size = view.indent_size

    def save_options(self):
        """no-op override"""
#       opts = self.options
#       view = self.textview.doc_view
#       view.indent_mode = opts.to_mode
#       view.indent_size = opts.to_size

    @objc_delegate
    def execute_(self, sender):
        opts = self.options
        self.textview.doc_view.change_indentation(
            opts.from_mode,
            opts.from_size,
            opts.to_mode,
            opts.to_size,
            True,
        )
        self.save_options()
        self.cancel_(sender)

# def change_indentation(textview, opts):
#   raise NotImplementedError
#   text = textview.string()
#   regex = re.compile(opts.search_pattern) if opts.regex_sort else None
#   if opts.match_pattern:
#       groups = [int(g.strip()) for g in opts.match_pattern.split("\\") if g.strip()]
#   else:
#       groups = None
#   def key(line):
#       if opts.ignore_leading_ws:
#           line = line.lstrip()
#       if regex is not None:
#           match = regex.search(line)
#           if match is None:
#               line = (1,)
#           elif not match.groups():
#               line = (0, match.group(0))
#           else:
#               matched = match.groups("")
#               if groups:
#                   matched = dict(enumerate(matched))
#                   matched = tuple(matched.get(g - 1, "") for g in groups)
#               line = (0,) + matched
#       return line
#   if opts.sort_selection:
#       range = text.lineRangeForRange_(textview.selectedRange())
#   else:
#       range = (0, len(text))
#   output = "".join(sorted(iterlines(text, range), key=key, reverse=opts.reverse_sort))
#   if textview.shouldChangeTextInRange_replacementString_(range, output):
#       textview.textStorage().replaceCharactersInRange_withString_(range, output)
#       textview.didChangeText()
#       if opts.sort_selection:
#           textview.setSelectedRange_(range)
