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
from os.path import exists, join

from editxt.util import WeakProperty

log = logging.getLogger(__name__)


class History(object):
    """A persistent ordered list of JSON-serializable items"""

    NAME = "history"
    INDEX_FILENAME = "{}-index.json"
    FILENAME_PATTERN = "{}-{}.txt"

    def __init__(self, store_dir, page_size=100, max_pages=10, name=NAME):
        self.store_dir = store_dir
        self.name = name
        self.page_size = page_size
        self.max_pages = max_pages
        self.pages = None
        self.zeropage = None
        self.zerofile = None
        self.views = set()

    def _initialize(self):
        self.pages = []
        index_file = join(self.store_dir, self.INDEX_FILENAME.format(self.name))
        if exists(index_file):
            try:
                with open(index_file) as fh:
                    self.pages = pages = json.load(fh)
                assert all(isinstance(p, str) for p in pages), \
                    repr(pages)
            except Exception:
                log.warn("cannot load %s", index_file, exc_info=True)
        if len(self.pages) < self.max_pages:
            for n in range(self.max_pages):
                filename = self.FILENAME_PATTERN.format(self.name, n)
                if filename not in self.pages:
                    self.pages.append(filename)
                if len(self.pages) == self.max_pages:
                    break
        elif len(self.pages) > self.max_pages:
            del self.pages[self.max_pages:]
        assert len(self.pages) == self.max_pages, repr(self.pages)
        self.zerofile = self.pages[0]
        self.zeropage = next(self.iter_pages(0))
        zeropath = join(self.store_dir, self.zerofile)
        if exists(zeropath) and not self.zeropage:
            with open(zeropath, "wb") as fh:
                pass # truncate corrupt page file

    def iter_pages(self, start=1):
        assert start > -1, start
        for pagefile in self.pages[start:]:
            pagepath = join(self.store_dir, pagefile)
            if exists(pagepath):
                page = []
                with open(pagepath) as fh:
                    for i, line in enumerate(fh):
                        try:
                            page.append(json.loads(line.rstrip("\n")))
                        except Exception as err:
                            log.warn("cannot load line %s in %s: %s",
                                     i + 1, pagepath, err)
                yield page
            else:
                yield []

    def __iter__(self):
        if self.zeropage is None:
            self._initialize()
        for item in reversed(self.zeropage):
            yield item
        for page in self.iter_pages():
            for item in reversed(page):
                yield item

    def iter_matching(self, predicate):
        """Iterate items matching predicate"""
        return filter(predicate, iter(self))

    def append(self, item):
        """Append an item to history

        This causes the history to be saved to disk. If item already
        exists in history it will be moved to the the most recent item,
        and the older item will be removed (this only applies to the
        first page of history).
        """
        if self.zeropage is None:
            self._initialize()
        zero = self.zeropage
        moved = None
        removed = []
        try:
            moved = zero.index(item)
        except ValueError:
            pass
        else:
            zero.remove(item)
            while True:
                try:
                    removed.append(zero.index(item))
                except ValueError:
                    break
                zero.remove(item)
        if moved is not None:
            for view in self.views:
                view.update(moved, removed)
            # rewrite entire file because an item was moved
            zero.append(item)
            zeropath = join(self.store_dir, self.zerofile)
            try:
                with open(zeropath, "wb") as fh:
                    for item in zero:
                        json.dump(item, fh)
                        fh.write("\n")
            except Exception:
                log.warn("cannot write to history: %s", zeropath, exc_info=True)
            assert len(zero) <= self.page_size, repr(zero)
            return
        if len(zero) < self.page_size:
            zero.append(item)
            mode = "ab"
        else:
            self.zeropage = zero = [item]
            self.zerofile = self.pages.pop()
            self.pages.insert(0, self.zerofile)
            index_name = self.INDEX_FILENAME.format(self.name)
            index_file = join(self.store_dir, index_name)
            try:
                with open(index_file, "wb") as fh:
                    json.dump(self.pages, fh)
            except Exception:
                log.warn("cannot write %s", index_file, exc_info=True)
            mode = "wb"
        for view in self.views:
            view.update()
        zeropath = join(self.store_dir, self.zerofile)
        try:
            with open(zeropath, mode) as fh:
                json.dump(item, fh)
                fh.write("\n")
        except Exception:
            log.warn("cannot write to history: %s", zeropath, exc_info=True)

    def __getitem__(self, index):
        """Get item by index

        :param index: Integer index of item in history.
        :returns: Command text or ``None`` if index does not reference a
        valid item in history.
        """
        if self.zeropage is None:
            self._initialize()
        zero = self.zeropage
        if index < len(zero):
            return zero[len(zero) - index - 1]
        index -= len(zero)
        for page in self.iter_pages():
            if index >= len(page):
                index -= len(page)
                continue
            return page[len(page) - index - 1]
        return None

    def __delitem__(self, index):
        """Remove item from history by index

        :param index: Integer index of item in history.
        """
        raise NotImplementedError

    def view(self):
        """Create and return a new view of this history object"""
        view = HistoryView(self)
        self.views.add(view)
        return view

    def discard_view(self, view):
        self.views.discard(view)


class HistoryView(object):
    """A history view that can be kept consistent when history is updated"""

    history = WeakProperty()

    def __init__(self, history):
        self.history = history
        self.history_index = -1
        self.history_edits = {}
        self.current_history = None

    def update(self, moved=None, removed=()):
        """Update this view's pointers to reflect a history change

        :param moved: Index of a item that was moved to front of history.
        :param removed: List of indices of items that were removed from
        history.
        """
        moved_edit = None
        if moved is None or self.history_index < moved:
            self.history_index += 1
        elif self.history_index == moved:
            self.history_index = 0
        if self.history_edits:
            moved_edit = self.history_edits.pop(moved, None)
            for index in sorted(self.history_edits, reverse=True):
                if index < 0:
                    continue
                if moved is None or index < moved:
                    self.history_edits[index + 1] = self.history_edits.pop(index)
            if moved_edit is not None:
                self.history_edits[0] = moved_edit
        if removed:
            raise NotImplementedError(removed)

    def get(self, current_item, forward=False):
        """Get next item in history

        :param current_item: Current history item (saved for later traversal).
        :param forward: Get older item if false (default) else newer.
        :returns: Text of next item in history.
        """
        last_index = self.history_index
        index = last_index + (-1 if forward else 1)
        if index < -1:
            return None
        if index == -1:
            text = self.history_edits.get(-1, "")
        else:
            text = self.history[index]
            if text is None:
                return None
        if last_index < 0 or current_item != self.current_history:
            self.history_edits[last_index] = current_item
        else:
            self.history_edits.pop(last_index, None)
        self.history_index = index
        self.current_history = text
        if index in self.history_edits:
            return self.history_edits[index]
        return text
