# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: cs.js
name = 'C#'
file_patterns = ['*.cs', '*.csharp']

keyword = """
    abstract as base bool break byte case catch char checked const
    continue decimal dynamic default delegate do double else enum event
    explicit extern false finally fixed float for foreach goto if
    implicit in int interface internal is lock long null when object
    operator out override params private protected public readonly ref
    sbyte sealed short sizeof stackalloc static string struct switch
    this true try typeof uint ulong unchecked unsafe ushort using
    virtual volatile void while async protected public private internal
    ascending descending from get group into join let orderby partial
    select set value var where yield
    """.split()

doctag = [RE(r"///")]

doctag0 = [RE(r"<!--|-->")]

doctag1 = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        ('doctag', doctag),
        ('doctag', doctag0),
        ('doctag', RE(r"</?"), [RE(r">")]),
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag1),
    ]

class comment0:
    default_text_color = DELIMITER
    rules = [
        # ('contains', 0, 'contains', 1) {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag1),
    ]
comment0.__name__ = 'comment'

meta_keyword = """
    if else elif endif define undef warning error line region endregion
    pragma checksum
    """.split()

class meta:
    default_text_color = DELIMITER
    rules = [('meta-keyword', meta_keyword)]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '""'},
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

keyword0 = ['class', 'interface']

title = [RE(r"[a-zA-Z]\w*")]

class _group0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('title', title),
        None,  # rules[2],
        None,  # rules[3],
    ]

keyword1 = ['namespace']

title0 = [RE(r"[a-zA-Z](?:\.?\w)*")]

class _group1:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword1),
        ('title', title0),
        None,  # rules[2],
        None,  # rules[3],
    ]

class _function:
    default_text_color = DELIMITER
    rules = [('_function', [RE(r"[{;=]")])]

class _group3:
    default_text_color = DELIMITER
    rules = [('title', title)]

class _params:
    default_text_color = DELIMITER
    rules = [('_params', [RE(r"\(")])]

class _params0:
    default_text_color = DELIMITER
    rules = [('_params', [RE(r"\)")])]
_params0.__name__ = '_params'

class params:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        None,  # rules[6],
        None,  # rules[7],
        ('number', number),
        None,  # rules[3],
    ]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        ('_group3', RE(r"(?=[a-zA-Z]\w*\s*\()"), [RE(r"\B\b")], _group3),
        ('params', _params, [_params0], params),
        None,  # rules[2],
        None,  # rules[3],
    ]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"(?=///)"), [RE(r"$")], comment),
    ('comment', RE(r"//"), [RE(r"$")], comment0),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment0),
    ('meta', RE(r"#"), [RE(r"$")], meta),
    ('string', RE(r"@\""), [RE(r"\"")], string),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('_group0', RE(r"\b(?:class|interface)"), [RE(r"[{;=]")], _group0),
    ('_group1', RE(r"\b(?:namespace)"), [RE(r"[{;=]")], _group1),
    ('_group2', RE(r"\b(?:new|return|throw|await)"), [RE(r"\B\b")]),
    ('function', RE(r"(?=(?:[a-zA-Z]\w*(?:<[a-zA-Z]\w*>)?\s+)+[a-zA-Z]\w*\s*\()"), [_function], function),
]

_group0.rules[2] = rules[2]
_group0.rules[3] = rules[3]
_group1.rules[2] = rules[2]
_group1.rules[3] = rules[3]
params.rules[1] = rules[6]
params.rules[2] = rules[7]
params.rules[4] = rules[3]
function.rules[3] = rules[2]
function.rules[4] = rules[3]
