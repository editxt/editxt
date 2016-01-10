# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: kotlin.js
name = 'Kotlin'
file_patterns = ['*.kotlin']

keyword = """
    val var get set class trait object open private protected public
    final enum if else do while for when break continue throw try catch
    finally import package is as in return fun override default
    companion reified inline volatile transient native Byte Short Char
    Int Long Boolean Float Double Void Unit Nothing
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        ('doctag', [RE(r"@[A-Za-z]+")]),
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class comment1:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]
comment1.__name__ = 'comment'

comment2 = ('comment', RE(r"//"), [RE(r"$")], comment1)

comment3 = ('comment', RE(r"/\*"), [RE(r"\*/")], comment1)

class _function:
    default_text_color = DELIMITER
    rules = [('function', [RE(r"[(?:]|$")])]

title = ('title', [RE(r"[a-zA-Z_]\w*")])

class _group1:
    default_text_color = DELIMITER
    rules = [title]

class type0:
    default_text_color = DELIMITER
    rules = [('keyword', ['reified'])]
type0.__name__ = 'type'

class _type:
    default_text_color = DELIMITER
    rules = [('type', [RE(r":\s*")])]

class params:
    default_text_color = DELIMITER
    rules = [('keyword', keyword), ('type', _type, [RE(r"(?=\s*[=\)])")])]

class function0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        ('keyword', ['fun']),
        ('_group1', RE(r"(?=[a-zA-Z_]\w*\s*\()"), [RE(r"\B\b")], _group1),
        ('type', RE(r"<"), [RE(r">")], type0),
        ('params', RE(r"\("), [RE(r"\)")], params),
        comment2,
        comment3,
    ]
function0.__name__ = 'function'

class _class:
    default_text_color = DELIMITER
    rules = [('class', [RE(r"[:\{(?:]|$")])]

class _type0:
    default_text_color = DELIMITER
    rules = [('type', [RE(r"<")])]
_type0.__name__ = '_type'

class _type1:
    default_text_color = DELIMITER
    rules = [('type', [RE(r">")])]
_type1.__name__ = '_type'

class _type2:
    default_text_color = DELIMITER
    rules = [('type', [RE(r"[,:]\s*")])]
_type2.__name__ = '_type'

class class1:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class', 'trait']),
        title,
        ('type', _type0, [_type1]),
        ('type', _type2, [RE(r"(?=[<\(,]|$)")]),
    ]
class1.__name__ = 'class'

class _variable:
    default_text_color = DELIMITER
    rules = [('variable', [RE(r"\s*[=:$]")])]

class string:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")])]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('keyword', keyword),
    ('literal', ['true', 'false', 'null']),
    ('comment', RE(r"/\*\*"), [RE(r"\*/")], comment),
    comment2,
    comment3,
    ('type', RE(r"(?=<)"), [RE(r">")]),
    ('function', RE(r"(?=\b(?:fun))"), [_function], function0),
    ('class', RE(r"\b(?:class|trait)"), [_class], class1),
    ('variable', RE(r"\b(?:var|val)"), [_variable]),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('meta', RE(r"^#!/usr/bin/env"), [RE(r"$")]),
    ('number', number),
]
