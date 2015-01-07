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
"""Tests for mocker extensions (mockerext module)

Note: some of these tests depend on PyObjC since they are geared toward making
testing of PyObjC applications more convenient.
"""
import logging
import mocker
import objc
from editxt.test.mockerext import install, MockerExt
from editxt.test.util import assert_raises, eq_, TestConfig

log = logging.getLogger(__name__)

def setup():
    install()

def test_MockExt__lshift__():
    def f(x):
        return x.meth(), x.meth()
    m = mocker.Mocker()
    y = m.mock()
    (y.meth() << 1).count(2)
    with m:
        result = f(y)
        assert result == (1, 1), "unexpected: %r" % (result,)

def test_MockExt__rshift__():
    def f(x):
        return x.meth()
    obj = object()
    m = mocker.Mocker()
    y = m.mock()
    assert (y.meth() >> obj) is obj
    with m:
        result = f(y)
        assert result is obj, "unexpected: %r" % (result,)

def test_MockerExt_method_of_NSObject():
    from Foundation import NSObject
    class Subclass(object): pass
    def test(method_as_string):
        def run(obj):
            m = mocker.Mocker()
            ob2 = object()
            # part 1: replace method
            if method_as_string:
                args = (obj, "isEqualTo_")
            else:
                args = (obj.isEqualTo_,)
            iseq = m.method(*args)
            iseq(obj) >> False
            with m:
                assert not obj.isEqualTo_(obj), "%r == %r" % (obj, obj)
            assert obj.isEqualTo_(obj), "%r != %r" % (obj, obj)
            # part 2: check if the original is called after test
#            func = iseq.replaced.func
#            try:
#                class Error(Exception): pass
#                def error(self, arg):
#                    assert self is obj, "%r != %r" % (self, obj)
#                    assert arg is ob2, repr(arg)
#                    raise Error("expected error")
#                iseq.replaced.func = error
#                assert_raises(Error, obj.isEqualTo_, ob2)
#            finally:
#                iseq.replaced.func = func
        a = NSObject.alloc().init()
        b = NSObject.alloc().init()
        run(a)
        run(b) # make sure first run did not disable future method replacements
    yield test, False
    yield test, True

def test_MockerExt_PyObjC_num_args_check():
    from Foundation import NSObject
    def test(c):
        m = mocker.Mocker()
        obj = c.cls.alloc().init()
        args = (obj, c.name) if c.method_as_string else (getattr(obj, c.name),)
        mocked = m.method(*args)
        mocked(*range(c.targs))
        try:
            with m:
                getattr(obj, c.name)(*range(c.targs))
        except AssertionError:
            if c.nargs == c.targs:
                raise # unexpected error (had correct number of arguments)
        else:
            assert c.nargs == c.targs, "wrong arg spec : expected MatchError"
    class PySubclass(NSObject):
        def method_with_zero_args(self):
            pass
        def method_with_one_arg(self, arg):
            pass
    c = TestConfig()
    for method_as_string in [True, False]:
        c = c(cls=NSObject, method_as_string=method_as_string)
        for n in [0, 1, 2]:
            yield test, c(name="isEqualTo_", nargs=1, targs=n)
        for n in [2, 3, 4]:
            yield test, c(name="insertValue_atIndex_inPropertyWithKey_", nargs=3, targs=n)
        c = c(cls=PySubclass)
        for n in [0, 1]:
            yield test, c(name="method_with_zero_args", nargs=0, targs=n)
        for n in [0, 1, 2]:
            yield test, c(name="method_with_one_arg", nargs=1, targs=n)

# def test_fail():
#   assert False, "stop"

def test_MockerExt_method_of_PyObject():
    from Foundation import NSObject
    class Subclass(object): pass
    def test(obj, method_as_string):
        m = mocker.Mocker()
        ob2 = object()
        # part 1: replace method
        func = obj.isEqualTo_.__func__
        if method_as_string:
            args = (obj, "isEqualTo_")
        else:
            args = (obj.isEqualTo_,)
        iseq = m.method(*args)
        iseq(ob2) >> True
        with m:
            assert obj.isEqualTo_(ob2)
        assert not obj.isEqualTo_(ob2), "%r == %r" % (obj, ob2)
        # part 2: verify that the replaced method is totally removed
        def error(self, arg):
            assert False, "this function should not be called"
        iseq.replaced.func = error
        assert not obj.isEqualTo_(ob2)

    class InstanceMethodTest(object):
        def isEqualTo_(self, other):
            return False
    yield test, InstanceMethodTest(), False
    yield test, InstanceMethodTest(), True
# (Pdb) [str(e.path) for e in rval.__mocker__._events]
# ['None', '<InstanceMethodTest>.isEqualTo_', '<InstanceMethodTest>.isEqualTo_(<object object at 0x289e0>)']

    class ClassMethodTest(object):
        @classmethod
        def isEqualTo_(cls, other):
            return False
    yield test, ClassMethodTest(), False


# (Pdb) [str(e.path) for e in rval.__mocker__._events]
# ['None', '<ClassMethodTest>.isEqualTo_', '<ClassMethodTest>.isEqualTo_(<object object at 0x289e8>)', '<ClassMethodTest>.isEqualTo_']

