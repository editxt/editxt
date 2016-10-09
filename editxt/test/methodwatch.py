"""A utility for watching method calls on an object

keyword: AOPython
"""

import re
from objc import selector as objc_selector
#from inspect import ismethod, isfunction
from functools import wraps

exclude_re=re.compile(r"^([A-Z_]|ns|isNS)")


def describe(obj, name, args, kw):
    def rep(value):
        try:
            return repr(value)
        except Exception:
            return "<{}>".format(type(value).__name__)
    argStr = ', '.join([rep(a) for a in args]
       + ['%s=%s' % (k, rep(v)) for k, v in kw.items()])
    print('%s.%s(%s)' % (obj.__name__, name, argStr))


def observe(obj,
            excludes=(),
            exclude_re=exclude_re,
            member_filter=lambda names: names,
            exclude_crashers={
                # NSScrollView methods that cannot be observed
                "getRectsBeingDrawn_count_",
                "sortSubviewsUsingFunction_context_"
            }):

    def wrap(obj, name, method):
        new_attr = None
        if isinstance(method, objc_selector):
            # objc method
            if hasattr(method, "callable"):
                # python method, possibly overriding objc method
                self_ = []
                python_method = method.callable
                @wraps(method)
                def wrapped(self, *args, **kw):
                    self_[:] = [self]
                    try:
                        describe(obj, name, args, kw)
                        return python_method(self, *args, **kw)
                    finally:
                        del self_[:]

                base = obj.__mro__[1]
                if hasattr(base, name):
                    @wraps(method)
                    def new_attr(a, *args, **kw):
                        if not self_:
                            args = (a,) + args
                        else:
                            args = (self_[0], a) + args
                        return getattr(base, name)(*args, **kw)
                    wrapped.selector = method.selector
            else:
                # objc method, not previously overridden in python
                @wraps(method)
                def wrapped(self, *args, **kw):
                    describe(obj, name, args, kw)
                    return getattr(super(new_class, self), name)(*args, **kw)
            wrapped.selector = method.selector
        else:
            # normal python method
            raise NotImplementedError((obj, name, method))
            @wraps(method)
            def wrapped(*args, **kw):
                describe(obj, name, args, kw)
                return method(*args, **kw)
        return wrapped, new_attr

    def can_advise(obj):
        cancall = hasattr(obj, "__call__") and not isinstance(obj, type)
        if cancall:
            match = exclude_re.search(obj.__name__)
        return cancall and not match and not getattr(obj, "isClassMethod", False)

    assert isinstance(obj, type), obj
    members = {}
    excludes = set(excludes)
    excludes.update(exclude_crashers)
    names = [n for n in dir(obj) if n not in excludes]
    for name in member_filter(names):
        attr = getattr(obj, name)
        if not can_advise(attr):
            continue
        #print("wrapping {}.{}".format(obj.__name__, name))
        members[name], new_attr = wrap(obj, name, attr)

        if new_attr is not None:
            # special case for overridden (python) method
            setattr(obj, name, new_attr)

    new_class = type("Observed" + obj.__name__, (obj,), members)
    return new_class


def methodwatch(_obj=None, **kw):
    """Make a class decorator for watching method calls

    Arguments are the same as observe, excluding the first (obj), which
    should be passed to the decorator.
    """
    if _obj is not None:
        assert not kw, kw
        return observe(_obj)
    def decorator(obj):
        return observe(obj, **kw)
    return decorator


def half(names, first=True):
    """Get a new list with half of the given list of names

    Useful for performing a binary search
    """
    index = int(len(names) / 2)
    if index == 0:
        raise Exception(names)
    if first:
        return names[:-index]
    return names[index:]
