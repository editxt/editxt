"""logmeta - a metaclass factory for method call logging (for debugging)

Examples:
log = logging.getLogger(__name__)

class Document(NSDocument):
    from editxt.test.logmeta import logmeta
    __metaclass__ = logmeta(log,
        ignore=["Representation", "eadFromFile", "riteToFile",
            "revertToSavedFromFile_ofType_", "initWithContentsOfFile_ofType_",
            "fileName", "fileURL", "hasUnautosavedChanges", "isDocumentEdited"],
        override=["[Dd]ocument", "[Ss]ave", "[Ff]ile", "[Rr]ead", "URL", "^_[a-z]"],
        verbose=["ileModif"]
    )

class Window(NSWindow):
    from editxt.test.logmeta import logmeta
    __metaclass__ = logmeta(log,
        ignore="(?i)key.*val",
        override=["[Dd]ocument", "[Ss]ave"],
        verbose="^setDocument_$"
    )

"""
import re
import inspect
from itertools import chain

DEFAULT_IGNORE = ("^pyobjc", "^CA_", "^methodFor", "__", ":", "^logmeta$")

def logmeta(log, ignore=None, override=None, verbose=None, local_override=False,
    default_ignore=DEFAULT_IGNORE):
    """Create a metaclass that wraps methods with logging decorators

    ignore - list of regular expressions matching methods to ignore
    override - list of regular expressions matching methods in base classes
        that should be overridden for the purpose of logging.
    verbose - list of regular expressions matching methods to log verbosely
    local_override - override all methods defined in the class to which
        the metaclass is applied. Defaults to False.
    default_ignore - list of default ignore patterns.
    """
    def regexps(value):
        if value is None:
            value = []
        elif isinstance(value, str):
            value = [value]
        return [re.compile(v) for v in value]
    ignore = regexps(ignore) + regexps(default_ignore)
    override = regexps(override)
    verbose = regexps(verbose)
    def should_wrap(attr, item, ignore, override, wrapped):
        return (hasattr(item, "__call__") and
            #(inspect.isfunction(item) or isinstance(item, objc_selector)) and
            not attr in wrapped and
            not any(e.search(attr) for e in ignore) and
            any(e.search(attr) for e in override))
    def short_repr(value):
        v = repr(value)
        if len(v) > 100:
            v = "%s...%s" % (v[:10], v[-10:])
        return v

    class LogMeta(type):

        def __new__(cls, classname, bases, classdict):
            log.info("%s : installing loggers", classname)
            if local_override:
                overlocal = regexps("^%s$" % n for n in classdict)
            else:
                overlocal = override
            wrapped = set()
            for attr, item in sorted(classdict.items()):
                if attr == "logmeta" and item is logmeta:
                    # omit logmeta, which was probably not intended to be a
                    # method. Handle common usecase:
                    # class X(object):
                    #     from debug import logmeta
                    #     __metaclass__ = logmeta(log)
                    classdict.pop(attr)
                    continue
                if should_wrap(attr, item, ignore, overlocal, wrapped):
                    classdict[attr] = cls.logwrap(classname, attr, item)
                    wrapped.add(attr)
            if override:
                for baseclass in bases:
                    for attr, item in sorted(baseclass.__dict__.items()):
                        if should_wrap(attr, item, ignore, override, wrapped):
                            classdict[attr] = cls.logwrap(classname, attr, item,
                                baseclass.__name__)
                            wrapped.add(attr)
            return super(LogMeta, cls).__new__(cls, classname, bases, classdict)
            #cls.class_ = super(LogMeta, cls).__new__(cls, classname, bases, classdict)
            #return cls.class_

        @classmethod
        def logwrap(cls, classname, name, method, basename=None):
            log.info("    %s.%s", basename or classname, name)
            vlog = any(e.search(name) for e in verbose)
            def wrapper(f, *args, **kw):
                if isinstance(method, staticmethod):
                    _o = classname
                else:
                    _o = "<%s at 0x%x>" % (classname, id(args[0]))
                _a = (short_repr(a) for a in args[1:])
                _k = ('%s=%s' % (k, short_repr(v)) for k, v in sorted(kw.items()))
                argstr = ", ".join(chain(_a, _k))
                if vlog:
                    try:
                        rval = f(*args, **kw)
                        log.info("%s.%s(%s) -> %r", _o, name, argstr, rval)
                        return rval
                    except Exception as exc:
                        log.info("%s.%s(%s) raised %s", _o, name, argstr, exc)
                        raise
                log.info("%s.%s(%s)", _o, name, str(argstr).decode("UTF-8"))
                return f(*args, **kw)
            return decorator(wrapper, method)

    return classmaker((LogMeta,))


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# PyObjC-aware decorator
# shamelessly copied from http://pypi.python.org/pypi/decorator
# http://micheles.googlecode.com/hg/decorator/documentation.html

