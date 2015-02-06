# -*- coding: utf-8 -*-
# EditXT
# Copyright 2007-2015 Daniel Miller <millerdev@gmail.com>
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
import AppKit as ak

from editxt.command.util import iterlines

class Text(object):

    def __init__(self, value=""):
        self.store = ak.NSTextStorage.alloc() \
            .initWithString_attributes_(value, {})
        self._delegate = TextStorageDelegate.alloc().init_(self.store)

    def on_edit(self, callback):
        return self._delegate.register_edit_callback(callback)

    def __getattr__(self, name):
        return getattr(self.store, name)

    def __getitem__(self, index):
        """Get a string for the given index or slice"""
        return self.store.string()[index]

    def __setitem__(self, index, value):
        if not isinstance(index, slice) or index.step is not None:
            raise NotImplementedError
        length = len(self)
        start = min(0 if index.start is None else index.start, length)
        if start < 0:
            start = convert_negative_index(start, length, 0)
        stop = min(length if index.stop is None else index.stop, length)
        if stop < 0:
            stop = convert_negative_index(stop, length, 0)
        if start > stop:
            raise ValueError(index)
        range_ = (start, stop - start)
        self.store.replaceCharactersInRange_withString_(range_, value)

    def __len__(self):
        return self.store.length()

    def __str__(self):
        return self.store.string()

    def __repr__(self):
        return repr(self.store.string())

    def iterlines(self, start=0, stop=None):
        """Generate lines of text"""
        range_ = (start,) if stop is None else (start, stop)
        return iterlines(self.string(), range_)


def convert_negative_index(index, length, underflow=None):
    if index >= 0:
        raise ValueError("expected negative index")
    value = length + index
    if value < 0:
        if underflow is None:
            raise IndexError(index)
        value = underflow
    return value


class TextStorageDelegate(ak.NSObject):

    def init_(self, target):
        target.setDelegate_(self)
        self.target = target
        self.callbacks = set()
        return self

    def register_edit_callback(self, callback):
        self.callbacks.add(callback)
        return lambda: self.callbacks.discard(callback)

    def dealloc(self):
        target, self.target = self.target, None
        if target is not None:
            target.setDelegate_(None)
        self.callbacks = None

    def textStorageDidProcessEditing_(self, notification):
        store = notification.object()
        for callback in list(self.callbacks):
            callback(store.editedRange())
