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

from mocker import Mocker, expect, ANY, MATCH
from nose.tools import eq_
from AppKit import *
from Foundation import *

import editxt.constants as const


from editxt.test.util import TestConfig

log = logging.getLogger(__name__)


def test_wrap_mode_transformer():
    from editxt.valuetrans import WrapModeTransformer
    assert WrapModeTransformer.allowsReverseTransformation()
    eq_(WrapModeTransformer.transformedValueClass(), int)
    def test(func, val, trans):
        eq_(func(val), trans)
    trans = WrapModeTransformer.create()
    # forward transformations
    yield test, trans.transformedValue_, None, None
    yield test, trans.transformedValue_, const.LINE_WRAP_WORD, 1
    yield test, trans.transformedValue_, const.LINE_WRAP_NONE, 0
    # reverse transformations
    yield test, trans.reverseTransformedValue_, None, None
    yield test, trans.reverseTransformedValue_, 1, const.LINE_WRAP_WORD
    yield test, trans.reverseTransformedValue_, 0, const.LINE_WRAP_NONE

def test_key_value_transformer():
    from editxt.valuetrans import KeyValueTransformer
    assert KeyValueTransformer.allowsReverseTransformation()
    eq_(KeyValueTransformer.transformedValueClass(), int)
    def test(func, val, trans):
        eq_(func(val), trans)
    data = {None:None, "one": 1, "two": 2}
    trans = KeyValueTransformer.alloc().init(data)
    # forward transformations
    yield test, trans.transformedValue_, None, None
    yield test, trans.transformedValue_, "one", 1
    yield test, trans.transformedValue_, "two", 2
    # reverse transformations
    yield test, trans.reverseTransformedValue_, None, None
    yield test, trans.reverseTransformedValue_, 1, "one"
    yield test, trans.reverseTransformedValue_, 2, "two"

def test_int_transformer():
    from editxt.valuetrans import IntTransformer
    assert IntTransformer.allowsReverseTransformation()
    eq_(IntTransformer.transformedValueClass(), NSDecimalNumber)
    def test(func, val, trans):
        eq_(func(val), trans)
    def ftest(func, val):
        if isinstance(val, basestring):
            tval = NSDecimalNumber.decimalNumberWithString_(val)
        else:
            tval = NSDecimalNumber.numberWithInt_(val)
        test(func, val, tval)
        eq_(type(func(val)), type(tval))
    def rtest(func, val):
        if isinstance(val, basestring):
            tval = val
            val = int(float(val))
        else:
            tval = NSDecimalNumber.numberWithInt_(val)
        test(func, tval, val)
        eq_(type(func(tval)), type(val))
    trans = IntTransformer.alloc().init()
    # forward transformations
    yield test, trans.transformedValue_, None, None
    yield ftest, trans.transformedValue_, -100
    yield ftest, trans.transformedValue_, -1
    yield ftest, trans.transformedValue_, 0
    yield ftest, trans.transformedValue_, 1
    yield ftest, trans.transformedValue_, 100
    yield ftest, trans.transformedValue_, "100"
    yield ftest, trans.transformedValue_, "6.0"
    # reverse transformations
    yield test, trans.reverseTransformedValue_, None, None
    yield rtest, trans.reverseTransformedValue_, -100
    yield rtest, trans.reverseTransformedValue_, -1
    yield rtest, trans.reverseTransformedValue_, 0
    yield rtest, trans.reverseTransformedValue_, 1
    yield rtest, trans.reverseTransformedValue_, 100
    yield rtest, trans.reverseTransformedValue_, "100"
    yield rtest, trans.reverseTransformedValue_, "6.0"

