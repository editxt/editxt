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
from __future__ import with_statement

import logging
import os
import re
from contextlib import closing
from tempfile import gettempdir

from AppKit import *
from Foundation import *
from mocker import Mocker, MockerTestCase, expect, ANY, MATCH
from nose.tools import *
from editxt.test.util import (assert_raises, TestConfig, untested,
    check_app_state, replattr)
from editxt.test.command.test_base import replace_history

import editxt
import editxt.constants as const
import editxt.command.find as mod
from editxt.command.find import (Finder, FindController, FindOptions,
    make_found_range_factory)
from editxt.command.find import FORWARD, BACKWARD
from editxt.command.parser import RegexPattern
from editxt.controls.textview import TextView

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement TextDocumentView.pasteboard_data()
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
        options = make_options(c)
        m = Mocker()
        tv = m.mock(NSTextView)
        finder_cls = m.replace("editxt.command.find.Finder")
        save_paste = m.replace(mod, "save_to_find_pasteboard")
        def check_options(get_tv, args):
            eq_(get_tv(), tv)
            eq_(args, options)
        finder = m.mock(Finder)
        save_paste(c.find)
        (finder_cls(ANY, ANY) << finder).call(check_options)
        getattr(finder, c.action)("<sender>") >> c.message
        with m:
            args = mod.find.arg_parser.parse(c.input)
            result = mod.find(tv, "<sender>", args)
            eq_(result, c.message)

    c = TestConfig(find="", replace="", search=mod.REGEX, ignore_case=False,
                   wrap=True, action="find_next", message=None)
    yield test, c(input=u"")
    yield test, c(input=u"/abc", find="abc")
    yield test, c(input=u":abc", find="abc")
    yield test, c(input=u":abc\:", find=r"abc\:")
    yield test, c(input=u"/\/abc\//", find=r"\/abc\/")
    yield test, c(input=u"/abc/def", find="abc", replace="def")
    yield test, c(input=u"/abc/def/", find="abc", replace="def")
    yield test, c(input=u"/abc/def/i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u":abc:def:i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u"'abc'def'i", find="abc", replace="def", ignore_case=True)
    yield test, c(input=u'"abc"def"i', find="abc", replace="def", ignore_case=True)
    yield test, c(input=u":ab\:c:def:i", find=r"ab\:c", replace="def", ignore_case=True)
    yield test, c(input=u"/abc// n", find="abc", action="find_next")
    yield test, c(input=u"/abc// p", find="abc", action="find_previous")
    yield test, c(input=u"/abc// previous", find="abc", action="find_previous")
    yield test, c(input=u"/abc// o", find="abc", action="replace_one")
    yield test, c(input=u"/abc// a", find="abc", action="replace_all")
    yield test, c(input=u"/abc// s", find="abc", action="replace_all_in_selection")
    yield test, c(input=u"/abc// c", find="abc", action="count_occurrences",
                  message="Found 3 occurrences")
    yield test, c(input=u"/abc//  regex", find="abc", search=mod.REGEX)
    yield test, c(input=u"/abc//  literal", find="abc", search=mod.LITERAL)
    yield test, c(input=u"/abc//  word", find="abc", search=mod.WORD)
    yield test, c(input=u"/abc//  python-replace", find="abc", search=mod.REPY)
    yield test, c(input=u"/abc//   no-wrap", find="abc", wrap=False)

def test_Finder_mark_occurrences():
    def test(c):
        text = "the text is made of many texts"
        m = Mocker()
        tv = m.mock(TextView)
        tv._Finder__last_mark >> (None, 0)
        tv._Finder__last_mark = (c.options.find_text, c.count)
        ts = tv.textStorage() >> m.mock(NSTextStorage)
        app = m.replace(editxt, "app")
        app.config["highlight_selected_text.color"] >> "<color>"
        full_range = NSMakeRange(0, ts.length() >> len(text))
        layout = tv.layoutManager()
        layout.removeTemporaryAttribute_forCharacterRange_(
            NSBackgroundColorAttributeName, full_range)
        find_target = lambda: tv
        finder = Finder(find_target, c.options)
        if c.options.find_text:
            text = NSString.alloc().initWithString_(text)
            (tv.string() << text).count(1, None)
            mark_range = layout.addTemporaryAttribute_value_forCharacterRange_ >> m.mock()
            mark = mark_range(NSBackgroundColorAttributeName, ANY, ANY)
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

