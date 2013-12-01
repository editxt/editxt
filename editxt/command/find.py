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
from editxt.command.base import command, CommandError, objc_delegate, PanelController
from editxt.command.parser import Choice, Regex, RegexPattern, CommandParser, Options
from editxt.command.util import make_command_predicate
from editxt.datatypes import WeakProperty
from editxt.platform.kvo import KVOProxy, KVOLink

log = logging.getLogger(__name__)


ACTION_FIND_SELECTED_TEXT = 101
ACTION_FIND_SELECTED_TEXT_REVERSE = 102

SELECTION_REQUIRED_ACTIONS = set([
    ACTION_FIND_SELECTED_TEXT,
    ACTION_FIND_SELECTED_TEXT_REVERSE,
])

FORWARD = "FORWARD"
BACKWARD = "BACKWARD"
WRAPTOKEN = "WRAPTOKEN"

REGEX = "regex"
REPY = "python-replace"
LITERAL = "literal"
WORD = "word"

@command(arg_parser=CommandParser(
    Regex('pattern', replace=True, default=(RegexPattern(), "")),
    Choice(('find-next next', 'find_next'),
        ('find-previous previous', 'find_previous'),
        ('replace-one one', 'replace_one'),
        ('replace-all all', 'replace_all'),
        ('replace-in-selection in-selection selection', 'replace_all_in_selection'),
        ('count-occurrences highlight', 'count_occurrences'),
        name='action'),
    Choice('regex literal word python-replace', name='search_type'),
    Choice(('wrap', True), ('no-wrap', False), name='wrap_around'),
), lookup_with_arg_parser=True)
def find(textview, sender, args):
    assert args is not None, sender
    opts = FindOptions(**args.__dict__)
    save_to_find_pasteboard(opts.find_text)
    finder = Finder(lambda:textview, opts, textview.app)
    return getattr(finder, args.action)(sender)


def toggle_boolean(depname):
    def make_property(func):
        name = func.__name__
        def fget(self):
            try:
                return self.__dict__[name]
            except KeyError:
                raise AttributeError(name)
        def fset(self, value):
            self.__dict__[name] = value
            if value:
                self.__dict__[depname] = False
        return property(fget, fset)
    return make_property


class FindOptions(Options):

    DEFAULTS = dict(
        pattern = (RegexPattern(), ""),
        action = 'find_next',
        search_type = REGEX,
        wrap_around = True,
    )
    app = WeakProperty()

    dependent_key_paths = {
        "match_entire_word": ["regular_expression", "search_type", "python_replace"],
        "regular_expression": ["match_entire_word", "search_type", "python_replace"],
        "python_replace": ["match_entire_word", "search_type", "regular_expression"],
        "search_type": ["match_entire_word", "regular_expression", "python_replace"],
        "pattern": ["find_text", "replace_text", "ignore_case"],
        "find_text": ["pattern"],
        "replace_text": ["pattern"],
        "ignore_case": ["pattern"],
    }

    @property
    def find_text(self):
        return self.pattern[0]
    @find_text.setter
    def find_text(self, value):
        value = RegexPattern(value, self.pattern[0].flags)
        self.pattern = (value, self.pattern[1])

    @property
    def replace_text(self):
        return self.pattern[1]
    @replace_text.setter
    def replace_text(self, value):
        self.pattern = (self.pattern[0], value or "")

    @property
    def ignore_case(self):
        return self.pattern[0].flags & re.IGNORECASE
    @ignore_case.setter
    def ignore_case(self, value):
        if value and not self.pattern[0].flags & re.IGNORECASE:
            find = self.pattern[0]
            find = RegexPattern(find, find.flags | re.IGNORECASE)
            self.pattern = (find, self.pattern[1])
        elif not value and self.pattern[0].flags & re.IGNORECASE:
            find = self.pattern[0]
            find = RegexPattern(find, find.flags ^ re.IGNORECASE)
            self.pattern = (find, self.pattern[1])

    @property
    def regular_expression(self):
        return self.search_type == REGEX or self.search_type == REPY
    @regular_expression.setter
    def regular_expression(self, value):
        assert isinstance(value, (int, bool)), value
        if value:
            if self.search_type != REPY:
                self.search_type = REGEX
        elif self.search_type != WORD:
            self.search_type = LITERAL

    @property
    def match_entire_word(self):
        return self.search_type == WORD
    @match_entire_word.setter
    def match_entire_word(self, value):
        assert isinstance(value, (int, bool)), value
        if value or not self.regular_expression:
            self.search_type = WORD if value else LITERAL

    @property
    def python_replace(self):
        return self.search_type == REPY
    @python_replace.setter
    def python_replace(self, value):
        assert isinstance(value, (int, bool)), value
        if value:
            self.search_type = REPY
        elif self.search_type == REPY:
            self.search_type = REGEX

    @property
    def recent_finds(self):
        predicate = make_command_predicate(find)
        items = self.app.text_commander.history.iter_matching(predicate)
        result = []
        for i, item in enumerate(items):
            if i < 10:
                result.append(item)
            else:
                break
        return result

    @property
    def recent_replaces(self):
        # DEPRECATED here so nib file can still bind
        return []


