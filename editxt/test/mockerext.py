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
import inspect
import logging
import mocker
import types
import weakref

log = logging.getLogger(__name__)

try:
    from Foundation import NSObject
    from objc import selector as objc_selector
except ImportError:
    # dummy types
    NSObject = type("NSObject", (object,), {})
    objc_selector = type("objc_selector", (object,), {})


class MockExt(mocker.Mock):
    """Enhanced Mock class"""

    def __lshift__(self, value, act=False):
        """syntax sugar for more concise expect/result expression syntax

        old:  expect(mock.func(arg)).result(value)
        new: mock.func(arg) << value

        Note: to mock a real left-shift operation use the following code in
        your test case:

            mock.func(arg).__lshift__(value, act=True)
        """
        if self.__mocker__.is_recording() and not act:
            return mocker.expect(self).result(value)
        return self.__mocker_act__("__lshift__", (value,))

    def __rshift__(self, value, act=False):
        """syntax sugar for more concise expect/result expression syntax

        old:  expect(mock.func(arg)).result(value)
        new: mock.func(arg) >> value

        This variation has a subtle difference from the 'sour' code above as
        well as the << operator. It returns 'value' rather than the expect
        object, which allows us to construct expressions while "injecing"
        return values into sub-expressions. For example:

            (mock.func(arg) >> value).value_func()

            Equivalent to:

            expect(mock.func(arg)).result(value)
            value.value_func()

        Note: to mock a real right-shift operation use the following code in
        your test case:

            mock.func(arg).__rshift__(value, act=True)
        """
        if self.__mocker__.is_recording() and not act:
            mocker.expect(self).result(value)
            return value
        return self.__mocker_act__("__rshift__", (value,))

    def __nonzero__(self):
        """improved __nonzero__ implementation

        This now works in Python 2.5 (just guesssing that it broke in that
        version). HOWEVER, this will not return a mock instance, so it cannot
        be used with expect(...).
        """
        try:
            result = self.__mocker_act__("nonzero")
        except mocker.MatchError, e:
            result = True
        if not isinstance(result, (bool, int)):
            # force result since this method must return a bool or int
            result = True
        return result

    def __repr__(self):
        """Compute a representation that describes the mock"""
        args = []
        for name, default in [("path", None), ("name", None), ("spec", None),
            ("type", None), ("object", None), ("passthrough", False),
            ("patcher", None), ("count", True)]:
            value = getattr(self, "__mocker_" + name + "__")
            if value is not default:
                if name in ("spec", "type"):
                    if name != "type" or value != self.__mocker_spec__:
                        if isinstance(value, property):
                            nameval = "property(%s, ...)" % value.fget.__name__
                        else:
                            nameval = value.__name__
                        args.append("%s=%s" % (name, nameval))
                elif name == "path":
                    if str(value) != "<mock>":
                        args.append("%s=%s" % (name, value))
                elif name != "name" or str(value) != str(self.__mocker_path__):
                    args.append("%s=%r" % (name, value))
        if args:
            return "<mock %x %s>" % (id(self), " ".join(args))
        return super(MockExt, self).__repr__() # lame, hope we never get here...

    def __getattribute__(self, name):
        # HACK overridden here because super call in original results in infinite recursion
        if name == "__pyobjc_object__":
            raise AttributeError(name)
        if name.startswith("__mocker_"):
            return object.__getattribute__(self, name)
        if name == "__class__":
            if self.__mocker__.is_recording() or self.__mocker_type__ is None:
                return type(self)
            return self.__mocker_type__
        return self.__mocker_act__("getattr", (name,))

    def __setattr__(self, name, value):
        # HACK overridden here because super call in original results in infinite recursion
        if name.startswith("__mocker_"):
            return object.__setattr__(self, name, value)
        return self.__mocker_act__("setattr", (name, value))


class DeferredRepr(object):
    """HACK __repr__ might call other mocked methods; thus must be deferred"""
    def __init__(self, obj):
        self.obj = obj
    def __repr__(self):
        try:
            return repr(self.obj)
        except Exception:
            return '<%s>' % type(self.obj).__name__


