# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: aspectj.js
name = 'AspectJ'
file_patterns = ['*.aspectj']

keyword = """
    false synchronized int abstract float private char boolean static
    null if const for true while long throw strictfp finally protected
    import native final return void enum else extends implements break
    transient new catch instanceof byte super volatile case assert short
    package default double public try this switch continue throws
    privileged aspectOf adviceexecution proceed cflowbelow cflow
    initialization preinitialization staticinitialization withincode
    target within execution getWithinTypeName handler thisJoinPoint
    thisJoinPointStaticPart thisEnclosingJoinPointStaticPart declare
    parents warning error soft precedence thisAspectInstance
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

keyword2 = """
    false synchronized int abstract float private char boolean static
    null if const for true while long throw strictfp finally protected
    import native final return void enum else extends implements break
    transient new catch instanceof byte super volatile case assert short
    package default double public try this switch continue throws
    privileged aspectOf adviceexecution proceed cflowbelow cflow
    initialization preinitialization staticinitialization withincode
    target within execution getWithinTypeName handler thisJoinPoint
    thisJoinPointStaticPart thisEnclosingJoinPointStaticPart declare
    parents warning error soft precedence thisAspectInstance get set
    args call
    """.split()

class _group3:
    default_text_color = DELIMITER
    rules = [('keyword', keyword2)]

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['aspect']),
        ('_group2', RE(r"\b(?:extends|implements|pertypewithin|perthis|pertarget|percflowbelow|percflow|issingleton)"), [RE(r"(?=[{;=])")]),
        title,
        ('_group3', RE(r"\([^\)]*"), [RE(r"[)]+")], _group3),
    ]
class0.__name__ = 'class'

class class2:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class', 'interface']),
        ('keyword', ['class', 'interface']),
        ('_group4', RE(r"\b(?:extends|implements)"), [RE(r"(?=[{;=])")]),
        title,
    ]
class2.__name__ = 'class'

class _group6:
    default_text_color = DELIMITER
    rules = [title]

class _group5:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['pointcut', 'after', 'before', 'around', 'throwing', 'returning']),
        ('_group6', RE(r"(?=[a-zA-Z_]\w*\s*\()"), [RE(r"\B|\b")], _group6),
    ]

class _group8:
    default_text_color = DELIMITER
    rules = [('keyword', keyword2)]

class _group7:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        ('_group8', RE(r"[a-zA-Z_]\w*\s*\("), [RE(r"(?=[{;])")], _group8),
        string1,
    ]

class _function0:
    default_text_color = DELIMITER
    rules = [('_function', [RE(r"[{;=]")])]
_function0.__name__ = '_function'

class _group10:
    default_text_color = DELIMITER
    rules = [title]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

number0 = ('number', number)

class params:
    default_text_color = DELIMITER
    rules = [('keyword', keyword), string0, string1, number0, comment3]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        ('_group10', RE(r"(?=[a-zA-Z_]\w*\s*\()"), [RE(r"\B|\b")], _group10),
        ('params', RE(r"\("), [RE(r"\)")], params),
        comment2,
        comment3,
    ]

rules = [
    ('keyword', keyword),
    ('comment', RE(r"/\*\*"), [RE(r"\*/")], comment),
    comment2,
    comment3,
    string0,
    string1,
    ('class', RE(r"\b(?:aspect)"), [_class0], class0),
    ('class', RE(r"\b(?:class|interface)"), [_class0], class2),
    ('_group5', RE(r"\b(?:pointcut|after|before|around|throwing|returning)"), [RE(r"[)]")], _group5),
    ('_group7', RE(r"(?=[:])"), [RE(r"[{;]")], _group7),
    ('_group9', RE(r"\b(?:new|throw)"), [RE(r"\B|\b")]),
    ('function', RE(r"(?=\w+ +\w+(?:\.)?\w+\s*\([^\)]*\)\s*(?:(?:throws)[\w\s,]+)?[\{;])"), [_function0], function),
    number0,
    ('meta', [RE(r"@[A-Za-z]+")]),
]