import os, sys, re, inspect
from functools import partial
from objc import selector as objc_selector

DEF = re.compile('\s*def\s*([_\w][_\w\d]*)\s*\(')

reserved_words = set("""
    and       del       from      not       while    
    as        elif      global    or        with     
    assert    else      if        pass      yield    
    break     except    import    print              
    class     exec      in        raise              
    continue  finally   is        return             
    def       for       lambda    try
""".split())

# basic functionality
class FunctionMaker(object):
    """
    An object with the ability to create functions with a given signature.
    It has attributes name, doc, module, signature, defaults, dict and
    methods update and make.
    """
    def __init__(self, func=None, name=None, signature=None,
                 defaults=None, doc=None, module=None, funcdict=None):
        if func:
            # func can be a class or a callable, but not an instance method
            self.name = func.__name__
            if self.name == '<lambda>': # small hack for lambda functions
                self.name = '_lambda_' 
            self.doc = func.__doc__
            try:
                self.module = func.__module__
            except AttributeError:
                pass
            if inspect.isfunction(func):
                argspec = inspect.getargspec(func)
                self.args, self.varargs, self.keywords, self.defaults = argspec
                for i, arg in enumerate(self.args):
                    setattr(self, 'arg%d' % i, arg)
                self.signature = inspect.formatargspec(
                    formatvalue=lambda val: "", *argspec)[1:-1]
                self.dict = func.__dict__.copy()
            elif isinstance(func, objc_selector):
                name = func.selector.replace(":", "_")
                self.args = ["self"]
                reserved = set(self.args) | reserved_words
                for arg in func.selector.split(":")[:-1]:
                    while arg in reserved or not arg:
                        arg += "_"
                    reserved.add(arg)
                    self.args.append(arg)
                self.varargs, self.keywords, self.defaults = None, None, None
                for i, arg in enumerate(self.args):
                    setattr(self, 'arg%d' % i, arg)
                self.signature = inspect.formatargspec(
                    self.args, formatvalue=lambda val: "")[1:-1]
                self.dict = {}
        if name:
            self.name = name
        if signature is not None:
            self.signature = signature
        if defaults:
            self.defaults = defaults
        if doc:
            self.doc = doc
        if module:
            self.module = module
        if funcdict:
            self.dict = funcdict
        # check existence required attributes
        assert hasattr(self, 'name')
        if not hasattr(self, 'signature'):
            raise TypeError('You are decorating a non function: %s' % func)

    def update(self, func, **kw):
        "Update the signature of func with the data in self"
        func.__name__ = self.name
        func.__doc__ = getattr(self, 'doc', None)
        func.__dict__ = getattr(self, 'dict', {})
        func.__defaults__ = getattr(self, 'defaults', ())
        callermodule = sys._getframe(3).f_globals.get('__name__', '?')
        func.__module__ = getattr(self, 'module', callermodule)
        func.__dict__.update(kw)

    def make(self, src_templ, evaldict=None, addsource=False, **attrs):
        "Make a new function from a given template and update the signature"
        src = src_templ % vars(self) # expand name and signature
        evaldict = evaldict or {}
        mo = DEF.match(src)
        if mo is None:
            raise SyntaxError('not a valid function template\n%s' % src)
        name = mo.group(1) # extract the function name
        reserved_names = set([name] + [
            arg.strip(' *') for arg in self.signature.split(',')])
        for n, v in evaldict.items():
            if n in reserved_names:
                raise NameError('%s is overridden in\n%s' % (n, src))
        if not src.endswith('\n'): # add a newline just for safety
            src += '\n'
        try:
            code = compile(src, '<string>', 'single')
            exec(code, evaldict)
        except:
            print('Error in generated code:', file=sys.stderr)
            print(src, file=sys.stderr)
            raise
        func = evaldict[name]
        if addsource:
            attrs['__source__'] = src
        self.update(func, **attrs)
        return func

    @classmethod
    def create(cls, obj, body, evaldict, defaults=None,
               doc=None, module=None, addsource=True,**attrs):
        """
        Create a function from the strings name, signature and body.
        evaldict is the evaluation dictionary. If addsource is true an attribute
        __source__ is added to the result. The attributes attrs are added,
        if any.
        """
        if isinstance(obj, str): # "name(signature)"
            name, rest = obj.strip().split('(', 1)
            signature = rest[:-1] #strip a right parens            
            func = None
        else: # a function
            name = None
            signature = None
            func = obj
        fun = cls(func, name, signature, defaults, doc, module)
        ibody = '\n'.join('    ' + line for line in body.splitlines())
        return fun.make('def %(name)s(%(signature)s):\n' + ibody, 
                        evaldict, addsource, **attrs)
  
