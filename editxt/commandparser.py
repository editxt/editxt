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
"""
Command parser specification:

- Arguments are space-delimited.
- Arguments must be in order.
- Argument names must be valid Python identifiers.
- Some examples:

    CommandParser(
        Choice('selection all'),
        Choice(('forward', False), ('reverse', True), name='reverse'),
    )
    matches:
        'selection reverse' : selection = 'selection',  reverse = True
        'sel rev'           : selection = 'selection',  reverse = True
        's r'               : selection = 'selection',  reverse = True
        'all reverse'       : selection = 'all',        reverse = True
        'a f'               : selection = 'all',        reverse = False
        ''                  : selection = 'selection',  reverse = False

    CommandParser(
        Regex('regex'),
        Choice(('no-opt', False), ('opt', True), name='opt'),
        Int('num'),
    )
    matches:
        '/^abc$/ opt 123'
        '/^abc$/ o 123'
        '/^abc$/o 123'

- An arguments may be skipped by entering an extra space:

    CommandParser(
        Choice(('yes', True), ('no', False), name='bool'),
        Regex('regex'),
        Int('num', default=42),
    )
    matches:
        'y'         : bool = True, regex = None, num = 42
        ' /abc/ 1'  : bool = None, regex = re.compile('abc'), num = 1
        ' /abc/'    : bool = None, regex = re.compile('abc'), num = None
        '  1'  : bool = False, regex = None, num = 1
"""
import re


class CommandParser(object):
    """Text command parser

    :params *argspec: Argument specifiers.
    """

    def __init__(self, *argspec):
        self.argspec = argspec
        # TODO assert no duplicate arg names

    def parse(self, text):
        """Parse arguments from the given text

        :param text: Argument string.
        :raises: `ArgumentError` if the text string is invalid.
        :returns: `Options` object with argument values as attributes.
        """
        opts = Options()
        errors = []
        index = 0
        for arg in self.argspec:
            try:
                value, index = arg.consume(text, index)
            except ParseError as err:
                errors.append(err)
                index = err.parse_index
            else:
                setattr(opts, arg.name, value)
        if errors:
            msg = u'invalid arguments: {}'.format(text)
            raise ArgumentError(msg, opts, errors)
        if index < len(text):
            msg = u'unexpected argument(s): ' + text[index:]
            raise ArgumentError(msg, opts, errors)
        return opts

    def get_placeholder(self, text):
        """Get placeholder string to follow the given command text

        :param text: Argument string.
        :returns: A string of placeholder text, which can be used as a
            hint about remaining arguments to be entered.
        """
        index = 0
        args = iter(self.argspec)
        while index < len(text):
            arg = next(args, None)
            if arg is None:
                return ""
            try:
                value, index = arg.consume(text, index)
            except ParseError as err:
                return ""
        placeholder = " ".join(str(arg) for arg in args)
        if placeholder:
            if index > len(text) or (text and not text.endswith(" ")):
                placeholder = " " + placeholder
        return placeholder

    def get_completions(self, text):
        """Get completions for the argument being entered at index

        :param text: Argument string.
        :returns: A list of possible values for the argument at index.
        """
        index = 0
        args = iter(self.argspec)
        while index < len(text):
            arg = next(args, None)
            if arg is None:
                return []
            pre = index
            try:
                value, index = arg.consume(text, index)
            except ParseError as err:
                index = err.parse_index
            if index == len(text) and text[-1] != " ":
                args = iter([arg])
                index = pre
                break
        arg = next(args, None)
        if arg is None:
            return []
        return arg.get_completions(text[index:])


def tokenize(text):
    return text.split()


IDENTIFIER_PATTERN = re.compile('^[a-zA-Z_][a-zA-Z0-9_]*$')

def identifier(name):
    ident = name.replace('-', '_')
    if not IDENTIFIER_PATTERN.match(ident):
        raise ValueError('invalid name: %s' % name)
    return ident


