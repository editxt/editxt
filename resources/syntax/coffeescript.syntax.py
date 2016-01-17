# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: coffeescript.js
name = 'CoffeeScript'
file_patterns = ['*.coffeescript', '*.coffee', '*.cson', '*.iced']

built_in = """
    npm require console print module global window document
    """.split()

keyword = """
    in if for while finally new do return else break catch instanceof
    throw try this switch continue typeof delete debugger super then
    unless until loop of by when and or is isnt not
    """.split()

number = ('number', [RE(r"\b(?:0b[01]+)")])

class number1:
    default_text_color = DELIMITER
    rules = [
        ('number', RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"), [RE(r"\B|\b")]),
    ]
number1.__name__ = 'number'

number2 = ('number', number1, [RE(r"(?:\s*/)?")])

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

string0 = ('string', RE(r"'''"), [RE(r"'''")], string)

string1 = ('string', RE(r"'"), [RE(r"'")], string)

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"#"), [RE(r"$")], comment)

class regexp:
    default_text_color = DELIMITER
    rules = [
        None, # subst0,
        comment0,
    ]

regexp0 = ('regexp', RE(r"///"), [RE(r"///")], regexp)

regexp1 = ('regexp', [RE(r"//[gim]*")])

regexp2 = ('regexp', [RE(r"\/(?![ *])(?:\\\/|.)*?\/[gim]*(?=\W|$)")])

_group3 = ('_group3', RE(r"`"), [RE(r"`")], 'javascript')

class subst:
    default_text_color = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', ['true', 'false', 'null', 'undefined', 'yes', 'no', 'on', 'off']),
        number,
        number2,
        string0,
        string1,
        None, # string3,
        None, # string4,
        regexp0,
        regexp1,
        regexp2,
        # ignore {'begin': '@[A-Za-z$_][0-9A-Za-z$_]*'},
        _group3,
    ]

subst0 = ('subst', RE(r"#\{"), [RE(r"}")], subst)

class string2:
    default_text_color = DELIMITER
    rules = [operator_escape, subst0]
string2.__name__ = 'string'

string3 = ('string', RE(r"\"\"\""), [RE(r"\"\"\"")], string2)

string4 = ('string', RE(r"\""), [RE(r"\"")], string2)

title = ('title', [RE(r"[A-Za-z$_][0-9A-Za-z$_]*")])

class _group4:
    default_text_color = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword),
        ('literal', ['true', 'false', 'null', 'undefined', 'yes', 'no', 'on', 'off']),
        number,
        number2,
        string0,
        string1,
        string3,
        string4,
        regexp0,
        regexp1,
        regexp2,
        # ignore {'begin': '@[A-Za-z$_][0-9A-Za-z$_]*'},
        _group3,
    ]

class params:
    default_text_color = DELIMITER
    rules = [('_group4', RE(r"\("), [RE(r"\)")], _group4)]

params0 = ('params', RE(r"(?=\([^\(])"), [RE(r"\B|\b")], params)

class function:
    default_text_color = DELIMITER
    rules = [title, params0]

class function1:
    default_text_color = DELIMITER
    rules = [params0]
function1.__name__ = 'function'

class _group5:
    default_text_color = DELIMITER
    rules = [
        ('function', RE(r"(?=(?:\(.*\))?\s*\B[-=]>)"), [RE(r"[-=]>")], function1),
    ]

class _group6:
    default_text_color = DELIMITER
    ends_with_parent = True
    rules = [('keyword', ['extends']), title]

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class']),
        ('_group6', RE(r"\b(?:extends)"), [RE(r"$")], _group6),
        title,
    ]
class0.__name__ = 'class'

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', ['true', 'false', 'null', 'undefined', 'yes', 'no', 'on', 'off']),
    number,
    number2,
    string0,
    string1,
    string3,
    string4,
    regexp0,
    regexp1,
    regexp2,
    # ignore {'begin': '@[A-Za-z$_][0-9A-Za-z$_]*'},
    _group3,
    ('comment', RE(r"###"), [RE(r"###")], comment),
    comment0,
    ('function', RE(r"(?=^\s*[A-Za-z$_][0-9A-Za-z$_]*\s*=\s*(?:\(.*\))?\s*\B[-=]>)"), [RE(r"[-=]>")], function),
    ('_group5', RE(r"[:\(,=]\s*"), [RE(r"\B|\b")], _group5),
    ('class', RE(r"\b(?:class)"), [RE(r"$")], class0),
    ('_group7', RE(r"(?=[A-Za-z$_][0-9A-Za-z$_]*:)"), [RE(r"(?=:)")]),
]

regexp.rules[0] = subst0
subst.rules[7] = string3
subst.rules[8] = string4