class Finder(object):

    app = WeakProperty()

    def __init__(self, find_target, options, app):
        self.find_target = find_target
        self.options = options
        self.options.app = app
        self.app = app

    def find_next(self, sender):
        self.find(FORWARD)

    def find_previous(self, sender):
        self.find(BACKWARD)

    def replace_one(self, sender):
        target = self.find_target()
        if target is not None:
            options = self.options
            rtext = options.replace_text
            if options.regular_expression:
                found = getattr(target, "_Finder__recently_found_range", None)
                if found is not None:
                    rtext = found.expand(rtext)
            range = target.selectedRange()
            if target.shouldChangeTextInRange_replacementString_(range, rtext):
                target.textStorage().replaceCharactersInRange_withString_(range, rtext)
                target.didChangeText()
                target.setNeedsDisplay_(True)
                return
        ak.NSBeep()

    def replace_all(self, sender):
        self._replace_all()

    def replace_all_in_selection(self, sender):
        self._replace_all(in_selection=True)

    def count_occurrences(self, sender):
        num = self.mark_occurrences(
            self.options.find_text, self.options.regular_expression)
        return "Found {} occurrence{}".format(num, ("" if num == 1 else "s"))

    def mark_occurrences(self, ftext, regex=False, color=None):
        """Mark occurrences of ftext in target

        This method always clears all existing text marks, and marks
        nothing if the given `ftext` is an empty string.

        :ftext: A string of text to find/mark.
        :regex: Boolean value indicating if ftext is a regular expression.
        :color: Color used to mark ranges. Yellow (#FEFF6B) by default.
        :returns: Number of marked occurrences.
        """
        target = self.find_target()
        last_mark = getattr(target, '_Finder__last_mark', (None, 0))
        if last_mark[0] == ftext:
            return last_mark[1]
        if color is None:
            color = self.app.config["highlight_selected_text.color"]
        layout = target.layoutManager()
        full_range = fn.NSMakeRange(0, target.textStorage().length())
        layout.removeTemporaryAttribute_forCharacterRange_(
            ak.NSBackgroundColorAttributeName, full_range)
        if not ftext:
            target._Finder__last_mark = (ftext, 0)
            return 0
        text = target.string()
        options = self.options
        original_ftext = ftext
        if regex and options.regular_expression:
            finditer = self.regexfinditer
        elif options.match_entire_word:
            ftext = "\\b" + re.escape(ftext) + "\\b"
            finditer = self.regexfinditer
        else:
            finditer = self.simplefinditer
        count = 0
        attr = ak.NSBackgroundColorAttributeName
        mark_range = layout.addTemporaryAttribute_value_forCharacterRange_
        for found in finditer(text, ftext, full_range, FORWARD, False):
            mark_range(attr, color, found.range)
            count += 1
        target._Finder__last_mark = (original_ftext, count)
        return count

    def find(self, direction):
        target = self.find_target()
        ftext = self.options.find_text
        if target is not None and ftext:
            selection = target.selectedRange()
            range = self._find(target, ftext, selection, direction)
            if range is not None:
                target.setSelectedRange_(range)
                target.scrollRangeToVisible_(range)
                return
        ak.NSBeep()

    def _find(self, target, ftext, selection, direction):
        """Return the range of the found text or None if not found"""
        options = self.options
        if options.regular_expression:
            finditer = self.regexfinditer
        elif options.match_entire_word:
            ftext = "\\b" + re.escape(ftext) + "\\b"
            finditer = self.regexfinditer
        else:
            finditer = self.simplefinditer
        text = target.string()
        range = fn.NSMakeRange(selection.location, 0)
        for i, found in enumerate(finditer(text, ftext, range, direction, True)):
            if found is WRAPTOKEN:
                # TODO show wrap overlay
                continue
            range = found.range
            if i == 0 and range == selection:
                # this is the first match and we found the selected text
                continue # find next
            target.__recently_found_range = found
            return range
        return None

    def _replace_all(self, in_selection=False):
        target = self.find_target()
        ftext = self.options.find_text
        range = None if target is None else target.selectedRange()
        if target is None or not ftext or (in_selection and range.length == 0):
            ak.NSBeep()
            return
        text = target.string()
        options = self.options
        if not in_selection:
            if options.wrap_around:
                range = fn.NSMakeRange(0, 0)
            else:
                # Replace all to the end of the file. Logically there should be
                # another option: replace all (backward) to the beginning of the
                # file, but there's no way to do that with the interface.
                range = fn.NSMakeRange(range.location, len(text) - range.location)
        if options.regular_expression:
            finditer = self.regexfinditer
        elif options.match_entire_word:
            ftext = "\\b" + re.escape(ftext) + "\\b"
            finditer = self.regexfinditer
        else:
            finditer = self.simplefinditer
        rtext = options.replace_text
        range0 = None
        rtexts = []
        for found in finditer(text, ftext, range, FORWARD, False):
            range = found.range
            if range0 is None:
                range0 = range
            else:
                rtexts.append(text[sum(range1):range.location])
            range1 = range
            rtexts.append(found.expand(rtext))
        if range0 is not None:
            start = range0.location
            range = fn.NSMakeRange(start, sum(range1) - start)
            value = "".join(rtexts)
            if target.shouldChangeTextInRange_replacementString_(range, value):
                target.textStorage().replaceCharactersInRange_withString_(range, value)
                target.didChangeText()
                target.setNeedsDisplay_(True)
                return
        ak.NSBeep()

    def simplefinditer(self, text, ftext, range,
                       direction=FORWARD, yield_on_wrap=True):
        """Yields FoundRanges of text that match ftext

        if yield_on_wrap evaluates to True and wrap_around search option is set
        then WRAPTOKEN is yielded when the search wraps around the beginning/end
        of the file
        """
        opts = 0
        options = self.options
        if options.ignore_case:
            opts |= fn.NSCaseInsensitiveSearch
        forwardSearch = (direction == FORWARD)
        if forwardSearch:
            startindex = index = range.location
        else:
            startindex = index = range.location + range.length
            opts |= fn.NSBackwardsSearch
        if range.length == 0:
            if options.wrap_around:
                range = fn.NSMakeRange(0, text.length())
            elif forwardSearch:
                range = fn.NSMakeRange(startindex, text.length() - startindex)
            else:
                range = fn.NSMakeRange(0, startindex)
        endindex = range.location + range.length
        FoundRange = make_found_range_factory(options)
        wrapped = False
        while True:
            if forwardSearch:
                if wrapped:
                    if index >= startindex:
                        break # searched to or beyond where we started
                    else:
                        frange = fn.NSRange(index, startindex - index)
                else:
                    frange = fn.NSRange(index, endindex - index)
            else:
                if wrapped:
                    if index <= startindex:
                        break # searched to or beyond where we started
                    else:
                        frange = fn.NSRange(startindex, index - startindex)
                else:
                    frange = fn.NSRange(range.location, index - range.location)
            found = text.rangeOfString_options_range_(ftext, opts, frange)
            if found and found.length > 0 and found.location < endindex:
                yield FoundRange(found)
                index = found.location + (found.length if forwardSearch else 0)
            elif options.wrap_around and not wrapped:
                if yield_on_wrap:
                    yield WRAPTOKEN
                index = range.location if forwardSearch else endindex
                wrapped = True
            else:
                break

    def regexfinditer(self, text, ftext, range, direction, yield_on_wrap):
        """Yields FoundRanges of text matched by ftext (a regular expression)

        if yield_on_wrap evaluates to True and wrapAround search option is set
        then WRAPTOKEN is yielded when the search wraps around the beginning/end
        of the file.
        """
        flags = re.UNICODE | re.MULTILINE
        options = self.options
        if options.ignore_case:
            flags |= re.IGNORECASE
        try:
            regex = re.compile(ftext, flags)
        except re.error as err:
            ak.NSBeep()
            log.error("cannot compile regex %r : %s", ftext, err)
        else:
            FoundRange = make_found_range_factory(options)
            backward = (direction == BACKWARD)
            wrapped = False
            endindex = range.location + range.length
            while True:
                if range.length > 0:
                    itr = regex.finditer(text, range.location, endindex)
                elif (wrapped and backward) or (not wrapped and not backward):
                    itr = regex.finditer(text, range.location)
                else:
                    itr = regex.finditer(text, 0, range.location)
                if backward:
                    itr = reversed(list(itr))
                for match in itr:
                    s = match.start()
                    e = match.end()
                    #log.debug("searching for %r found %r at (%s, %s)", ftext, match.group(), s, e)
                    yield FoundRange(fn.NSMakeRange(s, e - s), match)
                if options.wrap_around and not wrapped and range.length == 0:
                    if yield_on_wrap:
                        yield WRAPTOKEN
                    wrapped = True
                else:
                    break