class Type(object):
    """Base command argument type used to parse argument values"""

    def __init__(self, name, default=None):
        if not hasattr(self, 'args'):
            self.args = [name, default]
        if not hasattr(self, 'placeholder'):
            self.placeholder = name
        self.name = identifier(name)
        self.default = default

    def __eq__(self, other):
        if not issubclass(type(self), type(other)):
            return False
        return self.args == other.args

    def __str__(self):
        return self.placeholder

    def __repr__(self):
        argnames = self.__init__.im_func.func_code.co_varnames
        defaults = self.__init__.im_func.func_defaults
        assert argnames[0] == 'self', argnames
        assert len(self.args) == len(argnames) - 1, self.args
        args = []
        for name, default, value in zip(
                reversed(argnames), reversed(defaults), reversed(self.args)):
            if default != value:
                args.append('{}={!r}'.format(name, value))
        args.extend(repr(a) for a in reversed(self.args[:-len(defaults)]))
        return '{}({})'.format(type(self).__name__, ', '.join(reversed(args)))

    def consume(self, text, index):
        """Consume argument value from text starting at index

        This consumes the argument value plus a trailing space
        (if present).

        :param text: Text from which to consume argument value.
        :param index: Index into text from which to start consuming.
        :raises: ParseError if argument could not be consumed.
        :returns: A tuple `(<argument value>, <index>)` where `index` is
            that following the last consumed character in `text`.
            `index` is one more than the length of the given `text` if
            all remaining characters were consumed forming a valid token
            but the presence of any other character would extend the
            consumed token.
        """
        raise NotImplementedError("abstract method")

    def consume_token(self, text, index):
        """Helper method that consumes one token from text starting at index

        This consumes all text up to (including) the next space in the
        string. The returned token will not contain spaces. If the
        character at index is a space, then the argument should use its
        default value and the first element of the returned tuple will
        be `None`. This is meant to be called by subclasses; it is not
        part of the public interface.

        :param text: Argument string.
        :param index: Index from which to consume argument.
        :returns: A tuple `(<token string or None>, <index>)` where `index`
            is that following the last consumed character in `text`.
        """
        if index >= len(text):
            return None, index
        elif text[index] == ' ':
            return None, index + 1
        end = text.find(' ', index)
        if end < 0:
            token = text[index:]
            end = len(text)
        else:
            token = text[index:end]
            end += 1
        return token, end

    def get_completions(self, text):
        """Get argument value completions

        :param text: Argument value prefix.
        :returns: A list of possible completions for given prefix.
        """
        return []


class Choice(Type):
    """A multiple-choice argument type

    Choices are names without spaces. At least one choice name is
    required, more are usually provided.

    :param *choices: Two or more choice names or name/value pairs. Choices
    may be specified as a single space-delimited string, or one or more
    positional arguments consisting of either strings, or tuples in the
    form ("name-string", <value>). The value is the name in the case
    where name/value pairs are not given. The first choice is the
    default.
    :param name: Optional name, defaults to the first choice name. Must
    be specified as a keyword argument.
    """

    def __init__(self, *choices, **kw):
        self.args = choices
        self.kwargs = kw.copy()
        if len(choices) == 1 and isinstance(choices[0], basestring):
            choices = choices[0].split()
        if len(choices) < 2:
            raise ValueError('at least two choices are required')
        self.mapping = map = {}
        self.names = names = []
        self.alternates = alts = []
        for choice in choices:
            if isinstance(choice, basestring):
                if " " in choice:
                    name = choice
                    value = choice.split()[0]
                else:
                    name = value = choice
            else:
                try:
                    name, value = choice
                except (TypeError, ValueError):
                    raise ValueError("invalid choice: %r" % (choice,))
                if not isinstance(name, basestring):
                    raise ValueError("invalid choice name: %r" % (name,))
            for i, name in enumerate(name.split()):
                if i == 0:
                    names.append(name)
                else:
                    alts.append(name)
                if name in map:
                    raise ValueError("ambiguous name: %r" % (name,))
                map[name] = value
                for i in range(1, len(name)):
                    key = name[:i]
                    if key in names or key in alts:
                        raise ValueError("ambiguous name: %r" % (key,))
                    if key in map:
                        map.pop(key)
                    else:
                        map[key] = value
        self.placeholder = names[0]
        super(Choice, self).__init__(kw.pop('name', names[0]), map[names[0]])
        if kw:
            raise ValueError("unexpected arguments: %r" % (kw,))

    def __eq__(self, other):
        if not issubclass(type(self), type(other)):
            return False
        return self.args == other.args and self.kwargs == other.kwargs

    def __repr__(self):
        args = [repr(a) for a in self.args]
        args.extend('{}={!r}'.format(name, value)
                    for name, value in sorted(self.kwargs.iteritems()))
        return '{}({})'.format(type(self).__name__, ', '.join(args))

    def consume(self, text, index):
        """Consume a single choice name starting at index

        The token at index may be a complete choice name or a prefix
        that uniquely identifies any choice. Return the default (first)
        choice value if there is no token to consume.
        """
        token, end = self.consume_token(text, index)
        if token is None:
            return self.default, end
        if token in self.mapping:
            return self.mapping[token], end
        names = ', '.join(n for n in self.names if n.startswith(token))
        if names:
            msg = '{!r} is ambiguous: {}'.format(token, names)
        else:
            names = ', '.join(self.names)
            msg = '{!r} does not match any of: {}'.format(token, names)
        raise ParseError(msg, self, index, end)

    def get_completions(self, text):
        """List choice names that complete the given command text"""
        names = [n for n in self.names if n.startswith(text)]
        return names or [n for n in self.alternates if n.startswith(text)]


class Int(Type):

    def consume(self, text, index):
        token, end = self.consume_token(text, index)
        if token is None:
            return self.default, end
        try:
            return int(token), end
        except (ValueError, TypeError) as err:
            raise ParseError(str(err), self, index, end)