class MockerExt(mocker.Mocker):
    """Enhanced Mocker class"""

    def method(self, *method_spec, **kw):
        """Create a mock, and replace the original method with the mock.

        On replay, method will be replaced on the class where it was
        originally defined. All calls to that method will be intercepted
        by the returned mock.

        @param *method_spec: method or type and method name to be mocked, and
            replaced by the mock in replay mode.
        @param name: (keyword arg) name of the method being replaced.  The name
            is rarely needed, as method.__name__ is usually correct.
        @param passthrough: (keyword arg, default False) if True, passthrough of
            actions on the real object will happen automatically.
        """
        replacer = MethodReplacer(self.mock, *method_spec, **kw)
        self._get_replay_restore_event().add_task(replacer)
        return replacer

    def property(self, obj, name, verify=True):
        """Create a PropertyMock that replaces a property of class_"""
        event = self._get_replay_restore_event()
        mock = self.mock(property, name=DeferredRepr(obj))
        return PropertyReplacer.replace(obj, name, event, mock, verify)


class ReplacedMethod(object):

    replaced_methods = {}

    def __new__(cls, objtype, method_name, func, class_):
        rep = cls.replaced_methods.get((objtype, method_name))
        if rep is None:
            rep = super(ReplacedMethod, cls).__new__(cls)
            rep.objtype = objtype
            rep.name = rep.__name__ = method_name
            rep.func = func
            rep.class_ = class_
            rep.registry = []
            rep.installed = False
            cls.replaced_methods[(objtype, method_name)] = rep
            #setattr(objtype, method_name, rep)
        return rep

    def register(self, obj, mock, passthrough):
        self.registry.append((obj, mock, passthrough))

    def install(self):
        if not self.installed:
            self.installed = True
            setattr(self.objtype, self.name, self)

    def discard(self, obj):
        for i, (mocked, mock, passthrough) in enumerate(list(self.registry)):
            if obj is mocked:
                del self.registry[i]
                break
        if not issubclass(self.objtype, NSObject):
            # restore the world to the way it was before
            # (not possible with PyObjC types)
            del self.replaced_methods[(self.objtype, self.name)]
            setattr(self.objtype, self.name, self.func) #self.__get__(None, self.objtype))

    def __get__(self, obj, objtype=None):
        # TODO look for obj is None and implement __call__
        # may help with static method handling
        for mocked, mock, passthrough in self.registry:
            if obj is mocked or mocked is None:
                # TODO implement passthrough
                method = getattr(mock, self.name)
                return method
        return self.func.__get__(obj, objtype)
    
#   def __set__(self, obj, value):
#       raise NotImplementedError

#   def __call__(self, *args, **kw):
#       return self.original(*args, **kw)


class MethodReplacer(mocker.Task):
    """Task which installs and deinstalls a mocked method."""

    NA = object()

    @staticmethod
    def _create_func(name, nargs):
        """create a function with the specified name and number of arguments"""
        import types
        def f(): pass
        names = tuple("a%i" % i for i in range(nargs))
        f_code = types.CodeType(
            nargs,
            f.func_code.co_nlocals,
            f.func_code.co_stacksize,
            f.func_code.co_flags,
            f.func_code.co_code,
            f.func_code.co_consts,
            f.func_code.co_names,
            names,
            f.func_code.co_filename,
            name,
            f.func_code.co_firstlineno,
            f.func_code.co_lnotab,
        )
        return types.FunctionType(f_code, f.func_globals, name)

    def __init__(self, mock_factory, *method_spec, **kw):
        # get objtype and method_name
        if len(method_spec) == 1:
            obj = None
            name = kw.get("name")
            method = method_spec[0]
        elif len(method_spec) == 2:
            obj, name = method_spec
            method = None
            assert name is not None
        else:
            raise TypeError("invalid method_spec: %r" % (method_spec,))

        self.is_classmethod = False
        if isinstance(method, objc_selector) or isinstance(obj, NSObject):
            # method on pyobjc object
            if method is not None:
                obj = method.self
                if name is None:
                    name = method.selector.replace(":", "_")
            objtype = method.definingClass if obj is None else type(obj)
            func = getattr(objtype, name)
            class_ = type(objtype.__name__, (object,), {name: func})
        else:
            if method is not None:
                obj = getattr(method, "im_self", None)
            else:
                assert obj is not None
                method = getattr(obj, name)
            # TODO unbound method on pure python type
            # TODO static method on pure python type
            if isinstance(obj, type):
                # class method on pure python object
                self.is_classmethod = True
                name = method.__name__ if name is None else name
                func = method.im_func
                class_ = objtype = obj
                obj = None
            elif obj is not None:
                # bound method on pure python object
                name = method.__name__ if name is None else name
                func = method.im_func
                class_ = objtype = type(obj)
                assert objtype.__name__ != "type"
            else:
                raise TypeError("unknown method type: %r" % method)
        self.obj = obj
        self.replaced = rep = ReplacedMethod(objtype, name, func, class_)
        self.mock = mock_factory(rep.class_, name="<%s>" % rep.class_.__name__)
        self.passthrough = kw.get("passthrough", False)
        rep.register(obj, self.mock, self.passthrough)

    @property    
    def method(self):
        return self.replaced.__get__(self.obj, self.replaced.objtype)

    def __call__(self, *args, **kw):
        return self.method(*args, **kw)

    def replay(self):
        # late install necessitated by classmethod replacement:
        # an additional method retrieval occurs due to the spec_checker_recorder
        # getting the method from the class. In an instance method replacement,
        # this does not matter (method retrieval is not recorded in this case),
        # but in the class method case it matters because it an extra method
        # retrieval is recorded (all method retrievals are recorded for class
        # methods)
        self.replaced.install()

    def restore(self):
        self.replaced.discard(self.obj)


