# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: protobuf.js
name = 'Protocol Buffers'
file_patterns = ['*.protobuf']

built_in = """
    double float int32 int64 uint32 uint64 sint32 sint64 fixed32 fixed64
    sfixed32 sfixed64 bool string bytes
    """.split()

keyword = """
    package import option optional required repeated group
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
        ('keyword', ['message', 'enum', 'service']),
        ('title', title0, [RE(r"(?=\{)")]),
    ]
class0.__name__ = 'class'

class _function0:
    default_text_color = DELIMITER
    rules = [('_function', [RE(r";")])]
_function0.__name__ = '_function'

class function:
    default_text_color = DELIMITER
    rules = [('keyword', ['rpc', 'returns']), ('keyword', ['rpc'])]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', ['true', 'false']),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('class', RE(r"\b(?:message|enum|service)"), [RE(r"\{")], class0),
    ('function', RE(r"\b(?:rpc)"), [_function0], function),
    ('_group2', RE(r"^\s*[A-Z_]+"), [RE(r"\s*=")]),
]
