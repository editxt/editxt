# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: java.js
name = 'Java'
file_patterns = ['*.java', '*.jsp']

keyword = """
    false synchronized int abstract float private char boolean static
    null if const for true while long strictfp finally protected import
    native final void enum else break transient catch instanceof byte
    super volatile case assert short package default double public try
    this switch continue throws protected public private
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': '\\w+@', 'type': 'RegExp'}, 'relevance': 0},
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

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

string0 = ('string', RE(r"'"), [RE(r"'")], string)

string1 = ('string', RE(r"\""), [RE(r"\"")], string)

class _class0:
    default_text_color = DELIMITER
    rules = [('_class', [RE(r"[{;=]")])]
_class0.__name__ = '_class'

title = ('title', [RE(r"[a-zA-Z_]\w*")])

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class', 'interface']),
        ('keyword', ['class', 'interface']),
        ('_group2', RE(r"\b(?:extends|implements)"), [RE(r"(?=[{;=])")]),
        title,
    ]
class0.__name__ = 'class'

class _function0:
    default_text_color = DELIMITER
    rules = [('_function', [RE(r"[{;=]")])]
_function0.__name__ = '_function'

class _group4:
    default_text_color = DELIMITER
    rules = [title]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class params:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        string0,
        string1,
        ('number', number),
        comment3,
    ]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        ('_group4', RE(r"(?=[a-zA-Z_]\w*\s*\()"), [RE(r"\B|\b")], _group4),
        ('params', RE(r"\("), [RE(r"\)")], params),
        comment2,
        comment3,
    ]

number1 = [
    RE(r"\b(?:0[bB](?:[01]+[01_]+[01]+|[01]+)|0[xX](?:[a-fA-F0-9]+[a-fA-F0-9_]+[a-fA-F0-9]+|[a-fA-F0-9]+)|(?:(?:[\d]+[\d_]+[\d]+|[\d]+)(?:\.(?:[\d]+[\d_]+[\d]+|[\d]+))?|\.(?:[\d]+[\d_]+[\d]+|[\d]+))(?:[eE][-+]?\d+)?)[lLfF]?"),
]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"/\*\*"), [RE(r"\*/")], comment),
    comment2,
    comment3,
    string0,
    string1,
    ('class', RE(r"\b(?:class|interface)"), [_class0], class0),
    ('_group3', RE(r"\b(?:new|throw|return|else)"), [RE(r"\B|\b")]),
    ('function', RE(r"(?=(?:[a-zA-Z_]\w*(?:<[a-zA-Z_]\w*>)?\s+)+[a-zA-Z_]\w*\s*\()"), [_function0], function),
    ('number', number1),
    ('meta', [RE(r"@[A-Za-z]+")]),
]