def decorator(caller, func=None):
    """
    decorator(caller) converts a caller function into a decorator;
    decorator(caller, func) decorates a function using a caller.
    """
    if func is not None: # returns a decorated function
        return FunctionMaker.create(
            func, "return _call_(_func_, %(signature)s)",
            dict(_call_=caller, _func_=func), undecorated=func)
    else: # returns a decorator
        if isinstance(caller, partial):
            return partial(decorator, caller)
        # otherwise assume caller is a function
        f = inspect.getargspec(caller)[0][0] # first arg
        return FunctionMaker.create(
            '%s(%s)' % (caller.__name__, f), 
            'return decorator(_call_, %s)' % f,
            dict(_call_=caller, decorator=decorator), undecorated=caller,
            doc=caller.__doc__, module=caller.__module__)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# http://code.activestate.com/recipes/204197-solving-the-metaclass-conflict/
import inspect, types, builtins

############## preliminary: two utility functions #####################

def skip_redundant(iterable, skipset=None):
    "Redundant items are repeated items or items in the original skipset."
    if skipset is None: skipset = set()
    for item in iterable:
        if item not in skipset:
            skipset.add(item)
            yield item


def remove_redundant(metaclasses):
    skipset = set([type])
    for meta in metaclasses: # determines the metaclasses to be skipped
        skipset.update(inspect.getmro(meta)[1:])
    return tuple(skip_redundant(metaclasses, skipset))

##################################################################
## now the core of the module: two mutually recursive functions ##
##################################################################

memoized_metaclasses_map = {}

def get_noconflict_metaclass(bases, left_metas, right_metas):
     """Not intended to be used outside of this module, unless you know
     what you are doing."""
     # make tuple of needed metaclasses in specified priority order
     metas = left_metas + tuple(map(type, bases)) + right_metas
     needed_metas = remove_redundant(metas)

     # return existing confict-solving meta, if any
     if needed_metas in memoized_metaclasses_map:
       return memoized_metaclasses_map[needed_metas]
     # nope: compute, memoize and return needed conflict-solving meta
     elif not needed_metas:         # wee, a trivial case, happy us
         meta = type
     elif len(needed_metas) == 1: # another trivial case
        meta = needed_metas[0]
     # check for recursion, can happen i.e. for Zope ExtensionClasses
     elif needed_metas == bases: 
         raise TypeError("Incompatible root metatypes", needed_metas)
     else: # gotta work ...
         metaname = '_' + ''.join([m.__name__ for m in needed_metas])
         meta = classmaker()(metaname, needed_metas, {})
     memoized_metaclasses_map[needed_metas] = meta
     return meta

def classmaker(left_metas=(), right_metas=()):
    def make_class(name, bases, adict):
        metaclass = get_noconflict_metaclass(bases, left_metas, right_metas)
        return metaclass(name, bases, adict)
    return make_class

