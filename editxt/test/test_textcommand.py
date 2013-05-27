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
import json
import logging
from os.path import join

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_, assert_raises
from AppKit import *
from Foundation import *
from editxt.test.util import TestConfig, tempdir

import editxt.constants as const
import editxt.textcommand as mod
from editxt.commandparser import ArgumentError, CommandParser, Int, Options
from editxt.commands import command
from editxt.textcommand import TextCommandController

log = logging.getLogger(__name__)


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CommandBar tests

def test_CommandBar_editor():
    editor = type('Editor', (object,), {})()
    text_commander = type('TextCommandController', (object,), {})()
    cmd = mod.CommandBar(editor, text_commander)
    eq_(cmd.editor, editor)
    eq_(cmd.text_commander, text_commander)
    # NOTE the following depends on CPython weakref behavior
    del editor, text_commander
    with assert_raises(AttributeError):
        cmd.editor
    with assert_raises(AttributeError):
        cmd.text_commander

def test_CommandBar_execute():
    from editxt.document import TextDocumentView
    from editxt.textcommand import TextCommandController
    def test(c):
        m = Mocker()
        editor = m.mock()
        beep = m.replace(mod, 'NSBeep')
        commander = m.mock(TextCommandController)
        bar = mod.CommandBar(editor, commander)
        args = c.text.split()
        if args and not c.current:
            editor.current_view >> None
            beep()
        elif args:
            view = editor.current_view >> m.mock(TextDocumentView)
            command = m.mock()
            if c.lookup == 'first':
                commander.lookup(args[0]) >> command
                if isinstance(c.args, Exception):
                    expect(command.arg_parser.parse(c.argstr)).throw(c.args)
                else:
                    command.arg_parser.parse(c.argstr) >> c.args
            elif c.lookup == 'full':
                commander.lookup(args[0]) >> None
                if c.args is None:
                    commander.lookup_full_command(c.text) >> (None, None)
                else:
                    commander.lookup_full_command(c.text) >> (command, c.args)
            else:
                assert c.lookup == None, c.lookup
            if c.args is None or isinstance(c.args, Exception):
                beep()
            else:
                view.text_view >> '<view>'
                res = expect(command('<view>', bar, '<args>'))
                if c.error:
                    res.throw(Exception('bang!'))
                    beep()
        with m:
            bar.execute(c.text)
    c = TestConfig(args='<args>', error=False, current=True)
    yield test, c(text='')
    yield test, c(text='cmd x y z', argstr='x y z', lookup='first')
    yield test, c(text='cmd  x y  z', argstr=' x y  z', lookup='first')
    yield test, c(text='cmd x ', argstr='x ', lookup='first', args=Exception())
    yield test, c(text='123 456', lookup='full')
    yield test, c(text='123 456', lookup='full', current=False)
    yield test, c(text='cmd', argstr='', lookup='first', args=None)
    yield test, c(text='123 456', lookup='full', args=None)
    yield test, c(text='123 456', lookup='full', error=True)