class FindController(PanelController):
    """Window controller for find panel"""

    COMMAND = find
    NIB_NAME = "FindPanel"
    OPTIONS_KEY = const.FIND_PANEL_OPTIONS_KEY
    OPTIONS_FACTORY = FindOptions

    @classmethod
    def controller_class(cls):
        return super(FindController, cls).controller_class(
            find_text=objc.IBOutlet(),
            replace_text=objc.IBOutlet(),
            status_label=objc.IBOutlet(),
        )

    def __init__(self, app):
        super(FindController, self).__init__(app)
        self.finder = Finder(self.find_target, self.options, app)
        self.action_registry = {
            ak.NSFindPanelActionShowFindPanel: self.show_find_panel,
            ak.NSFindPanelActionNext: self.find_next,
            ak.NSFindPanelActionPrevious: self.find_previous,
            ak.NSFindPanelActionReplace: self.replace_one,
            ak.NSFindPanelActionReplaceAll: self.replace_all,
            ak.NSFindPanelActionReplaceAndFind: self.replace_and_find_next,
            ak.NSFindPanelActionReplaceAllInSelection: self.replace_all_in_selection,
            ak.NSFindPanelActionSetFindString: self.set_find_text_with_selection,
            ACTION_FIND_SELECTED_TEXT: self.find_selected_text,
            ACTION_FIND_SELECTED_TEXT_REVERSE: self.find_selected_text_reverse,
        }

    @objc_delegate
    def windowDidLoad(self):
        self.gui.window().setLevel_(ak.NSFloatingWindowLevel)
        target = self.find_target()
        if target is not None:
            font = target.doc_view.document.default_text_attributes()[ak.NSFontAttributeName]
            self.gui.find_text.setFont_(font)
            self.gui.replace_text.setFont_(font)

    @property
    def find_text(self):
        return self.gui.find_text

    # Menu actions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def validate_action(self, tag):
        if tag in self.action_registry:
            target = self.find_target()
            if target is not None:
                if tag in SELECTION_REQUIRED_ACTIONS:
                    return target.selectedRange().length > 0
                return True
        return False

    def perform_action(self, sender):
        default = lambda s: log.info("unknown action: %s", s.tag())
        self.action_registry.get(sender.tag(), default)(sender)

    def show_find_panel(self, sender):
        self.options.willChangeValueForKey_("recent_finds") # HACK
        self.load_options() # restore state
        self.options.didChangeValueForKey_("recent_finds") # HACK force reload
        self.gui.showWindow_(self)
        self.find_text.selectText_(sender)

    def find_next(self, sender):
        return self.finder.find_next(sender)

    def find_previous(self, sender):
        return self.finder.find_previous(sender)

    def replace_one(self, sender):
        return self.finder.replace_one(sender)

    def replace_all(self, sender):
        return self.finder.replace_all(sender)

    def replace_all_in_selection(self, sender):
        return self.finder.replace_all_in_selection(sender)

    def find_selected_text(self, sender):
        self.set_find_text_with_selection(sender)
        if self.save_options():
            self.finder.find_next(sender)

    def find_selected_text_reverse(self, sender):
        self.set_find_text_with_selection(sender)
        if self.save_options():
            self.finder.find_previous(sender)

    def replace_and_find_next(self, sender):
        self.finder.replace_one(sender)
        self.finder.find_next(sender)

    def set_find_text_with_selection(self, sender):
        target = self.find_target()
        if target is not None:
            range = target.selectedRange()
            if range.length > 0:
                text = target.string().substringWithRange_(range)
                if self.options.regular_expression:
                    text = re.escape(text)
                self.options.find_text = text

    # Panel actions ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @objc_delegate
    def panelFindNext_(self, sender):
        if self.save_options():
            self.gui.window().orderOut_(sender)
            self.finder.find_next(sender)

    @objc_delegate
    def panelFindPrevious_(self, sender):
        if self.save_options():
            self.gui.window().orderOut_(sender)
            self.finder.find_previous(sender)

    @objc_delegate
    def panelReplace_(self, sender):
        if self.save_options():
            self.gui.window().orderOut_(sender)
            self.finder.replace_one(sender)

    @objc_delegate
    def panelReplaceAll_(self, sender):
        if self.save_options():
            self.gui.window().orderOut_(sender)
            self.finder.replace_all(sender)

    @objc_delegate
    def panelReplaceAllInSelection_(self, sender):
        if self.save_options():
            self.gui.window().orderOut_(sender)
            self.finder.replace_all_in_selection(sender)

    @objc_delegate
    def panelCountFindText_(self, sender):
        if self.validate_expression():
            self.count_occurrences(
                self.options.find_text, self.options.regular_expression)

    @objc_delegate
    def panelCountReplaceText_(self, sender):
        if self.validate_expression():
            self.count_occurrences(self.options.replace_text, False)

    @objc_delegate
    def panelMarkAll_(self, sender):
        if self.save_options():
            raise NotImplementedError()

    @objc_delegate
    def recentFindSelected_(self, sender):
        # TODO make this support undo so the change can be easily reverted
        argstr = sender.selectedItem().title()
        try:
            options = self.command.parse(argstr)
            for key, value in options:
                if key != "action":
                    setattr(self.options, key, value)
        except Exception:
            log.warn("cannot parse find command: %s", argstr, exc_info=True)

    @objc_delegate
    def recentReplaceSelected_(self, sender):
        # TODO make this support undo so the change can be easily reverted
        pass #self.options.replace_text = sender.selectedItem().title()

    @objc_delegate
    def regexHelp_(self, sender):
        # TODO possibly open a sheet with a short description of how regular
        # expressions are used here, including notes about the default flags
        # that are set (MULTILINE | UNICODE) and the syntax that should be used.
        url = fn.NSURL.URLWithString_(const.REGEX_HELP_URL)
        ak.NSWorkspace.sharedWorkspace().openURL_(url)

    # Utility methods ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def find_target(self):
        try:
            editor = next(self.app.iter_editors())
        except StopIteration:
            pass
        else:
            docview = editor.current_view
            if docview is not None:
                return docview.text_view
        return None

    def count_occurrences(self, ftext, regex):
        target = self.find_target()
        if target is not None and ftext:
            count = self.finder.mark_occurrences(ftext, regex)
            if count:
                self.flash_status_text("%i occurrences" % count)
            else:
                self.flash_status_text("Not found")
        else:
            ak.NSBeep()

    def flash_status_text(self, text):
        self.stop_flashing_status()
        self.status_flasher = StatusFlasher.alloc().init(self.gui.status_label, text)

    def stop_flashing_status(self):
        flasher = getattr(self, "status_flasher", None)
        if flasher is not None:
            flasher.stop()

    # Window delegate implementation ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    @objc_delegate
    def windowWillClose_(self, window):
        self.stop_flashing_status()

    # Find Options implementation ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    def validate_expression(self):
        if self.options.regular_expression and self.find_text is not None:
            ftext = self.find_text.stringValue()
            flags = re.UNICODE | re.MULTILINE
            if self.options.ignore_case:
                flags |= re.IGNORECASE
            error = None
            try:
                regex = re.compile(ftext, flags)
                if self.options.python_replace:
                    make_found_range_factory(self.options)
            except re.error as err:
                title = "Cannot Compile Regular Expression"
                error = err
            except InvalidPythonExpression as err:
                title = "Cannot Compile Python Expression"
                error = err
            if error:
                ak.NSBeep()
                # Note: if the find dialog type is NSPanel (instead of NSWindow)
                # the focus will switch back to the main document window rather
                # than to the find dialog, which is not what we want. Therefore
                # we set the Custom Class of the find dialog to NSWindow.
                ak.NSBeginAlertSheet(
                    title,
                    "OK", None, None,
                    self.gui.window(), None, None, None, 0,
                    str(err),
                );
                return False
        return True

    def load_options(self):
        super(FindController, self).load_options()
        text = load_find_pasteboard_string()
        if text is not None and self.options.find_text != text:
            self.options.find_text = text

    def save_options(self):
        options = self.options
        if not (options.find_text and self.validate_expression()):
            return False
        save_to_find_pasteboard(options.find_text)
        if len(options.find_text) < 1000 and len(options.replace_text) < 1000:
            super(FindController, self).save_options()
        return True


