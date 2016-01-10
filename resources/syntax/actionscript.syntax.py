# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: actionscript.js
name = 'ActionScript'
file_patterns = ['*.actionscript', '*.as']

keyword = """
    as break case catch class const continue default delete do dynamic
    each else extends final finally for function get if implements
    import in include instanceof interface internal is namespace native
    new override package private protected public return set static
    super switch this throw try typeof use var void while with
    """.split()

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

string0 = ('string', RE(r"'"), [RE(r"'")], string)

string1 = ('string', RE(r"\""), [RE(r"\"")], string)

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"//"), [RE(r"$")], comment)

comment1 = ('comment', RE(r"/\*"), [RE(r"\*/")], comment)

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

title = ('title', [RE(r"[a-zA-Z]\w*")])

class class0:
    default_text_color = DELIMITER
    rules = [('keyword', ['package']), title]
class0.__name__ = 'class'

class _class:
    default_text_color = DELIMITER
    rules = [('class', [RE(r"{")])]

class class3:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class', 'interface']),
        ('_group1', RE(r"\b(?:extends|implements)"), [RE(r"\B\b")]),
        title,
    ]
class3.__name__ = 'class'

class meta:
    default_text_color = DELIMITER
    rules = [
        ('meta-keyword', ['import', 'include']),
        ('keyword', ['import', 'include']),
    ]

class _function:
    default_text_color = DELIMITER
    rules = [('function', [RE(r"[{;]")])]

class params:
    default_text_color = DELIMITER
    rules = [
        string0,
        string1,
        comment0,
        comment1,
        ('rest_arg', RE(r"[.]{3}"), [RE(r"[a-zA-Z_$][a-zA-Z0-9_$]*")]),
    ]

class function0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['function']),
        title,
        ('params', RE(r"\("), [RE(r"\)")], params),
        # ignore {'begin': ':\\s*([*]|[a-zA-Z_$][a-zA-Z0-9_$]*)'},
    ]
function0.__name__ = 'function'

rules = [
    ('keyword', keyword),
    ('literal', ['true', 'false', 'null', 'undefined']),
    string0,
    string1,
    comment0,
    comment1,
    ('number', number),
    ('class', RE(r"\b(?:package)"), [RE(r"{")], class0),
    ('class', RE(r"\b(?:class|interface)"), [_class], class3),
    ('meta', RE(r"\b(?:import|include)"), [RE(r";")], meta),
    ('function', RE(r"\b(?:function)"), [_function], function0),
]
