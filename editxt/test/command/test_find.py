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
from editxt.test.util import TestConfig, untested, check_app_state, replattr

import editxt
import editxt.constants as const
import editxt.command.find as mod
from editxt.command.find import Finder, FindController, FindOptions, FoundRange
from editxt.command.find import FORWARD, BACKWARD
from editxt.controls.textview import TextView
from editxt.test.command.test_base import replace_history

log = logging.getLogger(__name__)

# log.debug("""TODO
#     implement TextDocumentView.pasteboard_data()
# """)

def test_find_command():
    def test(c):
        assert int(c.regex) + int(c.match_word) < 2, c
        options = FindOptions(**{opt: c[key] for key, opt in {
            "find": "find_text",
            "replace": "replace_text",
            "regex": "regular_expression",
            "ignore_case": "ignore_case",
            "match_word": "match_entire_word",
            "wrap": "wrap_around",
        }.items()})
        m = Mocker()
        tv = m.mock(NSTextView)
        finder_cls = m.replace("editxt.command.find.Finder")
        def check_options(get_tv, args):
            eq_(get_tv(), tv)
            eq_(args, options)
        finder = m.mock(Finder)
        (finder_cls(ANY, ANY) << finder).call(check_options)
        getattr(finder, c.action)("<sender>")
        with m:
            args = mod.find.arg_parser.parse(c.input)
            mod.find(tv, "<sender>", args)

    c = TestConfig(find="", replace="", regex=True, ignore_case=False,
                   match_word=False, wrap=True, action="find_next")
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
    yield test, c(input=u"/abc//  r", find="abc", regex=True)
    yield test, c(input=u"/abc//  l", find="abc", regex=False, match_word=False)
    yield test, c(input=u"/abc//  w", find="abc", regex=False, match_word=True)
    yield test, c(input=u"/abc//   n", find="abc", wrap=False)

def test_Finder_mark_occurrences():
    def test(c):
        text = "the text is made of many texts"
        m = Mocker()
        tv = m.mock(TextView)
        tv._Finder__last_mark >> (None, 0)
        tv._Finder__last_mark = (c.options.find_text, c.count)
        tv.setNeedsDisplay_(True) # HACK
        ts = tv.textStorage() >> m.mock(NSTextStorage)
        app = m.replace(editxt, "app")
        app.config["highlight_selected_text.color"] >> "<color>"
        full_range = NSMakeRange(0, ts.length() >> len(text))
        ts.beginEditing()
        ts.removeAttribute_range_(NSBackgroundColorAttributeName, full_range)
        find_target = lambda: tv
        finder = Finder(find_target, c.options)
        if c.options.find_text:
            text = NSString.alloc().initWithString_(text)
            (tv.string() << text).count(1, None)
            mark_range = ts.addAttribute_value_range_ >> m.mock()
            mark = mark_range(NSBackgroundColorAttributeName, ANY, ANY)
            expect(mark).count(c.count)
        ts.endEditing()
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
    m.property(fc, "options")
    m.property(fc, "find_text")
    #fc.options.load()
    m.method(fc.gui.showWindow_)(fc)
    #fc.find_text.setStringValue_(fc.options.find_text >> "abc")
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
            rfr = FoundRange(None) if c.rfr else None
            if c.regex:
                (m.property(fc.finder, "recently_found_range").value << rfr).count(1,2)
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
        text = sender.selectedItem().title() >> "<value>"
        prop = m.property(fc, "options").value >> m.mock()
        setattr(prop, c.prop, text)
    yield test, c(meth="recentFindSelected_", do=do, prop="find_text")
    yield test, c(meth="recentReplaceSelected_", do=do, prop="replace_text")

    def do(m, c, fc, sender):
        ws = m.replace(mod, 'NSWorkspace')
        url = NSURL.URLWithString_(const.REGEX_HELP_URL)
        (ws.sharedWorkspace() >> m.mock(NSWorkspace)).openURL_(url)
    yield test, c(meth="regexHelp_", do=do)

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
            text = tv.string() >> "<text>"
            sel = tv.selectedRange() >> (1, 2)
            range = _find(text, c.ftext, sel, direction) >> ("<range>" if c.found else None)
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
        regexfind = m.method(fc.finder.regexfinditer)
        simplefind = m.method(fc.finder.simplefinditer)
        rfr = m.property(fc.finder, "recently_found_range")
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
        for i, r in enumerate(c.matches):
            if r is mod.WRAPTOKEN:
                items.append(r)
                continue
            found = FoundRange(NSMakeRange(*r))
            items.append(found)
            if i == 0 and found.range == sel:
                continue
            rfr.value = found
            rng = found.range
        finditer(u"<text>", ftext, range, direction, True) >> items
        with m:
            result = fc.finder._find(u"<text>", u"<find>", sel, direction)
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
    def test(c):
        options = FindOptions()
        setattr(options, c.att.name, c.att.before)
        setattr(options, c.dep.name, c.dep.before)
        eq_(getattr(options, c.att.name), c.att.before)
        eq_(getattr(options, c.dep.name), c.dep.before)
        # make the change, which fires the dependent change
        setattr(options, c.att.name, c.att.after)
        eq_(getattr(options, c.dep.name), c.dep.after)
    p = lambda n,b,a: TestConfig(name=n, before=b, after=a)
    c = TestConfig()
    yield test, c(att=p("regular_expression", False, True), dep=p("match_entire_word", True, False))
    yield test, c(att=p("regular_expression", True, False), dep=p("match_entire_word", False, False))
    yield test, c(att=p("match_entire_word", False, True), dep=p("regular_expression", True, False))
    yield test, c(att=p("match_entire_word", True, False), dep=p("regular_expression", False, False))