def test_get_placeholder():
    from editxt.commandparser import CommandParser, Bool, Regex, VarArgs
    from editxt.document import TextDocumentView
    from editxt.textcommand import TextCommandController
    def test(c):
        m = Mocker()
        editor = m.mock()
        beep = m.replace(mod, 'NSBeep')
        commander = m.mock(TextCommandController)
        bar = mod.CommandBar(editor, commander)
        args = c.text.split()
        if args:
            @command(arg_parser=CommandParser(
                Bool('selection sel s', 'all a', True),
                Bool('yes', 'no', False),
                Regex('sort_regex', True),
            ))
            def cmd(textview, sender, args):
                raise NotImplementedError("should not get here")
            commander.lookup(args[0]) >> (cmd if c.match == "simple" else None)
            if c.match == "parse":
                @command(arg_parser=CommandParser(
                    Regex('search_pattern'),
                    VarArgs("args", placeholder="..."),
                ))
                def search(textview, sender, args):
                    raise NotImplementedError("should not get here")
                commander.lookup_full_command(c.text) >> (search, "<args>")
            elif not c.match:
                commander.lookup_full_command(c.text) >> (None, None)
        with m:
            eq_(bar.get_placeholder(c.text), c.expect)
    c = TestConfig(match="simple")
    yield test, c(text='', expect="")
    yield test, c(text='cmd', expect=" selection no sort_regex")
    yield test, c(text='cmd ', expect="selection no sort_regex")
    yield test, c(text='cmd s', expect=" no sort_regex")
    yield test, c(text='cmd se', expect="")
    yield test, c(text='cmd sel', expect=" no sort_regex")
    yield test, c(text='cmd sel ', expect="no sort_regex")
    yield test, c(text='cmd sel /', expect="")
    yield test, c(text='cmd a', expect=" no sort_regex")
    yield test, c(text='cmd a ', expect="no sort_regex")
    yield test, c(text='cmd all', expect=" no sort_regex")
    yield test, c(text='cmd all ', expect="no sort_regex")
    yield test, c(text='cmd x', expect="")
    yield test, c(text='cmd x ', expect="")
    yield test, c(text='cmd   ', expect="sort_regex")
    yield test, c(text='cmd  /', expect="")
    yield test, c(text='cmd    ', expect="")
    yield test, c(text='/', expect="", match="parse")
    yield test, c(text='/x', expect="", match="parse")
    yield test, c(text='/x ', expect="", match="parse")
    yield test, c(text='/x/ ', expect="...", match="parse")
    yield test, c(text='/x/  ', expect="", match="parse")
    yield test, c(text='/x/ a', expect="", match="parse")
    yield test, c(text='cmd', expect="", match=None)

def test_get_completions():
    from editxt.commandparser import CommandParser, Bool, Regex, VarArgs
    from editxt.document import TextDocumentView
    from editxt.textcommand import TextCommandController
    def test(c):
        m = Mocker()
        editor = m.mock()
        beep = m.replace(mod, 'NSBeep')
        commander = m.mock(TextCommandController)
        bar = mod.CommandBar(editor, commander)
        args = c.text.split()
        @command(arg_parser=CommandParser(
            Bool('selection s', 'all a', True),
            Bool('reverse r', 'forward f', default=False),
            Regex('sort_regex', True),
        ))
        def cmd(textview, sender, args):
            raise NotImplementedError("should not get here")
        if len(args) < 2 and not c.text.endswith(" "):
            commander.commands >> {"cmd": cmd, "foo": cmd, 1: cmd}
        else:
            commander.lookup(args[0]) >> \
                (cmd if args[0] in ["cmd", "foo"] else None)
            if c.text.startswith("/"):
                @command(arg_parser=CommandParser(
                    Regex('search_pattern'),
                    Bool('yes y', 'no n', True),
                ))
                def search(textview, sender, args):
                    raise NotImplementedError("should not get here")
                commander.lookup_full_command(c.text) >> (search, "<args>")
            elif args[0] not in ["cmd", "foo"]:
                commander.lookup_full_command(c.text) >> (None, None)
        with m:
            eq_(bar.get_completions(c.text), c.expect)
    c = TestConfig()
    yield test, c(text='x', expect=([], -1))
    yield test, c(text='', expect=(["cmd", "foo"], 0))
    yield test, c(text='c', expect=(["cmd"], 0))
    yield test, c(text='cm', expect=(["cmd"], 0))
    yield test, c(text='cmd', expect=(["cmd"], 0))
    yield test, c(text='cmx', expect=([], -1))
    yield test, c(text='cmd ', expect=(["selection", "all"], 0))
    yield test, c(text='cmd s', expect=(["selection"], 0))
    yield test, c(text='cmd se', expect=(["selection"], 0))
    yield test, c(text='cmd selection', expect=(["selection"], 0))
    yield test, c(text='cmd sec', expect=([], -1))
    yield test, c(text='cmd s ', expect=(["forward", "reverse"], 0))
    yield test, c(text='cmd s r', expect=(["reverse"], 0))
    yield test, c(text='/', expect=([], -1))
    yield test, c(text='/a', expect=([], -1))
    yield test, c(text='/abc/ ', expect=(["yes", "no"], 0))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# TextControllerCommand tests

def test_TextCommandController_init():
    m = Mocker()
    menu = m.mock(NSMenu)
    with m:
        ctl = TextCommandController()
        eq_(ctl.commands, {})
        eq_(ctl.commands_by_path, {})
        eq_(ctl.input_handlers, {})
        eq_(ctl.editems, {})