class String(Type):

    ESCAPES = {
        '\\': '\\',
        "'": "'",
        '"': '"',
        'a': '\a',
        'b': '\b',
        'f': '\f',
        'n': '\n',
        'r': '\r',
        't': '\t',
        'v': '\v',
    }

    def consume(self, text, index):
        if index >= len(text):
            return self.default, index
        if text[index] not in ['"', "'"]:
            return self.consume_token(text, index)
        delim = text[index]
        chars, esc = [], 0
        escapes = self.ESCAPES
        for i, c in enumerate(text[index + 1:]):
            if esc:
                esc = 0
                try:
                    chars.append(escapes[c])
                    continue
                except KeyError:
                    chars.append('\\')
            elif c == delim:
                if text[index + i + 2:index + i + 3] == ' ':
                    index += 1
                return ''.join(chars), index + i + 2
            if c == '\\':
                esc = 1
            else:
                chars.append(c)
        token = ''.join(chars)
        msg = 'unterminated string: {}{}'.format(delim, token)
        raise ParseError(msg, self, index, len(text))


class VarArgs(Type):
    """Consume all remaining arguments by splitting the string"""

    def __init__(self, name, placeholder=""):
        self.args = [name, placeholder]
        self.placeholder = placeholder
        super(VarArgs, self).__init__(name)

    def consume(self, text, index):
        return text[index:].split(), len(text)


class Regex(Type):

    NON_DELIMITERS = r'.^$*+?[]{}\()'
    WORDCHAR = re.compile(r'\w', re.UNICODE)

    def __init__(self, name, replace=False, default=None, flags=re.U | re.M):
        self.args = [name, replace, default, flags]
        self.replace = replace
        self.flags = flags
        default = (None, None) if replace and default is None else default
        super(Regex, self).__init__(name, default)

    def consume(self, text, index):
        if index >= len(text):
            return self.default, index
        no_delim = self.NON_DELIMITERS
        if text[index] in no_delim or self.WORDCHAR.match(text[index]):
            msg = "invalid search pattern: {!r}".format(text[index:])
            raise ParseError(msg, self, index, len(text) - index)
        expr, index = self.consume_expression(text, index)
        try:
            if self.replace:
                if index >= len(text):
                    index = len(text) + 1 # to show we would consume more
                    return (re.compile(expr, self.flags), self.default[1]), index
                repl, index = self.consume_expression(text, index - 1)
                flags, index = self.consume_flags(text, index)
                return (re.compile(expr, flags), repl), index
            flags, index = self.consume_flags(text, index)
            return re.compile(expr, flags), index
        except re.error as err:
            msg = "invalid regular expression: {}".format(err)
            raise ParseError(msg, self, index, index)

    def consume_expression(self, text, index):
        delim = text[index]
        chars, esc = [], 0
        i = -1
        for i, c in enumerate(text[index + 1:]):
            if esc:
                esc = 0
                if c == '\\':
                    chars.append(c)
                else:
                    chars.append('\\')
            elif c == delim:
                return ''.join(chars), index + i + 2
            if c == '\\':
                esc = 1
            else:
                chars.append(c)
        if not esc:
            return ''.join(chars), index + i + 3
        token = ''.join(chars)
        msg = 'unterminated regex: {}{}'.format(delim, token)
        raise ParseError(msg, self, index, len(text))

    def consume_flags(self, text, index):
        flags = {'i': re.IGNORECASE, 's': re.DOTALL, 'l': re.LOCALE}
        value = self.flags
        while index < len(text):
            char = text[index].lower()
            if char in flags:
                value |= flags[char]
            elif char == ' ':
                return value, index + 1
            else:
                c = text[index]
                msg = 'unknown flag: {}'.format(c)
                raise ParseError(msg, self, index, index)
            index += 1
        return value, index


class Options(object):
    """Parsed argument container

    Argument values are attributes.
    """

    def __init__(self, **opts):
        for name, value in opts.items():
            setattr(self, name, value)

    def __eq__(self, other):
        if not issubclass(type(other), type(self)):
            return False
        obj = Options().__dict__
        data = {k: v for k, v in self.__dict__.items() if k not in obj}
        othr = {k: v for k, v in other.__dict__.items() if k not in obj}
        return data == othr

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        obj = Options().__dict__
        vars = ['{}={!r}'.format(*kv)
            for kv in self.__dict__.items() if kv[0] not in obj]
        return '{}({})'.format(type(self).__name__, ', '.join(vars))


class Error(Exception):

    def __str__(self):
        return self.args[0]

    def __eq__(self, other):
        if not issubclass(type(other), type(self)):
            return False
        return self.args == other.args

    def __ne__(self, other):
        return not self.__eq__(other)


class ArgumentError(Error):

    def __str__(self):
        ext = ""
        if self.errors:
            ext = "\n" + "\n".join(str(err) for err in self.errors)
        return self.args[0] + ext

    @property
    def options(self):
        return self.args[1]

    @property
    def errors(self):
        return self.args[2]


class ParseError(Error):

    @property
    def arg(self):
        return self.args[1]

    @property
    def error_index(self):
        return self.args[2]

    @property
    def parse_index(self):
        return self.args[3]
