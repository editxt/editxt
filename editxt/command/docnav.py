# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2014 Daniel Miller <millerdev@gmail.com>
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
from collections import defaultdict

import editxt.constants as const
from editxt.command.base import command, CommandError
from editxt.command.parser import (CommandParser, Choice, CompleteWord,
    Conditional, Int, Regex, String, Error)
from editxt.command.util import has_editor
from editxt.editor import Editor
from editxt.platform.app import beep
from editxt.platform.constants import KEY
from editxt.project import Project

log = logging.getLogger(__name__)


class EditorTreeItem(String):

    NO_MATCH = const.Constant("no match")

    def __init__(self, *args, editor=None, **kw):
        super().__init__(*args, **kw)
        self.editor = editor
        self.completions = {} if editor is not None else None

    def with_context(self, editor):
        return type(self)(self.name, default=self.default, editor=editor)

    def iter_editors(self, arg):
        current_project = self.editor.project
        for editor in current_project.editors:
            yield editor
        for project in current_project.window.projects:
            yield project

    @staticmethod
    def full_name(editor):
        parts = [editor.name, editor.short_path(name=False)]
        return "::".join(p for p in parts if p)

    def cached_completions(self, arg):
        key = (arg.text, arg.start)
        try:
            items = self.completions[key]
        except KeyError:
            items = self.completions[key] = self.get_completions(arg)
        return items

    def value_of(self, consumed, arg):
        if self.completions is not None and consumed:
            starts = []
            for comp in self.cached_completions(arg):
                if comp.name == consumed:
                    return comp.editor
                if comp.name.startswith(consumed):
                    starts.append(comp.editor)
            if starts:
                return starts[0]
            full_name = self.full_name
            for editor in self.iter_editors(arg):
                if full_name(editor) == consumed:
                    return editor
        if consumed:
            return self.NO_MATCH
        return self.default

    def parse_completions(self, text, index, args):
        items, end = super().parse_completions(text, index, args)
        if self.completions is not None:
            self.completions[(text, index)] = items
        return items, end

    def get_completions(self, arg):
        if self.editor is None:
            return []
        try:
            token = self.consume(arg.text, arg.start)[0] or ""
        except Error:
            return []
        editors = []
        names = defaultdict(int)
        for editor in self.iter_editors(arg):
            editors.append(editor)
            names[editor.name] += 1
        words = []
        nameset = set()
        full_name = self.full_name
        for editor in editors:
            name = editor.name
            if names[name] > 1:
                name = full_name(editor)
            if name in nameset:
                continue # ignore duplicate
            nameset.add(name)
            if not name.startswith(token):
                continue
            escaped = name.replace(" ", "\\ ") if " " in name else name
            words.append(CompleteWord(escaped, editor=editor, name=name))
        return words

    def get_placeholder(self, arg):
        if not arg:
            return str(self)
        token = self.consume(arg.text, arg.start)[0] or ""
        comps = [word for word in self.cached_completions(arg)
                      if word.name.startswith(token)]
        if len(comps) == 1:
            return comps[0][len(token):]
        return ""

    def arg_string(self, value):
        if value is not None:
            value = self.full_name(value)
        return super().arg_string(value)


class ProjectItem(EditorTreeItem):

    def iter_editors(self, arg):
        if not has_project(arg):
            return
        for editor in arg.args.name.value.editors:
            yield editor


def no_editor(arg):
    # a bit hackish, but only true if first arg is skipped
    name = arg.args.name
    return name.value is None and not name.could_consume_more

def has_project(arg):
    return isinstance(arg.args.name.value, Project)


@command(arg_parser=CommandParser(
    EditorTreeItem("name"),
    Conditional(has_project, ProjectItem("file")),
    Conditional(no_editor, Choice(
        ("previous", const.PREVIOUS),
        ("next", const.NEXT),
        ("up", const.UP),
        ("down", const.DOWN),
        name="direction"
    )),
    Conditional(no_editor, Int("offset", default=1)),
), title="Navigate Document Tree", is_enabled=has_editor)
def doc(editor, sender, args):
    """Navigate the document tree"""
    if args is None:
        from editxt.commands import show_command_bar
        show_command_bar(editor, sender, doc.name + " ")
        return
    if args.name is not None:
        new_editor = args.file
        if new_editor is None:
            new_editor = args.name
        if new_editor is not EditorTreeItem.NO_MATCH and \
                editor.project.window.focus(new_editor):
            return
    elif editor.project.window.focus(args.direction, args.offset):
        return
    beep()
