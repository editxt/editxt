# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: elm.js
name = 'Elm'
file_patterns = ['*.elm']

keyword = """
    let in if then else case of where module import exposing type alias
    as infix infixl infixr port
    """.split()

title = [RE(r"^[_a-z][\w']*")]

keyword0 = ['module', 'where']

keyword1 = ['module']

type = [RE(r"\b[A-Z][\w]*(?:\((?:\.\.|,|\w+)\))?")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class _group5:
    default_text_color = DELIMITER
    rules = [
        ('type', type),
        ('comment', RE(r"--"), [RE(r"$")], comment),
        ('comment', RE(r"{-"), [RE(r"-}")], comment),
    ]

class _group0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('keyword', keyword1),
        ('_group5', RE(r"\("), [RE(r"\)")], _group5),
        _group5.rules[1],
        _group5.rules[2],
    ]

keyword2 = ['import', 'as', 'exposing']

class _group1:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword2),
        _group0.rules[2],
        _group5.rules[1],
        _group5.rules[2],
    ]

keyword3 = ['type', 'alias']

type0 = [RE(r"\b[A-Z][\w']*")]

class _group6:
    default_text_color = DELIMITER
    rules = []

class _group2:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword3),
        ('type', type0),
        _group0.rules[2],
        ('_group6', RE(r"{"), [RE(r"}")], _group6),
        _group5.rules[1],
        _group5.rules[2],
    ]

keyword4 = ['infix', 'infixl', 'infixr']

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class _group3:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword4),
        ('number', number),
        _group5.rules[1],
        _group5.rules[2],
    ]

keyword5 = ['port']

class _group4:
    default_text_color = DELIMITER
    rules = [('keyword', keyword5), _group5.rules[1], _group5.rules[2]]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

rules = [
    ('keyword', keyword),
    ('_group0', RE(r"\b(?:module)"), [RE(r"where")], _group0),
    ('_group1', RE(r"import"), [RE(r"$")], _group1),
    ('_group2', RE(r"type"), [RE(r"$")], _group2),
    ('_group3', RE(r"\b(?:infix|infixl|infixr)"), [RE(r"$")], _group3),
    ('_group4', RE(r"port"), [RE(r"$")], _group4),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('type', type0),
    ('title', title),
    _group5.rules[1],
    _group5.rules[2],
    # ignore {'begin': '->|<-'},
]
