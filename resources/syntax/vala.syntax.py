# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: vala.js
name = 'Vala'
file_patterns = ['*.vala']

built_in = ['DBus', 'GLib', 'CCode', 'Gee', 'Object']

keyword = """
    char uchar unichar int uint long ulong short ushort int8 int16 int32
    int64 uint8 uint16 uint32 uint64 float double bool struct enum
    string void weak unowned owned async signal static abstract
    interface override while do for foreach else switch case break
    default return try catch public private protected internal using new
    this get set const stdout stdin stderr var
    """.split()

literal = ['false', 'true', 'null']

class _class:
    default_text_color = DELIMITER
    rules = [('_class', [RE(r"{")])]

keyword0 = ['class', 'interface', 'delegate', 'namespace']

title = [RE(r"[a-zA-Z_]\w*")]

class class0:
    default_text_color = DELIMITER
    rules = [('keyword', keyword0), ('title', title)]
class0.__name__ = 'class'

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('class', RE(r"\b(?:class|interface|delegate|namespace)"), [_class], class0),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('string', RE(r"\"\"\""), [RE(r"\"\"\"")]),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('meta', RE(r"^#"), [RE(r"$")]),
]
