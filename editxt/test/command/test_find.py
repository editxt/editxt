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
import os
import re
from contextlib import closing
from tempfile import gettempdir

import AppKit as ak
import Foundation as fn
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import (assert_raises, TestConfig, untested,
    check_app_state, replattr, test_app)

import editxt.constants as const
import editxt.command.find as mod
from editxt.command.find import (Finder, FindController, FindOptions,
    make_found_range_factory)
from editxt.command.find import FORWARD, BACKWARD
from editxt.command.parser import RegexPattern
from editxt.editor import Editor
from editxt.platform.text import Text
from editxt.platform.views import TextView
from editxt.window import Window

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement Editor.pasteboard_data()
# """)

def make_options(config):
    return FindOptions(**{opt: config[key] for key, opt in {
        "find": "find_text",
        "replace": "replace_text",
        "action": "action",
        "search": "search_type",
        "ignore_case": "ignore_case",
        "wrap": "wrap_around",
    }.items() if key in config})

def test_find_command():
    def test(c):
        m = Mocker()
        app = m.mock('editxt.application.Application')
        options = make_options(c)
        options.app = app
        editor = m.mock(Editor)
        editor.app >> app
        finder_cls = m.replace("editxt.command.find.Finder")
        save_paste = m.replace(mod, "save_to_find_pasteboard")
        def check_options(get_editor, args, app):
            eq_(get_editor(), editor)
            eq_(args, options)
        finder = m.mock(Finder)
        save_paste(c.find)
        (finder_cls(ANY, ANY, app) << finder).call(check_options)
        getattr(finder, c.action)(None) >> c.message
        with m:
            args = mod.find.arg_parser.parse(c.input)
            result = mod.find(editor, args)
            eq_(result, c.message)

    c = TestConfig(find="", replace="", search=mod.REGEX, ignore_case=False,
                   wrap=True, action="find_next", message=None)
    yield test, c(input="")
    yield test, c(input="/abc", find="abc")
    yield test, c(input=":abc", find="abc")
    yield test, c(input=":abc\:", find=r"abc\:")
    yield test, c(input="/\/abc\//", find=r"\/abc\/")
    yield test, c(input="/abc/def", find="abc", replace="def")
    yield test, c(input="/abc/def/", find="abc", replace="def")
    yield test, c(input="/abc/def/i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=":abc:def:i", find="abc", replace="def", ignore_case=True)
    yield test, c(input="'abc'def'i", find="abc", replace="def", ignore_case=True)
    yield test, c(input='"abc"def"i', find="abc", replace="def", ignore_case=True)
    yield test, c(input=":ab\:c:def:i", find=r"ab\:c", replace="def", ignore_case=True)
    yield test, c(input="/abc// n", find="abc", action="find_next")
    yield test, c(input="/abc// p", find="abc", action="find_previous")
    yield test, c(input="/abc// previous", find="abc", action="find_previous")
    yield test, c(input="/abc// o", find="abc", action="replace_one")
    yield test, c(input="/abc// a", find="abc", action="replace_all")
    yield test, c(input="/abc// s", find="abc", action="replace_all_in_selection")
    yield test, c(input="/abc// c", find="abc", action="count_occurrences",
                  message="Found 3 occurrences")
    yield test, c(input="/abc//  regex", find="abc", search=mod.REGEX)
    yield test, c(input="/abc//  literal", find="abc", search=mod.LITERAL)
    yield test, c(input="/abc//  word", find="abc", search=mod.WORD)
    yield test, c(input="/abc//  python-replace", find="abc", search=mod.REPY)
    yield test, c(input="/abc//   no-wrap", find="abc", wrap=False)

def test_Finder_mark_occurrences():
    def test(c):
        string = "the text is made of many texts"
        m = Mocker()
        editor = m.mock(Editor)
        editor._Finder__last_mark >> (None, 0)
        editor._Finder__last_mark = (c.options.find_text, c.count)
        app = m.mock('editxt.application.Application')
        app.theme["highlight_selected_text.color"] >> "<color>"
        (editor.text << Text(string)).count(1, None)
        full_range = (0, len(string))
        layout = editor.text_view.layoutManager()
        layout.removeTemporaryAttribute_forCharacterRange_(
            ak.NSBackgroundColorAttributeName, full_range)
        finder = Finder((lambda: editor), c.options, app)
        if c.options.find_text:
            mark_range = layout.addTemporaryAttribute_value_forCharacterRange_ >> m.mock()
            mark = mark_range(ak.NSBackgroundColorAttributeName, ANY, ANY)
            expect(mark).count(c.count)
        with m:
            count = finder.mark_occurrences(c.options.find_text, c.allow_regex)
            eq_(count, c.count)

    o = FindOptions
    c = TestConfig(allow_regex=False)
    yield test, c(options=o(find_text=""), count=0)
    yield test, c(options=o(find_text="text"), count=2)
    yield test, c(options=o(find_text="[t]"), count=0)
    yield test, c(options=o(find_text="[t]", regular_expression=True), count=0)
    yield test, c(options=o(find_text="text", match_entire_word=True), count=1)
    c = c(allow_regex=True)
    yield test, c(options=o(find_text="[t]", regular_expression=True), count=5)

def test_Finder():
    BEEP = const.Constant("BEEP")
    def test(c):
        m = Mocker()
        beep = m.replace(mod, "beep")
        options = make_options(c)
        editor = m.mock(Editor)
        (editor.selection << c.select).count(0, None)
        (editor.text << Text(c.text)).count(0, None)

        def put(text, rng, select=False):
            editor.text[rng] = text
        (editor.put(ANY, ANY) << (c.expect is not BEEP)).call(put).count(0, 1)
        if c.expect is BEEP:
            beep()
        finder = Finder((lambda: editor), options, None)
        with m:
            if isinstance(c.expect, Exception):
                def check(err):
                    print(err)
                    eq_(str(err), str(c.expect))
                with assert_raises(type(c.expect), msg=check):
                    getattr(finder, c.action)(None)
            else:
                getattr(finder, c.action)(None)
                if c.expect is BEEP:
                    eq_(editor.text[:], c.text)
                else:
                    eq_(editor.text[:], c.expect)
    c = TestConfig(text="The quick Fox is a brown fox", select=(0, 16))

    c = c(search="literal", action="replace_one")
    yield test, c(
        find="Fox", replace="cat",
        select=(0, 3),
        expect=BEEP)
    yield test, c(
        find="Fox", replace="cat",
        select=(10, 0),
        expect=BEEP)
    yield test, c(
        find="Fox", replace="cat",
        select=(10, 2),
        expect=BEEP)
    yield test, c(
        find="Fox", replace="cat",
        select=(10, 3),
        expect="The quick cat is a brown fox")
    yield test, c(
        find="", replace="cat",
        select=(10, 3),
        expect=BEEP)
    yield test, c(
        find="[F]ox", replace="cat",
        select=(10, 3),
        expect=BEEP)
    yield test, c(
        find="Fox", replace="cat",
        select=(10, 5),
        expect="The quick cat is a brown fox")

    c = c(search="python-replace")
    yield test, c(
        find="[Ff]ox", replace="match[0].upper()",
        select=(0, 3),
        action="replace_one",
        expect=BEEP)
    yield test, c(
        find="[Ff]ox", replace="match[0].upper()",
        select=(10, 3),
        action="replace_one",
        expect="The quick FOX is a brown fox")
    yield test, c(
        find="[Ff]ox", replace="match[0].upper()",
        select=(10, 5),
        action="replace_one",
        expect="The quick FOX is a brown fox")
    yield test, c(
        find="n [Ff]ox", replace="match[0].upper()",
        select=(10, 3),
        action="replace_one",
        expect=BEEP)
    yield test, c(
        find="[Ff]ox", replace="match[0].lower()",
        action="replace_all",
        expect="The quick fox is a brown fox")
    yield test, c(
        find="[Ff]ox", replace="match.group(0).upper()",
        action="replace_all_in_selection",
        expect="The quick FOX is a brown fox")
    yield test, c(
        find="[Ff]ox", replace="match[1]",
        action="replace_all",
        expect="The quick "
            "!! Fox >> match[1] >> IndexError: no such group !!"
            " is a brown "
            "!! fox >> match[1] >> IndexError: no such group !!")
    yield test, c(
        find="[Ff]ox", replace="",
        action="replace_all",
        expect="The quick "
            "!! Fox >>  >> Python Replace expected str, got None !!"
            " is a brown "
            "!! fox >>  >> Python Replace expected str, got None !!")
    yield test, c(
        find="[Ff]ox", replace="1",
        action="replace_all",
        expect="The quick "
            "!! Fox >> 1 >> Python Replace expected str, got 1 !!"
            " is a brown "
            "!! fox >> 1 >> Python Replace expected str, got 1 !!")
    yield test, c(
        find="x", replace="match(", action="replace_all",
        expect=mod.InvalidPythonExpression(
            "def repy(match, range_):\n"
            "    return match(",
            "unexpected EOF while parsing (<string>, line 2)"))
    yield test, c(
        find="(", replace="match[0].lower()",
        action="replace_all",
        expect=mod.CommandError(
            "cannot compile regex '(' : missing ), unterminated subpattern at position 0"))

    c = TestConfig(
        text="The \U0001f612 Fox is a \U0001f34c fox",
        search="literal",
        action="replace_one",
    )
    yield test, c(
        find="Fox", replace="cat",
        select=(7, 7),
        expect="The \U0001f612 cat is a \U0001f34c fox")
    yield test, c(
        find="[Ff]ox", replace="dog",
        select=(0, 0),
        search="regex",
        action="replace_all",
        expect="The \U0001f612 dog is a \U0001f34c dog")
    yield test, c(
        find="[Ff]ox", replace="match[0].upper()",
        select=(7, 7),
        search="python-replace",
        action="replace_one",
        expect="The \U0001f612 FOX is a \U0001f34c fox")

def test_FindController_shared_controller():
    with test_app() as app:
        fc = FindController.shared_controller(app)
        assert isinstance(fc, FindController), fc
        f2 = FindController.shared_controller(app)
        assert fc is f2

def test_FindController_validate_action():
    def test(c):
        with test_app() as app:
            m = Mocker()
            fc = FindController(app)
            if c.tag in fc.action_registry:
                editor = (m.mock(Editor) if c.has_target else None)
                m.method(fc.get_editor)() >> editor
                if c.has_target:
                    if c.tag in mod.SELECTION_REQUIRED_ACTIONS:
                        editor.selection >> (0, c.sel)
            with m, replattr(fc, 'options', FindOptions()):
                result = fc.validate_action(c.tag)
                eq_(result, c.result)
    c = TestConfig(has_target=True, result=True, tag=0)
    yield test, c(has_target=False, result=False)
    yield test, c(tag=mod.ACTION_FIND_SELECTED_TEXT_REVERSE+1, result=False)

    for tag in [
        ak.NSFindPanelActionShowFindPanel,
        ak.NSFindPanelActionNext,
        ak.NSFindPanelActionPrevious,
        ak.NSFindPanelActionReplace,
        ak.NSFindPanelActionReplaceAll,
        ak.NSFindPanelActionReplaceAndFind,
        ak.NSFindPanelActionReplaceAllInSelection,
        ak.NSFindPanelActionSetFindString,
    ]:
        yield test, c(tag=tag)

    for tag in [
        mod.ACTION_FIND_SELECTED_TEXT,
        mod.ACTION_FIND_SELECTED_TEXT_REVERSE,
    ]:
        yield test, c(tag=tag, sel=0, result=False)
        yield test, c(tag=tag, sel=2)
    
def test_FindController_perform_action():
    def test(c):
        with test_app() as app:
            m = Mocker()
            fc = FindController(app)
            flog = m.replace("editxt.command.find.log")
            beep = m.replace(mod, "beep")
            get_editor = m.method(fc.get_editor)
            sender = m.mock()
            (sender.tag() << c.tag).count(1, 2)
            func = None
            for tag, meth in list(fc.action_registry.items()):
                fc.action_registry[tag] = temp = m.mock(meth)
                if tag == c.tag:
                    func = temp
            if c.fail:
                flog.info(ANY, c.tag)
            else:
                if c.error:
                    err = mod.CommandError("error!")
                    expect(func(sender)).throw(err)
                    beep()
                    editor = get_editor() >> (m.mock() if c.target else None)
                    if c.target:
                        editor.message("error!", msg_type=const.ERROR)
                    else:
                        flog.warn(err)
                else:
                    func(sender)
            with m:
                fc.perform_action(sender)
    c = TestConfig(fail=False, error=False)
    for tag in [
        ak.NSFindPanelActionShowFindPanel,
        ak.NSFindPanelActionNext,
        ak.NSFindPanelActionPrevious,
        ak.NSFindPanelActionReplace,
        ak.NSFindPanelActionReplaceAll,
        ak.NSFindPanelActionReplaceAndFind,
        ak.NSFindPanelActionReplaceAllInSelection,
        ak.NSFindPanelActionSetFindString,
        mod.ACTION_FIND_SELECTED_TEXT,
        mod.ACTION_FIND_SELECTED_TEXT_REVERSE,
    ]:
        yield test, c(tag=tag)
    yield test, c(tag=mod.ACTION_FIND_SELECTED_TEXT_REVERSE + 1, fail=True)
    yield test, c(tag=ak.NSFindPanelActionNext, error=True, target=True)
    yield test, c(tag=ak.NSFindPanelActionNext, error=True, target=False)

def test_FindController_show_find_panel():
    with test_app() as app:
        m = Mocker()
        fc = FindController(app)
        sender = m.mock()
        opts = m.property(fc, "options").value
        opts.willChangeValueForKey_("recent_finds")
        m.method(fc.load_options)()
        opts.didChangeValueForKey_("recent_finds")
        m.property(fc, "find_text")
        m.method(fc.gui.show)()
        with m:
            fc.show_find_panel(sender)

def test_FindController_actions():
    def test(c):
        with test_app() as app:
            m = Mocker()
            fc = FindController(app)
            sender = m.mock()
            if "do" in c:
                c.do(m, c, fc, sender)
            else:
                m.method(fc.finder, c.real)(*c.args)
            with m:
                getattr(fc, c.meth)(sender)
    c = TestConfig()
    yield test, c(meth="find_next", real="find", args=(FORWARD,))
    yield test, c(meth="find_previous", real="find", args=(BACKWARD,))

    def do(m, c, fc, sender):
        m.method(fc.set_find_text_with_selection)(sender)
        m.method(fc.save_options)() >> c.saved
        if c.saved:
            m.method(fc.finder.find_next)(sender)
    yield test, c(meth="find_selected_text", do=do, saved=True)
    yield test, c(meth="find_selected_text", do=do, saved=False)

    def do(m, c, fc, sender):
        m.method(fc.set_find_text_with_selection)(sender)
        m.method(fc.save_options)() >> c.saved
        if c.saved:
            m.method(fc.finder.find_previous)(sender)
    yield test, c(meth="find_selected_text_reverse", do=do, saved=True)
    yield test, c(meth="find_selected_text_reverse", do=do, saved=False)

    def do(m, c, fc, sender):
        kw = {"in_selection": True} if c.sel_only else {}
        m.method(fc.finder._replace_all)(**kw)
    yield test, c(meth="replace_all", do=do, sel_only=False)
    yield test, c(meth="replace_all_in_selection", do=do, sel_only=True)

    def do(m, c, fc, sender):
        m.method(fc.finder.replace_one)(sender)
        m.method(fc.finder.find_next)(sender)
    yield test, c(meth="replace_and_find_next", do=do)

    def do(m, c, fc, sender):
        window = fc.gui.window = m.mock(ak.NSWindow)
        if m.method(fc.save_options)() >> c.saved:
            window.orderOut_(sender)
            m.method(fc.finder, c.real)(sender)
    for saved in (True, False):
        cx = c(saved=saved, do=do)
        yield test, cx(meth="panelFindNext_", real="find_next")
        yield test, cx(meth="panelFindPrevious_", real="find_previous")
        yield test, cx(meth="panelReplace_", real="replace_one")
        yield test, cx(meth="panelReplaceAll_", real="replace_all")
        yield test, cx(meth="panelReplaceAllInSelection_", real="replace_all_in_selection")
        #yield test, cx(meth="panelMarkAll_", real="mark_all")

    def do(m, c, fc, sender):
        options = m.replace(fc, "options")
        (options.regular_expression << True).count(0, None)
        if m.method(fc.validate_expression)() >> c.valid:
            text = getattr(options, c.val) >> "<value>"
            m.method(fc.count_occurrences)(text, c.regex)
    for v in (True, False):
        cx = c(valid=v, do=do)
        yield test, cx(meth="panelCountFindText_", val="find_text", regex=True)
        yield test, cx(meth="panelCountReplaceText_", val="replace_text", regex=False)

    def do(m, c, fc, sender):
        ws = m.replace(ak, 'NSWorkspace')
        url = fn.NSURL.URLWithString_(const.REGEX_HELP_URL)
        (ws.sharedWorkspace() >> m.mock(ak.NSWorkspace)).openURL_(url)
    yield test, c(meth="regexHelp_", do=do)

def test_FindController_recentFindSelected_():
    Config = TestConfig
    def test(command, options):
        m = Mocker()
        nspb = m.replace(ak, 'NSPasteboard')
        pboard = nspb.pasteboardWithName_(ak.NSFindPboard)
        pboard.availableTypeFromArray_([ak.NSStringPboardType]) >> None
        with m, test_app() as app:
            fc = FindController(app)
            sender = Config(selectedItem=lambda:Config(title=lambda:command))
            fc.recentFindSelected_(sender)
            eq_(fc.options._target, options)

    yield test, "/abc", FindOptions(find_text="abc")
    yield test, "/abc// unknown-action", FindOptions()
    yield test, "/abc/def/i all word no-wrap", FindOptions(
        find_text="abc",
        replace_text="def",
        action="find_next",
        ignore_case=True,
        search_type=mod.WORD,
        wrap_around=False,
    )

def test_FindController_finder_find():
    def test(c):
        with test_app() as app:
            m = Mocker()
            fc = FindController(app)
            beep = m.replace(mod, 'beep')
            dobeep = True
            direction = "<direction>"
            _find = m.method(fc.finder._find)
            editor = m.replace(fc.finder, 'get_editor')() >> (m.mock(TextView) if c.has_tv else None)
            if c.has_tv:
                m.replace(fc.finder, "options").find_text >> c.ftext
                if c.ftext:
                    found = TestConfig(range="<range>")
                    _find(editor, direction) >> (found if c.found else None)
                    if c.found:
                        editor.selection = found.range
                        editor.text_view.scrollRangeToVisible_(found.range)
                        dobeep = False
            if dobeep:
                beep()
            with m:
                fc.finder.find(direction)
    c = TestConfig(ftext="find", has_tv=True)
    yield test, c(has_tv=False)
    yield test, c(has_tv=True, ftext="")
    yield test, c(found=False)
    yield test, c(found=True)

def test_FindController_validate_expression():
    def test(c):
        with test_app() as app:
            m = Mocker()
            fc = FindController(app)
            fc.options = make_options(c)
            beep = m.replace(mod, "beep")
            sheet = m.replace(ak, "NSBeginAlertSheet")
            gui = m.replace(fc, "gui")
            ftext = m.mock(ak.NSTextField)
            if c.search != mod.LITERAL:
                if c.ftext is None:
                    gui.find_text >> None
                else:
                    (gui.find_text << ftext).count(1, None)
                    ftext.stringValue() >> c.ftext
                if not c.expect:
                    beep()
                    sheet(
                        ANY,
                        "OK", None, None,
                        gui.window >> "<window>", None, None, None, 0,
                        ANY,
                    );
            with m:
                result = fc.validate_expression()
                eq_(result, c.expect)
    c = TestConfig(search=mod.REGEX, expect=True)
    yield test, c(ftext=None)
    yield test, c(ftext="(", search=mod.LITERAL)
    yield test, c(ftext="(", expect=False)

def test_FindController__replace_all():
    def test(c):
        with test_app() as app:
            m = Mocker()
            fc = FindController(app)
            beep = m.replace(mod, 'beep')
            editor = (m.mock(Editor) if c.has_tv else None)
            m.replace(fc.finder, 'get_editor')() >> editor
            options = m.replace(fc.finder, "options")
            ftext = options.find_text >> c.ftext
            range = (editor.selection >> c.sel) if c.has_tv else None
            if c.has_tv and c.ftext and ((c.sel_only and c.sel[1] > 0) or not c.sel_only):
                text = editor.text >> Text(c.text)
                if not c.sel_only:
                    if (options.wrap_around >> c.wrap):
                        range = (0, 0)
                    else:
                        range = (range[0], len(text) - range[0])
                if options.regular_expression >> c.regex:
                    finditer = m.method(fc.finder.regexfinditer)
                elif options.match_entire_word >> c.mword:
                    ftext = "\\b" + re.escape(ftext) + "\\b"
                    finditer = m.method(fc.finder.regexfinditer)
                else:
                    finditer = m.method(fc.finder.simplefinditer)
                rtext = options.replace_text >> c.rtext
                found = None
                ranges = []
                rtexts = []
                items = []
                FoundRange = make_found_range_factory(
                    FindOptions(regular_expression=c.regex, match_entire_word=c.mword))
                for rng in c.ranges:
                    found = FoundRange(rng)
                    if ranges:
                        rtexts.append(text[sum(ranges[-1]):rng[0]])
                    ranges.append(found.range)
                    rtexts.append(rtext)
                    items.append(found)
                finditer(text, ftext, range, FORWARD, False) >> items
                if ranges:
                    start = c.ranges[0][0]
                    range = (start, sum(c.ranges[-1]) - start)
                    value = "".join(rtexts)

                    def put(val, rng, select=False):
                        text[rng] = val
                    (editor.put(value, range) << c.replace).call(put)
            if c.beep:
                beep()
            with m:
                fc.finder._replace_all(c.sel_only)
                if c.ranges and c.replace:
                    eq_(text[:], "<XEXX>")
    c = TestConfig(has_tv=True, text="<TEXT>", ftext="T", rtext="X",
        sel_only=False, sel=(1, 0), wrap=False, regex=False, mword=False,
        ranges=[], replace=True, beep=True)
    yield test, c(has_tv=False)
    yield test, c(ftext="")
    yield test, c(sel_only=True, sel=(1, 0))
    yield test, c(sel_only=True, sel=(1, 2))
    yield test, c(wrap=True)
    yield test, c(regex=True)
    yield test, c(mword=True)
    yield test, c
    yield test, c(ranges=[(1, 1), (4, 1)], replace=False)
    yield test, c(ranges=[(1, 1), (4, 1)], beep=False)

def test_FindController_count_occurrences():
    def test(c):
        with test_app() as app:
            m = Mocker()
            beep = m.replace(mod, 'beep')
            fc = FindController(app)
            flash = m.method(fc.flash_status_text)
            mark = m.method(fc.finder.mark_occurrences)
            m.method(fc.get_editor)() >> (m.mock(Editor) if c.has_tv else None)
            if c.has_tv:
                ftext = "<find>"
                mark(ftext, c.regex, timeout=30) >> c.cnt
                if c.cnt:
                    flash("%i occurrences" % c.cnt)
                else:
                    flash("Not found")
            else:
                beep()
            with m:
                fc.count_occurrences("<find>", c.regex)
    c = TestConfig(has_tv=True, regex=False, cnt=0)
    yield test, c
    yield test, c(regex=True)
    yield test, c(cnt=42)
    yield test, c(has_tv=False)

def test_FindController_get_editor():
    def test(c):
        with test_app() as app:
            m = Mocker()
            fc = FindController(app)
            iter_windows = m.method(app.iter_windows)
            if c.has_window:
                window = m.mock(Window)
                x = iter([window])
                window.current_editor >> (m.mock(Editor) if c.has_editor else None)
            else:
                x = iter([])
            iter_windows() >> x
            assert fc.app is not None
            with m:
                result = fc.get_editor()
                if c.has_editor:
                    assert result is not None
                else:
                    eq_(result, None)
    c = TestConfig(has_window=False, has_editor=False)
    yield test, c
    yield test, c(has_window=True)
    yield test, c(has_window=True, has_editor=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Test FindOptions

# def test_FindOptions_defaults():
#   options = FindOptions(FindController)
#   for name, value in options.defaults.items():
#       eq_(getattr(options, name), value, name)

def test_FindOptions_dependent_options():
    from collections import namedtuple
    def test(c):
        options = FindOptions()
        setattr(options, c.att.name, c.att.before)
        for dep in c.deps:
            setattr(options, dep.name, dep.before)
        eq_(getattr(options, c.att.name), c.att.before, c.att.name)
        for dep in c.deps:
            eq_(getattr(options, dep.name), dep.before, dep.name)
        # make the change, which fires the dependent change
        setattr(options, c.att.name, c.att.after)
        eq_(getattr(options, c.att.name), c.att.after, c.att.name)
        for dep in c.deps:
            eq_(getattr(options, dep.name), dep.after, dep.name)
    p = namedtuple("F", ["name", "before", "after"])
    c = TestConfig()
    yield test, c(att=p("regular_expression", True, True), deps=[
        p("match_entire_word", False, False),
        p("python_replace", True, True),
        p("search_type", mod.REPY, mod.REPY),
    ])
    yield test, c(att=p("regular_expression", False, True), deps=[
        p("match_entire_word", True, False),
        p("python_replace", False, False),
        p("search_type", mod.WORD, mod.REGEX),
    ])
    yield test, c(att=p("regular_expression", True, False), deps=[
        p("match_entire_word", False, False),
        p("python_replace", False, False),
        p("search_type", mod.REGEX, mod.LITERAL),
    ])
    yield test, c(att=p("match_entire_word", False, True), deps=[
        p("regular_expression", True, False),
        p("python_replace", False, False),
        p("search_type", mod.REGEX, mod.WORD),
    ])
    yield test, c(att=p("match_entire_word", True, False), deps=[
        p("regular_expression", False, False),
        p("python_replace", False, False),
        p("search_type", mod.WORD, mod.LITERAL),
    ])
    yield test, c(att=p("python_replace", False, True), deps=[
        p("regular_expression", False, True),
        p("match_entire_word", True, False),
        p("search_type", mod.WORD, mod.REPY),
    ])
    yield test, c(att=p("python_replace", True, False), deps=[
        p("regular_expression", True, True),
        p("match_entire_word", False, False),
        p("search_type", mod.REPY, mod.REGEX),
    ])
    yield test, c(att=p("python_replace", False, False), deps=[
        p("regular_expression", False, False),
        p("match_entire_word", False, False),
        p("search_type", mod.LITERAL, mod.LITERAL),
    ])
    yield test, c(att=p("python_replace", False, False), deps=[
        p("regular_expression", False, False),
        p("match_entire_word", True, True),
        p("search_type", mod.WORD, mod.WORD),
    ])

def test_FindController_load_options():
    def test(c):
        m = Mocker()
        nspb = m.replace(ak, 'NSPasteboard')
        pboard = nspb.pasteboardWithName_(ak.NSFindPboard)
        pboard.availableTypeFromArray_([ak.NSStringPboardType]) >> (c.ftext is not None)
        if c.ftext is not None:
            pboard.stringForType_(ak.NSStringPboardType) >> c.ftext
        with test_app() as app:
            history = app.text_commander.history
            if c.hist is not None:
                history.append(c.hist)
            with m:
                fc = FindController(app) # calls load_options()
                eq_(fc.options._target, FindOptions(**c.opts))
                eq_(fc.options.recent_finds, [] if c.hist is None else [c.hist])
    o = dict
    c = TestConfig(ftext=None, hist=None, opts={})
    yield test, c
    yield test, c(ftext="", hist="/abc", opts=o(find_text=""))
    yield test, c(ftext="def", hist="/abc", opts=o(find_text="def"))
    yield test, c(hist="/")
    yield test, c(hist="/abc", opts=o(find_text="abc"))
    yield test, c(hist="//repl", opts=o(replace_text="repl"))
    yield test, c(hist="/abc//i find-previous literal no-wrap",
                    opts=o(
                        find_text="abc",
                        action="find_previous",
                        ignore_case=True,
                        search_type=mod.LITERAL,
                        wrap_around=False,
                    ))

def test_FindController_save_options():
    def test(c):
        m = Mocker()
        with test_app() as app:
            history = app.text_commander.history
            fc = FindController(app) # calls load_options()
            fc.options.find_text = "" # clear value from real pasteboard
            fc.options.ignore_case = False
            nspb = m.replace(ak, 'NSPasteboard')
            if "find_text" in c.opts:
                pboard = nspb.pasteboardWithName_(ak.NSFindPboard)
                pboard.declareTypes_owner_([ak.NSStringPboardType], None)
                pboard.setString_forType_(c.opts["find_text"], ak.NSStringPboardType)
            with m:
                for k, v in c.opts.items():
                    setattr(fc.options, k, v)
                print(fc.options._target)
                eq_(fc.save_options(), c.res, fc.options._target)
                eq_(list(history), [] if c.hist is None else [c.hist])
    o = dict
    c = TestConfig(opts={}, hist=None, res=True)
    yield test, c(res=False)
    yield test, c(opts=o(find_text="abc"), hist="/abc//")
    yield test, c(opts=o(replace_text="abc"), res=False)
    yield test, c(opts=o(
            find_text="abc",
            replace_text="def",
            ignore_case=True,
            action="replace_all",
            search_type=mod.WORD,
            wrap_around=False,
        ), hist="/abc/def/i replace-all word no-wrap")

def test_Match():
    match = mod.Match(re.search("(\d)(\d)(\d)(\d)(\d)", "12345"))

    yield eq_, match.groups(), ("1", "2", "3", "4", "5")

    def test(key, result, *slice):
        if slice:
            if len(slice) == 1:
                end = slice[0]
                eq_(match[key:end], result)
            else:
                end, step = slice
                eq_(match[key:end:step], result)
        else:
            eq_(match[key], result)
    yield test, 0, "12345"
    yield test, 1, "1"
    yield test, 5, "5"
    yield test, None, "123", 3
    yield test, 0, "123", 3
    yield test, 1, "23", 3
    yield test, 1, "24", None, 2
    yield test, 0, "135", 8, 2

    def test(func, result):
        eq_(func(match), result)
    yield test, str, "12345"
    yield test, repr, "<Match '12345'>"

    yield eq_, repr(mod.Match(None)), "<Match None>"
    yield eq_, str(mod.Match(None)), "None"

# def test():
#     assert False, "stop"

def test_minimal_regex_escape():
    def test(input, output):
        eq_(mod.minimal_regex_escape(input), output)

    yield test, ".*+?\\|-^$()[]{", "\\.\\*\\+\\?\\\\\\|\\-\\^\\$\\(\\)\\[\\]\\{"
    yield test, "( \n\t )", "\\( \n\t \\)"
    yield test, "}:!", "}:!"
