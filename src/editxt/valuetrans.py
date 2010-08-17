# -*- coding: utf-8 -*-
# EditXT
# Copywrite (c) 2007-2010 Daniel Miller <millerdev@gmail.com>
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
from AppKit import *
from Foundation import *

import editxt.constants as const

log = logging.getLogger("editxt.valuetrans")


class KeyValueTransformer(NSValueTransformer):

    @classmethod
    def transformedValueClass(cls):
        return int

    @classmethod
    def allowsReverseTransformation(cls):
        return True

    @objc.namedselector("init:")
    def init(self, map):
        self = super(KeyValueTransformer, self).init()
        self.forward = dict(map)
        self.reverse = dict((v, k) for k, v in self.forward.iteritems())
        assert len(self.forward.values()) == len(self.reverse.keys())
        return self

    def transformedValue_(self, value):
        return self.forward[value]

    def reverseTransformedValue_(self, value):
        return self.reverse[value]


class WrapModeTransformer(KeyValueTransformer):

    @classmethod
    def create(cls):
        return cls.alloc().init({
            None: None,
            const.LINE_WRAP_NONE: 0,
            const.LINE_WRAP_WORD: 1,
        })


class IndentModeTransformer(KeyValueTransformer):

    @classmethod
    def create(cls):
        return cls.alloc().init({
            None: None,
            const.INDENT_MODE_TAB: 0,
            const.INDENT_MODE_SPACE: 1,
        })


class NewlineModeTransformer(KeyValueTransformer):

    @classmethod
    def create(cls):
        return cls.alloc().init({
            None: None,
            const.NEWLINE_MODE_UNIX: 0,
            const.NEWLINE_MODE_MAC: 1,
            const.NEWLINE_MODE_WINDOWS: 2,
            const.NEWLINE_MODE_UNICODE: 3,
        })


class IntTransformer(NSValueTransformer):

    @classmethod
    def create(cls):
        return cls.alloc().init()

    @classmethod
    def transformedValueClass(cls):
        return NSDecimalNumber

    @classmethod
    def allowsReverseTransformation(cls):
        return True

    def transformedValue_(self, value):
        if value is None:
            return None
        return NSDecimalNumber.numberWithInt_(value)

    def reverseTransformedValue_(self, value):
        if value is None:
            return None
        return int(str(value))


class AbstractNameTransformer(NSValueTransformer):

    @classmethod
    def create(cls):
        return cls.alloc().init()

    def init(self):
        self = super(AbstractNameTransformer, self).init()
        self.rtrans_dict = {}
        self.names = []
        return self

    def add_named_object(self, name, obj):
        self.names.append(name)
        self.rtrans_dict[name] = obj

    @classmethod
    def transformedValueClass(cls):
        return NSString

    @classmethod
    def allowsReverseTransformation(cls):
        return True

    def transformedValue_(self, value):
        raise NotImplementedError("abstract method")

    def reverseTransformedValue_(self, name):
        return self.rtrans_dict[name]


class CharacterEncodingTransformer(AbstractNameTransformer):

    def init(self):
        self = super(CharacterEncodingTransformer, self).init()
        self.add_named_object("Unspecified", None)
        for value in const.CHARACTER_ENCODINGS:
            name = NSString.localizedNameOfStringEncoding_(value)
            self.add_named_object(name, value)
        return self

    def transformedValue_(self, value):
        if value is None:
            return "Unspecified"
        return NSString.localizedNameOfStringEncoding_(value)


class SyntaxDefTransformer(AbstractNameTransformer):

    def init(self):
        self = super(SyntaxDefTransformer, self).init()
        self.add_named_object("None", None)
        return self

    def update_definitions(self, defs):
        for sdef in defs:
            self.add_named_object(sdef.name, sdef)

    def transformedValue_(self, value):
        if value is None:
            return u"None"
        return value.name


def register_value_transformers():
    trans_types = [
        WrapModeTransformer,
        IndentModeTransformer,
        NewlineModeTransformer,
        IntTransformer,
        CharacterEncodingTransformer,
        SyntaxDefTransformer,
    ]
    for t in trans_types:
        trans = t.create()
        NSValueTransformer.setValueTransformer_forName_(trans, t.__name__)