class StatusFlasher(fn.NSObject):

    timing = (0.2, 0.2, 0.2, 5)

    @objc.namedSelector(b"init:text:")
    def init(self, label, text):
        def runner():
            label.setHidden_(True)
            label.setStringValue_(text)
            for t in self.timing:
                 yield t
                 label.setHidden_(not label.isHidden())
            self.stop()
        self = super(StatusFlasher, self).init()
        self.label = label
        self.runner = runner()
        self.doEvent()
        return self

    def doEvent(self):
        if self.runner is not None:
            try:
                t = next(self.runner)
            except StopIteration:
                return
            self.performSelector_withObject_afterDelay_("doEvent", self, t)

    def stop(self):
        if self.runner is not None:
            self.label.setStringValue_("")
            self.label.setHidden_(False)
        self.runner = None


class BaseFoundRange(object):

    def __init__(self, range, match=None):
        self.range = range
        self.match = match


def make_found_range_factory(options):
    if options.search_type == REPY:
        func = "def repy(match, range_):\n    return {}" \
            .format(options.replace_text)
        namespace = {}
        try:
            exec(func, globals(), namespace)
        except Exception as err:
            raise InvalidPythonExpression(func, err)
        repy = namespace["repy"]
        def expand(self, text):
            match = Match(self.match)
            try:
                return repy(match, self.range)
            except Exception as err:
                return "!! {} >> {} >> {}: {} !!" \
                    .format(match, text, type(err).__name__, err)
    elif options.search_type == REGEX or options.search_type == WORD:
        def expand(self, text):
            try:
                return self.match.expand(text)
            except Exception as err:
                return "!! {} >> {} >> {}: {} !!" \
                    .format(Match(self.match), text, type(err).__name__, err)
    else:
        assert options.search_type == LITERAL, options
        def expand(self, text):
            return text
    return type("FoundRange", (BaseFoundRange,), {"expand": expand})