def test_Finder_python_replace():
    def test(c):
        m = Mocker()
        options = make_options(c)
        tv = m.mock(TextView)
        tv.selectedRange() >> NSMakeRange(0, 16)
        tv.string() >> NSString.alloc().initWithString_(c.text)
        if not isinstance(c.expect, Exception):
            result = [c.text]
            def replace(range, value):
                start, end = range
                text = result[0]
                result[0] = text[:start] + value + text[start + end:]
            tv.shouldChangeTextInRange_replacementString_(ANY, ANY) >> True
            expect(tv.textStorage().replaceCharactersInRange_withString_(
                ANY, ANY)).call(replace)
            tv.didChangeText()
            tv.setNeedsDisplay_(True)
        finder = Finder((lambda: tv), options)
        with m:
            if isinstance(c.expect, Exception):
                def check(err):
                    print err
                    eq_(str(err), str(c.expect))
                with assert_raises(type(c.expect), msg=check):
                    getattr(finder, c.action)(None)
            else:
                getattr(finder, c.action)(None)
                eq_(result[0], c.expect)
    c = TestConfig(search="python-replace", text="The quick Fox is a brown fox")
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
        find="x", replace="match(", action="replace_all",
        expect=mod.InvalidPythonExpression(
            "def repy(match, range_):\n"
            "    return match(",
            "invalid syntax (<string>, line 2)"))

def test_FindController_shared_controller():
    fc = FindController.shared_controller()
    assert isinstance(fc, FindController), fc
    f2 = FindController.shared_controller()
    assert fc is f2