def test_encoding_transformer():
    from editxt.valuetrans import CharacterEncodingTransformer
    assert CharacterEncodingTransformer.allowsReverseTransformation()
    eq_(CharacterEncodingTransformer.transformedValueClass(), NSString)
    def test(func, val, trans):
        eq_(func(val), trans)
    def ftest(func, val):
        tval = NSString.localizedNameOfStringEncoding_(val)
        test(func, val, tval)
        eq_(type(func(val)), type(tval))
    def rtest(func, val):
        tval = NSString.localizedNameOfStringEncoding_(val)
        test(func, tval, val)
        eq_(type(func(tval)), type(val))
    trans = CharacterEncodingTransformer.alloc().init()
    # forward transformations
    yield test, trans.transformedValue_, None, "Unspecified"
    yield ftest, trans.transformedValue_, NSASCIIStringEncoding
    yield ftest, trans.transformedValue_, NSNEXTSTEPStringEncoding
    yield ftest, trans.transformedValue_, NSJapaneseEUCStringEncoding
    yield ftest, trans.transformedValue_, NSUTF8StringEncoding
    yield ftest, trans.transformedValue_, NSISOLatin1StringEncoding
    yield ftest, trans.transformedValue_, NSSymbolStringEncoding
    yield ftest, trans.transformedValue_, NSNonLossyASCIIStringEncoding
    yield ftest, trans.transformedValue_, NSShiftJISStringEncoding
    yield ftest, trans.transformedValue_, NSISOLatin2StringEncoding
    yield ftest, trans.transformedValue_, NSUnicodeStringEncoding
    yield ftest, trans.transformedValue_, NSWindowsCP1251StringEncoding
    yield ftest, trans.transformedValue_, NSWindowsCP1252StringEncoding
    yield ftest, trans.transformedValue_, NSWindowsCP1253StringEncoding
    yield ftest, trans.transformedValue_, NSWindowsCP1254StringEncoding
    yield ftest, trans.transformedValue_, NSWindowsCP1250StringEncoding
    yield ftest, trans.transformedValue_, NSISO2022JPStringEncoding
    yield ftest, trans.transformedValue_, NSMacOSRomanStringEncoding
    #yield ftest, trans.transformedValue_, NSProprietaryStringEncoding
    # reverse transformations
    yield test, trans.reverseTransformedValue_, "Unspecified", None
    yield rtest, trans.reverseTransformedValue_, NSASCIIStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSNEXTSTEPStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSJapaneseEUCStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSUTF8StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSISOLatin1StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSSymbolStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSNonLossyASCIIStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSShiftJISStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSISOLatin2StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSUnicodeStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSWindowsCP1251StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSWindowsCP1252StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSWindowsCP1253StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSWindowsCP1254StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSWindowsCP1250StringEncoding
    yield rtest, trans.reverseTransformedValue_, NSISO2022JPStringEncoding
    yield rtest, trans.reverseTransformedValue_, NSMacOSRomanStringEncoding
    #yield rtest, trans.reverseTransformedValue_, NSProprietaryStringEncoding

def test_syntaxdef_transformer():
    from editxt import app
    from editxt.syntax import PLAIN_TEXT
    from editxt.valuetrans import SyntaxDefTransformer
    assert SyntaxDefTransformer.allowsReverseTransformation()
    eq_(SyntaxDefTransformer.transformedValueClass(), NSString)
    def test(func, val, trans):
        eq_(func(val), trans)
    sdef = type("FakeDef", (object,), {"name": "Fake Syntax"})
    trans = SyntaxDefTransformer.alloc().init()
    trans.update_definitions([PLAIN_TEXT, sdef])
    yield test, trans.transformedValue_, None, "None"
    yield test, trans.transformedValue_, PLAIN_TEXT, "Plain Text"
    yield test, trans.transformedValue_, sdef, sdef.name
    yield test, trans.reverseTransformedValue_, "None", None
    yield test, trans.reverseTransformedValue_, "Plain Text", PLAIN_TEXT
    yield test, trans.reverseTransformedValue_, sdef.name, sdef

def test_register_value_transformers():
    import editxt.valuetrans as mod
    from editxt.valuetrans import register_value_transformers
    m = Mocker()
    vt = m.replace(mod, 'NSValueTransformer')
    trans = [
        mod.WrapModeTransformer,
        mod.IndentModeTransformer,
        mod.NewlineModeTransformer,
        mod.IntTransformer,
        mod.CharacterEncodingTransformer,
        mod.SyntaxDefTransformer,
    ]
    def make_is_trans(t):
        def is_trans(arg):
            return isinstance(arg, t)
        return is_trans
    for t in trans:
        vt.setValueTransformer_forName_(MATCH(make_is_trans(t)), t.__name__)
    with m:
        register_value_transformers()