class PropertyMock(object):

    def __init__(self, name, original):
        self.name = name
        self.original = original
        self.registry = {}

    def register(self, obj, mock):
        self.registry[obj] = mock

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        mock = self.registry[obj]
        return getattr(mock, self.name)

    def __set__(self, obj, value):
        mock = self.registry[obj]
        setattr(mock, self.name, value)

    def __delete__(self, obj):
        mock = self.registry[obj]
        return delattr(mock, self.name)


class PropertyValueMock(object):

    def __init__(self, obj, propmock):
        self.obj = obj
        self.mock = propmock

    def _get_value(self):
        return self.mock.__get__(self.obj)
    def _set_value(self, value):
        self.mock.__set__(self.obj, value)
    def _del_value(self):
        self.mock.__delete__(self.obj)
    value = property(_get_value, _set_value, _del_value)


class PropertyReplacer(mocker.Task):
    """Task which installs and deinstalls a mocked property"""
    NA = object()

    @classmethod
    def replace(cls, obj, name, event, mock, verify):
        type_ = type(obj)
        if verify and name not in dir(obj):
            raise AssertionError("unknown property: %s" % name)
        try:
            prop = getattr(type_, name)
        except AttributeError:
            # HACK fix for objc IBOutlet
            prop = type_.__dict__.get(name, cls.NA)
        if not isinstance(prop, PropertyMock):
            prop = PropertyMock(name, prop)
            event.add_task(cls(type_, name, prop))
        prop.register(obj, mock)
        return PropertyValueMock(obj, prop)

    def __init__(self, type_, name, prop):
        self.type_ = type_
        self.name = name
        self.prop = prop
        setattr(type_, name, prop)

    def restore(self):
        if self.prop.original is self.NA:
            delattr(self.type_, self.name)
        else:
            setattr(self.type_, self.name, self.prop.original)

    def __del__(self):
        self.restore()


class SpecCheckerExt(mocker.SpecChecker):
    """Task to check if arguments of the last action conform to a real method.
    
    mockerext improvements:
     -  avoids method.__nonzero__ ()
     -  handles pyobjc methods
    note: most of these are ugly patches because they redefine entire methods
    """
    
    VARARGS_METHOD_SPECS = {
        "arrayWithObjects:": (("self",), "args", None, None),
        "dictionaryWithObjectsAndKeys:": (("self",), "args", None, None),
    }

    def __init__(self, method):
        self._method = method
        self._unsupported = False

        if method is not None:
            try:
                self._args, self._varargs, self._varkwargs, self._defaults = \
                    SpecCheckerExt.getargspec(method)
            except TypeError:
                self._unsupported = True
            else:
                if self._defaults is None:
                    self._defaults = ()
                if type(method) is type(self.run) \
                    or isinstance(method, objc_selector):
                    self._args = self._args[1:]

    @classmethod
    def getargspec(cls, method):
        if isinstance(method, objc_selector):
            try:
                method = method.callable
            except AttributeError:
                try:
                    # HACK handle methods with varargs
                    return cls.VARARGS_METHOD_SPECS[method.selector]
                except KeyError:
                    pass
                nargs = method.selector.count(":")
                names = tuple(["self"] + ["arg%i" % i for i in xrange(nargs)])
                return names, None, None, None
        return inspect.getargspec(method)

    def verify(self):
        if self._method is None:
            raise AssertionError("Method not found in real specification")


def install():
    mocker.Mock = MockExt
    mocker.Mocker = MockerExt
    mocker.SpecChecker = SpecCheckerExt
