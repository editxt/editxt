# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: lua.js
name = 'Lua'
file_patterns = ['*.lua']

built_in = """
    _G _VERSION assert collectgarbage dofile error getfenv getmetatable
    ipairs load loadfile loadstring module next pairs pcall print
    rawequal rawget rawset require select setfenv setmetatable tonumber
    tostring type unpack xpcall coroutine debug io math os package
    string table
    """.split()

keyword = """
    and break do else elseif end false for if in local nil not or repeat
    return then true until while
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"--(?!\[=*\[)"), [RE(r"$")], comment)

#class _group1:
#    default_text_color = DELIMITER
#    rules = []

_group10 = ('_group1', RE(r"\[=*\["), [RE(r"\]=*\]")]) #, _group1)

class comment1:
    default_text_color = DELIMITER
    rules = [
        _group10,
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]
comment1.__name__ = 'comment'

comment2 = ('comment', RE(r"--\[=*\["), [RE(r"\]=*\]")], comment1)

class params:
    default_text_color = DELIMITER
    ends_with_parent = True
    rules = [comment0, comment2]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['function']),
        ('title', [RE(r"(?:[_a-zA-Z]\w*\.)*(?:[_a-zA-Z]\w*:)?[_a-zA-Z]\w*")]),
        ('params', RE(r"\("), [RE(r"(?=\))")], params),
        comment0,
        comment2,
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

operator_escape = ('operator.escape', [RE(r"\\[\s\S]")])

class string:
    default_text_color = DELIMITER
    rules = [operator_escape]

class string2:
    default_text_color = DELIMITER
    rules = [_group10]
string2.__name__ = 'string'

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    comment0,
    comment2,
    ('function', RE(r"\b(?:function)"), [RE(r"\)")], function),
    ('number', number),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('string', RE(r"\[=*\["), [RE(r"\]=*\]")], string2),
]