def test_TextCommandController_lookup():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        ctl = TextCommandController()
        for command in c.commands:
            ctl.add_command(command, None, menu)
        eq_(ctl.lookup(c.lookup), c.result)
    @command(names="cmd cm")
    def cmd(*args):
        pass
    @command(names="cmd")
    def cm2(*args):
        pass
    @command
    def no(*args):
        pass
    c = TestConfig(commands=[], lookup='cmd', result=None)
    yield test, c
    yield test, c(commands=[no])
    yield test, c(commands=[cmd], result=cmd)
    yield test, c(commands=[cmd, cm2], result=cm2)
    yield test, c(commands=[cmd, cm2], lookup='cm', result=cmd)

def test_TextCommandController_lookup_full_command():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        ctl = TextCommandController()
        for command in c.commands:
            ctl.add_command(command, None, menu)
            menu.insertItem_atIndex_(ANY, ANY)
        eq_(ctl.lookup_full_command(c.lookup), c.result)
    @command(names="cm")
    def cmd(*args):
        pass
    @command(
        arg_parser=CommandParser(Int("value")),
        lookup_with_arg_parser=True)
    def num(*args):
        pass
    c = TestConfig(commands=[], lookup='cmd', result=(None, None))
    yield test, c
    yield test, c(commands=[cmd])
    yield test, c(commands=[num])
    yield test, c(commands=[num], lookup='123', result=(num, Options(value=123)))

def test_TextCommandController_load_commands():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        ctl = TextCommandController()
        handlers = ctl.input_handlers = m.mock(dict)
        add = m.method(ctl.add_command)
        mod = m.mock(dict)
        m.method(ctl.iter_command_modules)() >> [("<path>", mod)]
        cmds = []; mod.get("text_menu_commands", []) >> cmds
        for i in xrange(c.commands):
            cmd = "<command %s>" % i
            add(cmd, "<path>", menu)
            cmds.append(cmd)
        hnds = mod.get("input_handlers", {}) >> {}
        for i in xrange(c.handlers):
            hnds["handle%s" % i] = "<handle %s>" % i
        handlers.update(hnds)
        with m:
            ctl.load_commands(menu)
    c = TestConfig()
    yield test, c(commands=0, handlers=0)
    yield test, c(commands=2, handlers=2)

def test_TextCommandController_add_command():
    def test(c):
        m = Mocker()
        menu = m.mock(NSMenu)
        mi_class = m.replace(mod, 'NSMenuItem')
        ctl = TextCommandController()
        handlers = m.replace(ctl, 'input_handlers')
        validate = m.method(ctl.validate_hotkey)
        cmd = m.mock()
        cmd.names >> []
        cmd.lookup_with_arg_parser >> False
        tag = cmd._TextCommandController__tag = ctl.tagger.next() + 1
        validate(cmd.hotkey >> "<hotkey>") >> ("<hotkey>", "<keymask>")
        mi = mi_class.alloc() >> m.mock(NSMenuItem)
        (cmd.title << "<title>").count(2)
        mi.initWithTitle_action_keyEquivalent_(
            '<title>', "performTextCommand:" ,"<hotkey>") >> mi
        mi.setKeyEquivalentModifierMask_("<keymask>")
        mi.setTag_(tag)
        menu.insertItem_atIndex_(mi, tag)
        with m:
            ctl.add_command(cmd, None, menu)
            assert ctl.commands[tag] is cmd, (ctl.commands[tag], cmd)
    c = TestConfig()
    yield test, c
    #yield test, c

def test_TextCommandController_validate_hotkey():
    tc = TextCommandController()
    eq_(tc.validate_hotkey(None), (u"", 0))
    eq_(tc.validate_hotkey(("a", 1)), ("a", 1))
    assert_raises(AssertionError, tc.validate_hotkey, ("a", "b", "c"))