# -> rval = method(*args, **kw)
# /Users/dmiller/Code/EditXT/libtest/mocker-0.10.1/build/lib/mocker.py(1066)__call__()
# -> return self.__mocker_act__("call", args, kwargs)
# /Users/dmiller/Code/EditXT/libtest/mocker-0.10.1/build/lib/mocker.py(1031)__mocker_act__()
# -> return self.__mocker__.act(path)

# [str(e.path) for e in self._events]

# <function spec_checker_recorder at 0x5f651f0>
# [... '<ClassMethodTest>.isEqualTo_(<object object at 0x289f0>)', '<ClassMethodTest>.isEqualTo_']

# InstanceMethodTest
# <class 'editxt.test.test_mockerext.InstanceMethodTest'>
# (Action('getattr', ('isEqualTo_',), {}, <mocker.Path object at 0x616ab10>),)
# ['None', '<InstanceMethodTest>.isEqualTo_']
# <class 'editxt.test.test_mockerext.InstanceMethodTest'>
# (Action('getattr', ('isEqualTo_',), {}, <mocker.Path object at 0x616ab10>), Action('call', (<object object at 0x289e0>,), {}, <mocker.Path object at 0x616abb0>))
# ['None', '<InstanceMethodTest>.isEqualTo_', '<InstanceMethodTest>.isEqualTo_(<object object at 0x289e0>)']

# The additional method retrieval is due to the spec_checker_recorder() getting
# the method from the class. In an instance method replacement, this would not
# matter, but in the class method case it does because it records a method
# retrieval (all method retrievals are recorded for class methods)



#   def isEqualTo_(other):
#       return False
#   Test.isEqualTo_ = staticmethod(isEqualTo_)
#   yield test, Test()
# 
#   def isEqualTo_(cls, other):
#       return cls == other
#   Test.isEqualTo_ = classmethod(isEqualTo_)
#   yield test, c(obj=Test())

def test_MockerExt_property():
    from Foundation import NSObject
    def test(base, create):
        def foo(self):
            return "foo"
        def _get_bar(self):
            return self._bar
        def _set_bar(self, value):
            self._bar = value
        def _del_bar(self):
            del self._bar
        bar = property(_get_bar, _set_bar, _del_bar)
        T = type("T", (base,), dict(foo=foo, bar=bar))
        m = MockerExt()
        t = create(T)
        m.property(t, "bar")
        t.bar = "xyz"
        t.bar >> "abc"
        del t.bar
        with m:
            assert t.foo() == "foo"
            t.bar = "xyz"
            b = t.bar
            assert b == "abc", "got %r" % b
            del t.bar
            assert isinstance(t, T)
        assert T.bar is bar
    yield test, object, lambda T: T()
    yield test, NSObject, lambda T: T.alloc().init()

def test_MockerExt_property_attr():
    from Foundation import NSObject
    class Obj(object):
        def __init__(self):
            self.foo = 0
    obj = Obj()
    m = MockerExt()
    m.property(obj, "foo")
    obj.foo >> "xyz"
    obj.foo = "abc"
    obj.foo >> "def"
    with m:
        assert obj.foo == "xyz"
        obj.foo = "abc"
        assert obj.foo == "def"
        assert isinstance(obj, Obj)
    assert not hasattr(Obj, "foo")

def test_MockerExt_property_value_mock():
    from Foundation import NSObject
    class Obj(object):
        def __init__(self):
            self.foo = 0
    obj = Obj()
    m = MockerExt()
    foo = m.property(obj, "foo")
    foo.value >> "xyz"
    foo.value = "abc"
    foo.value >> "def"
    del foo.value
    with m:
        assert obj.foo == "xyz"
        obj.foo = "abc"
        assert obj.foo == "def"
        del obj.foo
        assert isinstance(obj, Obj)
    assert not hasattr(Obj, "foo")

def test_MockerExt_property_multiple_instances():
    def eq(a, b):
        assert a == b, "%r != %r" % (a, b)
    class T(object):
        @property
        def bar(self):
            return self._bar
    def setup(m, num):
        t = T()
        m.property(t, "bar")
        t.bar >> num
        return t
    m = MockerExt()
    t1 = setup(m, 1)
    t2 = setup(m, 2)
    with m:
        eq(t1.bar, 1)
        eq(t2.bar, 2)

def test_SpecCheckerExt_function_signature():
    def test(args, msg):
        class Test(object): pass
        def func(arg): pass
        t = Test()
        t.func = func
        m = MockerExt()
        m.replace(t, "func")(*args)
        def check(err):
            assert msg in str(err), "{!r} not in {!r}".format(msg, err)
        with m, assert_raises(AssertionError, msg=check):
            t.func(*args)
    yield test, (1, 2), "Specification is func(arg): too many args provided"
    yield test, (), "Specification is func(arg): 'arg' not provided"

if __name__ == "__main__":
    test_MockExt__lshift__()
    test_MockExt__rshift__()
    test_MockExt_property()

    m = mocker.Mocker()
    t = m.mock(object)
    print(t)
    print(t.y())