class Match(object):
    """re match object wrapper with support for getitem/slice

    >>> match = Match(re.search("(\d)(\d)(\d)(\d)(\d)", "12345"))
    >>> match
    <Match '12345'>
    >>> str(match)
    '12345'
    >>> match[0]
    '12345'
    >>> match[1]
    '1'
    >>> match[5]
    '5'
    >>> match[0:3]
    '123'
    >>> match[1:3]
    '23'
    >>> match[1::2]
    '24'
    >>> match[6]
    Traceback (most recent call last):
      ...
    IndexError: no such group
    """

    def __init__(self, match):
        self.match = match

    def __getattr__(self, name):
        return getattr(self.match, name)

    def __getitem__(self, key):
        if isinstance(key, slice):
            return "".join(self.match.groups()[key])
        return self.match.group(key)

    def __str__(self):
        try:
            return self.match.group(0)
        except Exception:
            return str(self.match)

    def __repr__(self):
        try:
            value = self.match.group(0)
        except Exception:
            value = self.match
        return "<{} {!r}>".format(type(self).__name__, value)


class InvalidPythonExpression(CommandError):

    def __init__(self, func, err):
        super(Exception, self).__init__(func, err)

    def __str__(self):
        return "could not compile:\n\n{}\n\n{}".format(*self.args[:2])


def load_find_pasteboard_string():
    """Get value of system ak.NSFindPboard if it is a string

    :returns: String if pasteboard contains a string, otherwise ``None``.
    """
    pboard = ak.NSPasteboard.pasteboardWithName_(ak.NSFindPboard)
    if pboard.availableTypeFromArray_([ak.NSStringPboardType]):
        return pboard.stringForType_(ak.NSStringPboardType)
    return None


def save_to_find_pasteboard(text):
    """Save the given text to the system ak.NSFindPboard"""
    pboard = ak.NSPasteboard.pasteboardWithName_(ak.NSFindPboard)
    pboard.declareTypes_owner_([ak.NSStringPboardType], None)
    pboard.setString_forType_(text, ak.NSStringPboardType)