def test_FindController_validate_action():
    def test(c):
        m = Mocker()
        fc = FindController.shared_controller()
        if c.tag in fc.action_registry:
            tv = (m.mock(TextView) if c.has_target else None)
            m.method(fc.find_target)() >> tv
            if c.has_target:
                if c.tag in mod.SELECTION_REQUIRED_ACTIONS:
                    tv.selectedRange().length >> c.sel
        with m, replattr(fc, 'options', FindOptions()):
            result = fc.validate_action(c.tag)
            eq_(result, c.result)
    c = TestConfig(has_target=True, result=True, tag=0)
    yield test, c(has_target=False, result=False)
    yield test, c(tag=mod.ACTION_FIND_SELECTED_TEXT_REVERSE+1, result=False)

    for tag in [
        NSFindPanelActionShowFindPanel,
        NSFindPanelActionNext,
        NSFindPanelActionPrevious,
        NSFindPanelActionReplace,
        NSFindPanelActionReplaceAll,
        NSFindPanelActionReplaceAndFind,
        NSFindPanelActionReplaceAllInSelection,
        NSFindPanelActionSetFindString,
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
        m = Mocker()
        fc = FindController()
        flog = m.replace("editxt.command.find.log")
        sender = m.mock()
        (sender.tag() << c.tag).count(1, 2)
        func = None
        for tag, meth in fc.action_registry.items():
            fc.action_registry[tag] = temp = m.mock(meth)
            if tag == c.tag:
                func = temp
        if c.fail:
            flog.info(ANY, c.tag)
        else:
            func(sender)
        with m:
            fc.perform_action(sender)
    c = TestConfig(fail=False)
    yield test, c(tag=mod.ACTION_FIND_SELECTED_TEXT_REVERSE + 1, fail=True)
    for tag in [
        NSFindPanelActionShowFindPanel,
        NSFindPanelActionNext,
        NSFindPanelActionPrevious,
        NSFindPanelActionReplace,
        NSFindPanelActionReplaceAll,
        NSFindPanelActionReplaceAndFind,
        NSFindPanelActionReplaceAllInSelection,
        NSFindPanelActionSetFindString,
        mod.ACTION_FIND_SELECTED_TEXT,
        mod.ACTION_FIND_SELECTED_TEXT_REVERSE,
    ]:
        yield test, c(tag=tag)

def test_FindController_show_find_panel():
    m = Mocker()
    fc = FindController.shared_controller()
    sender = m.mock()
    opts = m.property(fc, "options").value
    opts.willChangeValueForKey_("recent_finds")
    m.method(fc.load_options)()
    opts.didChangeValueForKey_("recent_finds")
    m.property(fc, "find_text")
    m.method(fc.gui.showWindow_)(fc)
    fc.find_text.selectText_(sender)
    with m:
        fc.show_find_panel(sender)

def test_FindController_actions():
    def test(c):
        m = Mocker()
        fc = FindController.shared_controller()
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
        beep = m.replace(mod, 'NSBeep')
        dobeep = True
        tv = m.replace(fc.finder, 'find_target')() >> (m.mock(TextView) if c.has_tv else None)
        if c.has_tv:
            options = m.replace(fc.finder, "options")
            rtext = options.replace_text >> "abc"
            options.regular_expression >> c.regex
            FoundRange = make_found_range_factory(FindOptions(regular_expression=c.regex))
            if c.regex:
                if c.rfr:
                    tv._Finder__recently_found_range >> FoundRange(None)
                elif c.rfr is None:
                    expect(tv._Finder__recently_found_range).throw(AttributeError)
                else:
                    tv._Finder__recently_found_range >> None
            range = tv.selectedRange() >> m.mock()
            tv.shouldChangeTextInRange_replacementString_(range, rtext) >> c.act
            if c.act:
                tv.textStorage().replaceCharactersInRange_withString_(range, rtext)
                tv.didChangeText()
                tv.setNeedsDisplay_(True)
                dobeep = False
        if dobeep:
            beep()
    cx = c(meth="replace_one", do=do, has_tv=True, regex=True, rfr=True, act=True)
    yield test, cx
    yield test, cx(has_tv=False)
    yield test, cx(regex=False)
    yield test, cx(rfr=False)
    yield test, cx(rfr=None)
    yield test, cx(act=False)

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
        if m.method(fc.save_options)() >> c.saved:
            (m.method(fc.gui.window)() >> m.mock(NSWindow)).orderOut_(sender)
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
        ws = m.replace(mod, 'NSWorkspace')
        url = NSURL.URLWithString_(const.REGEX_HELP_URL)
        (ws.sharedWorkspace() >> m.mock(NSWorkspace)).openURL_(url)
    yield test, c(meth="regexHelp_", do=do)

def test_FindController_recentFindSelected_():
    Config = TestConfig
    def test(command, options):
        m = Mocker()
        nspb = m.replace(mod, 'NSPasteboard')
        pboard = nspb.pasteboardWithName_(NSFindPboard)
        pboard.availableTypeFromArray_([NSStringPboardType]) >> None
        with m, replace_history() as history:
            fc = FindController()
            sender = Config(selectedItem=lambda:Config(title=lambda:command))
            fc.recentFindSelected_(sender)
            eq_(fc.options._target, options)

    yield test, "/abc", FindOptions(find_text="abc")
    yield test, "/abc// unknown-action", FindOptions()
    yield test, "/abc/def/i all word no-wrap", FindOptions(
        find_text=u"abc",
        replace_text=u"def",
        action="find_next",
        ignore_case=True,
        search_type=mod.WORD,
        wrap_around=False,
    )

def test_FindController_finder_find():
    def test(c):
        m = Mocker()
        fc = FindController.shared_controller()
        beep = m.replace(mod, 'NSBeep')
        dobeep = True
        direction = "<direction>"
        _find = m.method(fc.finder._find)
        tv = m.replace(fc.finder, 'find_target')() >> (m.mock(TextView) if c.has_tv else None)
        m.replace(fc.finder, "options").find_text >> c.ftext
        if c.has_tv and c.ftext:
            sel = tv.selectedRange() >> (1, 2)
            range = _find(tv, c.ftext, sel, direction) >> ("<range>" if c.found else None)
            if c.found:
                tv.setSelectedRange_(range)
                tv.scrollRangeToVisible_(range)
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

def test_FindController__find():
    def test(c):
        m = Mocker()
        fc = FindController.shared_controller()
        tv = m.mock(TextView)
        regexfind = m.method(fc.finder.regexfinditer)
        simplefind = m.method(fc.finder.simplefinditer)
        sel = NSMakeRange(1, 2)
        direction = "<direction>"
        options = m.property(fc.finder, "options").value >> m.mock(FindOptions)
        ftext = u"<find>"
        if options.regular_expression >> c.regex:
            finditer = regexfind
        elif options.match_entire_word >> c.mword:
            finditer = regexfind
            ftext = u"\\b" + re.escape(ftext) + u"\\b"
        else:
            finditer = simplefind
        range = NSMakeRange(sel.location, 0)
        items = []
        rng = None
        tv.string() >> u"<text>"
        FoundRange = make_found_range_factory(
            FindOptions(regular_expression=c.regex, match_entire_word=c.mword))
        for i, r in enumerate(c.matches):
            if r is mod.WRAPTOKEN:
                items.append(r)
                continue
            found = FoundRange(NSMakeRange(*r))
            items.append(found)
            if i == 0 and found.range == sel:
                continue
            tv._Finder__recently_found_range = found
            rng = found.range
        finditer(u"<text>", ftext, range, direction, True) >> items
        with m:
            result = fc.finder._find(tv, u"<find>", sel, direction)
            eq_(result, rng)
    c = TestConfig(regex=False, mword=False, matches=[])
    yield test, c
    yield test, c(regex=True)
    yield test, c(mword=True)
    yield test, c(matches=[(2, 2)])
    # test with WRAPTOKEN
    yield test, c(matches=[mod.WRAPTOKEN])
    yield test, c(matches=[mod.WRAPTOKEN, (1, 2)])
    # test with first match being same as selection
    yield test, c(matches=[(1, 2)])
    yield test, c(matches=[(1, 2), (2, 2)])

def test_FindController__replace_all():
    def test(c):
        m = Mocker()
        fc = FindController.shared_controller()
        beep = m.replace(mod, 'NSBeep')
        dobeep = True
        tv = m.replace(fc.finder, 'find_target')() >> (m.mock(TextView) if c.has_tv else None)
        options = m.replace(fc.finder, "options")
        ftext = options.find_text >> c.ftext
        range = (tv.selectedRange() >> NSRange(*c.sel)) if c.has_tv else None
        if c.has_tv and c.ftext and ((c.sel_only and c.sel[1] > 0) or not c.sel_only):
            text = tv.string() >> c.text
            if not c.sel_only:
                if (options.wrap_around >> c.wrap):
                    range = NSMakeRange(0, 0)
                else:
                    range = NSMakeRange(range[0], len(text) - range[0])
            if options.regular_expression >> c.regex:
                finditer = m.method(fc.finder.regexfinditer)
            elif options.match_entire_word >> c.mword:
                ftext = u"\\b" + re.escape(ftext) + u"\\b"
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
            for r in c.ranges:
                found = FoundRange(NSMakeRange(*r))
                if ranges:
                    rtexts.append(text[sum(ranges[-1]):r[0]])
                ranges.append(found.range)
                rtexts.append(rtext)
                items.append(found)
            finditer(text, ftext, range, FORWARD, False) >> items
            if ranges:
                start = c.ranges[0][0]
                range = NSMakeRange(start, sum(c.ranges[-1]) - start)
                value = "".join(rtexts)
                if tv.shouldChangeTextInRange_replacementString_(range, value) >> c.replace:
                    ts = tv.textStorage() >> m.mock(NSTextStorage)
                    ts.replaceCharactersInRange_withString_(range, value)
                    tv.didChangeText()
                    tv.setNeedsDisplay_(True)
                    dobeep = False
        eq_(dobeep, c.beep)
        if dobeep:
            beep()
        with m:
            fc.finder._replace_all(c.sel_only)
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
        m = Mocker()
        beep = m.replace(mod, 'NSBeep')
        fc = FindController.shared_controller()
        flash = m.method(fc.flash_status_text)
        mark = m.method(fc.finder.mark_occurrences)
        tv = m.method(fc.find_target)() >> (m.mock(TextView) if c.has_tv else None)
        if c.has_tv:
            ftext = u"<find>"
            mark(ftext, c.regex) >> c.cnt
            if c.cnt:
                flash("%i occurrences" % c.cnt)
            else:
                flash("Not found")
        else:
            beep()
        with m:
            fc.count_occurrences(u"<find>", c.regex)
    c = TestConfig(has_tv=True, regex=False, cnt=0)
    yield test, c
    yield test, c(regex=True)
    yield test, c(cnt=42)
    yield test, c(has_tv=False)

def test_FindController_find_target():
    from editxt.editor import Editor
    from editxt.document import TextDocumentView
    def test(c):
        m = Mocker()
        fc = FindController.shared_controller()
        app = m.replace(editxt, "app")
        x = expect(app.iter_editors().next())
        if c.has_ed:
            ed = m.mock(Editor)
            x.result(ed)
            dv = ed.current_view >> (m.mock(TextDocumentView) if c.has_dv else None)
            if c.has_dv:
                dv.text_view >> (m.mock(TextView) if c.has_tv else None)
        else:
            x.throw(StopIteration)
        with m:
            result = fc.find_target()
            if c.has_ed and c.has_tv:
                assert result is not None
            else:
                eq_(result, None)
    c = TestConfig(has_ed=False, has_dv=True, has_tv=False)
    yield test, c
    yield test, c(has_ed=True)
    yield test, c(has_ed=True, has_dv=True)
    yield test, c(has_ed=True, has_dv=True, has_tv=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Test FindOptions

# def test_FindOptions_defaults():
#   options = FindOptions(FindController)
#   for name, value in options.defaults.iteritems():
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
        nspb = m.replace(mod, 'NSPasteboard')
        pboard = nspb.pasteboardWithName_(NSFindPboard)
        pboard.availableTypeFromArray_([NSStringPboardType]) >> (c.ftext is not None)
        if c.ftext is not None:
            pboard.stringForType_(NSStringPboardType) >> c.ftext
        with replace_history() as history:
            if c.hist is not None:
                history.append(c.hist)
            with m:
                fc = FindController() # calls load_options()
                eq_(fc.options._target, FindOptions(**c.opts))
                eq_(fc.options.recent_finds, [] if c.hist is None else [c.hist])
    o = dict
    c = TestConfig(ftext=None, hist=None, opts={})
    yield test, c
    yield test, c(ftext=u"", hist="/abc", opts=o(find_text=u""))
    yield test, c(ftext=u"def", hist="/abc", opts=o(find_text=u"def"))
    yield test, c(hist="/")
    yield test, c(hist="/abc", opts=o(find_text=u"abc"))
    yield test, c(hist="//repl", opts=o(replace_text=u"repl"))
    yield test, c(hist="/abc//i find-previous literal no-wrap",
                    opts=o(
                        find_text=u"abc",
                        action="find_previous",
                        ignore_case=True,
                        search_type=mod.LITERAL,
                        wrap_around=False,
                    ))

def test_FindController_save_options():
    def test(c):
        m = Mocker()
        with replace_history() as history:
            fc = FindController() # calls load_options()
            fc.options.find_text = u"" # clear value from real pasteboard
            fc.options.ignore_case = False
            nspb = m.replace(mod, 'NSPasteboard')
            if "find_text" in c.opts:
                pboard = nspb.pasteboardWithName_(NSFindPboard)
                pboard.declareTypes_owner_([NSStringPboardType], None)
                pboard.setString_forType_(c.opts["find_text"], NSStringPboardType)
            with m:
                for k, v in c.opts.items():
                    setattr(fc.options, k, v)
                print fc.options._target
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