def test_TextCommandController_is_textview_command_enabled():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        mi = m.mock(NSMenuItem)
        tv = m.mock(NSTextView)
        tc = m.mock()
        tcc = TextCommandController()
        cmds = m.replace(tcc, 'commands')
        cmds.get(mi.tag() >> 42) >> (tc if c.has_command else None)
        if c.has_command:
            if c.error:
                expect(tc.is_enabled(tv, mi)).throw(Exception)
                lg.error("%s.is_enabled failed", ANY, exc_info=True)
            else:
                tc.is_enabled(tv, mi) >> c.enabled
        with m:
            result = tcc.is_textview_command_enabled(tv, mi)
            eq_(result, c.enabled)
    c = TestConfig(has_command=True, enabled=False)
    yield test, c(has_command=False)
    yield test, c(error=True)
    yield test, c(error=False)
    yield test, c(error=False, enabled=True)

def test_TextCommandController_do_textview_command():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        mi = m.mock(NSMenuItem)
        tv = m.mock(NSTextView)
        tc = m.mock()
        tcc = TextCommandController()
        cmds = m.replace(tcc, 'commands')
        cmds.get(mi.tag() >> 42) >> (tc if c.has_command else None)
        if c.has_command:
            tc(tv, mi, None)
            if c.error:
                m.throw(Exception)
                lg.error("%s.execute failed", ANY, exc_info=True)
        with m:
            tcc.do_textview_command(tv, mi)
    c = TestConfig(has_command=True)
    yield test, c(has_command=False)
    yield test, c(error=True)
    yield test, c(error=False)

def test_TextCommandController_do_textview_command_by_selector():
    def test(c):
        m = Mocker()
        lg = m.replace("editxt.textcommand.log")
        tv = m.mock(NSTextView)
        tcc = TextCommandController()
        sel = "<selector>"
        callback = m.mock()
        handlers = m.replace(tcc, 'input_handlers')
        cmd = handlers.get(sel) >> (callback if c.has_selector else None)
        if c.has_selector:
            callback(tv, None, None)
            if c.error:
                m.throw(Exception)
                lg.error("%s failed", callback, exc_info=True)
        with m:
            result = tcc.do_textview_command_by_selector(tv, sel)
            eq_(result, c.result)
    c = TestConfig(has_selector=True, result=False)
    yield test, c(has_selector=False)
    yield test, c(error=True)
    yield test, c(error=False, result=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# CommandHistory tests

def test_CommandHistory__iter__():
    def test(files, lookups):
        # :param files: List of items representing history files, each
        #               being a list of commands.
        # :param lookups: List of tuples (<history index>, <command text>), ...]
        index = []
        pattern = mod.CommandHistory.FILENAME_PATTERN
        with tempdir() as tmp:
            for i, value in enumerate(files):
                index.append(pattern.format(i))
                if value is not None:
                    with open(join(tmp, pattern.format(i)), "wb") as fh:
                        for command in reversed(value):
                            fh.write(json.dumps(command) + "\n")
            with open(join(tmp, mod.CommandHistory.INDEX_FILENAME), "wb") as fh:
                json.dump(index, fh)

            history = mod.CommandHistory(tmp, 3, 5)
            eq_(list(enumerate(history)), lookups)

    yield test, [], []
    yield test, [None, None, ["command {}".format(i) for i in range(3)]], [
        (0, "command 0"),
        (1, "command 1"),
        (2, "command 2"),
    ]
    yield test, [["command {}".format(i)] for i in range(3)], [
        (0, "command 0"),
        (1, "command 1"),
        (2, "command 2"),
    ]
    yield test, \
        [["command {}".format(i + p * 3)
            for i in xrange(3)] for p in xrange(5)], \
        [(i, "command {}".format(i)) for i in xrange(15)]

def test_CommandHistory_append():
    def test(appends, lookups):
        with tempdir() as tmp:
            history = mod.CommandHistory(tmp, 3, 5)
            for item in appends:
                history.append(item)

            history = mod.CommandHistory(tmp, 3, 5)
            eq_(list(enumerate(history)), lookups)

    yield test, [], []
    yield test, "a", [(0, "a")]
    yield test, "abac", [(0, "c"), (1, "a"), (2, "b")]
    yield test, "abcdefghiabca", [
        (0, "a"), (1, "c"), (2, "b"),
        (3, "i"), (4, "h"), (5, "g"),
        (6, "f"), (7, "e"), (8, "d"),
        (9, "c"), (10, "b"), (11, "a")
    ]