def test_FindController_load_options():
#    def test(c):
#        m = Mocker()
#        nspb = m.replace(mod, 'NSPasteboard')
#        pboard = nspb.pasteboardWithName_(NSFindPboard)
#        pboard.availableTypeFromArray_([NSStringPboardType]) >> c.has_ftext
#        if c.has_ftext:
#            pboard.stringForType_(NSStringPboardType) >> c.ftext
#        with replace_history() as history:
#            if c.state:
#                options = FindOptions(**c.state)
#                history.append(
#                    FindController.COMMAND.name,
#                    FindController.COMMAND.arg_parser.arg_string(options))
#            with m:
#                fc = FindController() # calls load_options()
#                options = fc.options
#                if c.state is not None:
#                    for k, v in FindOptions():
#                        eq_(getattr(options, k), c.state.get(k, v), k)
#                assert isinstance(options.recent_finds, NSMutableArray)
#                assert isinstance(options.recent_replaces, NSMutableArray)
#                if c.has_ftext:
#                    eq_(options.find_text, c.ftext)
#                else:
#                    eq_(options.find_text, u"")
    def test(c):
        m = Mocker()
        nsud = m.replace('editxt.command.find.NSUserDefaults')
        nspb = m.replace(mod, 'NSPasteboard')
        defaults = nsud.standardUserDefaults() >> m.mock(NSUserDefaults)
        defaults.dictionaryForKey_(const.FIND_PANEL_OPTIONS_KEY) >> c.state
        pboard = nspb.pasteboardWithName_(NSFindPboard)
        pboard.availableTypeFromArray_([NSStringPboardType]) >> c.has_ftext
        if c.has_ftext:
            pboard.stringForType_(NSStringPboardType) >> c.ftext
        with m, replace_history() as history:
            fc = FindController() # calls load_options()
            options = fc.options
            if c.state is not None:
                for k, v in FindOptions():
                    eq_(getattr(options, k), c.state.get(k, v), k)
            assert isinstance(options.recent_finds, NSMutableArray)
            assert isinstance(options.recent_replaces, NSMutableArray)
            if c.has_ftext:
                eq_(options.find_text, c.ftext)
            else:
                eq_(options.find_text, u"")
    c = TestConfig(state=None, has_ftext=False)
    d = dict
    yield test, c
    yield test, c(has_ftext=True, ftext=u"")
    yield test, c(has_ftext=True, ftext=u"abc")
    yield test, c(state={})
    yield test, c(state=d(replace_text=u"repl"))
    yield test, c(state=d(replace_text=u"repl", wrap_around=False))
    yield test, c(state=d(recent_finds=[u"find"]))
    yield test, c(state=d(recent_replaces=[u"repl"]))

def test_FindController_save_options():
    def test(c):
        m = Mocker()
        fc = FindController()
        options = FindOptions()
        options.find_text = c.astate.get("find_text", u"")
        nsud = m.replace('editxt.command.base.NSUserDefaults')
        nspb = m.replace(mod, 'NSPasteboard')
        if "find_text" in c.astate:
            pboard = nspb.pasteboardWithName_(NSFindPboard)
            pboard.declareTypes_owner_([NSStringPboardType], None)
            pboard.setString_forType_(c.astate["find_text"], NSStringPboardType)
        zstate = {}
        for k, v in FindOptions():
            setattr(options, k, c.astate.get(k, v))
            zstate[k] = c.zstate.get(k, v)
        defaults = nsud.standardUserDefaults() >> m.mock(NSUserDefaults)
        def do(state, key):
            eq_(state, zstate)
            return True
        expect(defaults.setObject_forKey_(ANY, const.FIND_PANEL_OPTIONS_KEY)).call(do)
        with m, replattr(fc, "options", options):
            fc.save_options()
    c = TestConfig(astate={}, zstate={}, has_ftext=False)
    d = dict
    yield test, c
    yield test, c(astate=d(find_text="abc"), zstate=d(find_text="abc", recent_finds=["abc"]))
    yield test, c(astate=d(replace_text="abc"), zstate=d(replace_text="abc", recent_replaces=["abc"]))
    yield test, c(astate=d(find_text="abc", recent_finds=list("abcdefghij")), zstate=d(
        find_text="abc",
        recent_finds=["abc"] + list("abcdefghi"),
    ))


# def test():
#     assert False, "stop"
