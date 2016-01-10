# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: thrift.js
name = 'Thrift'
file_patterns = ['*.thrift']

built_in = ['bool', 'byte', 'i16', 'i32', 'i64', 'double', 'string', 'binary']

keyword = """
    namespace const typedef struct enum service exception void oneway
    set list map required optional
    """.split()

class string:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")])]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class title0:
    default_text_color = DELIMITER
    rules = [('title', RE(r"[a-zA-Z]\w*"), [RE(r"\B|\b")])]
title0.__name__ = 'title'

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['struct', 'enum', 'service', 'exception']),
        ('title', title0, [RE(r"\B\b")]),
    ]
class0.__name__ = 'class'

class _group2:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['bool', 'byte', 'i16', 'i32', 'i64', 'double', 'string', 'binary']),
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', ['true', 'false']),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('class', RE(r"\b(?:struct|enum|service|exception)"), [RE(r"\{")], class0),
    ('_group2', RE(r"\b(?:set|list|map)\s*<"), [RE(r">")], _group2),
]
