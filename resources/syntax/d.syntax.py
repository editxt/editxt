# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: d.js
name = 'D'
file_patterns = ['*.d']

built_in = """
    bool cdouble cent cfloat char creal dchar delegate double dstring
    float function idouble ifloat ireal long real short string ubyte
    ucent uint ulong ushort wchar wstring
    """.split()

keyword = """
    abstract alias align asm assert auto body break byte case cast catch
    class const continue debug default delete deprecated do else enum
    export extern final finally for foreach foreach_reverse goto if
    immutable import in inout int interface invariant is lazy macro
    mixin module new nothrow out override package pragma private
    protected public pure ref return scope shared static struct super
    switch synchronized template this throw try typedef typeid typeof
    union unittest version void volatile while with __FILE__ __LINE__
    __gshared __thread __traits __DATE__ __EOF__ __TIME__ __TIMESTAMP__
    __VENDOR__ __VERSION__
    """.split()

literal = ['false', 'null', 'true']

string = [RE(r"x\"[\da-fA-F\s\n\r]*\"[cwd]?")]

number = [
    RE(r"\b(?:((?:0[xX](?:([\da-fA-F][\da-fA-F_]*|_[\da-fA-F][\da-fA-F_]*)\.(?:[\da-fA-F][\da-fA-F_]*|_[\da-fA-F][\da-fA-F_]*)|\.?(?:[\da-fA-F][\da-fA-F_]*|_[\da-fA-F][\da-fA-F_]*))[pP][+-]?(?:0|[1-9][\d_]*|\d[\d_]*|[\d_]+?\d))|(?:(0|[1-9][\d_]*|\d[\d_]*|[\d_]+?\d)(?:\.\d*|(?:[eE][+-]?(?:0|[1-9][\d_]*|\d[\d_]*|[\d_]+?\d)))|\d+\.(?:0|[1-9][\d_]*|\d[\d_]*|[\d_]+?\d)(?:0|[1-9][\d_]*|\d[\d_]*|[\d_]+?\d)|\.(?:0|[1-9][\d_]*)(?:[eE][+-]?(?:0|[1-9][\d_]*|\d[\d_]*|[\d_]+?\d))?))(?:[fF]|L|i|[fF]i|Li)?|(?:(0|[1-9][\d_]*)|0[bB][01_]+|0[xX](?:[\da-fA-F][\da-fA-F_]*|_[\da-fA-F][\da-fA-F_]*))(?:i|[fF]i|Li))"),
]

number0 = [
    RE(r"\b(?:(0|[1-9][\d_]*)|0[bB][01_]+|0[xX](?:[\da-fA-F][\da-fA-F_]*|_[\da-fA-F][\da-fA-F_]*))(?:L|u|U|Lu|LU|uL|UL)?"),
]

keyword0 = [RE(r"@[a-zA-Z_][a-zA-Z_\d]*")]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

class string0:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\([\'"\\?\\\\abfnrtv]|u[\\dA-Fa-f]{4}|[0-7]{1,3}|x[\\dA-Fa-f]{2}|U[\\dA-Fa-f]{8})|&[a-zA-Z\\d]{2,};', 'relevance': 0},
    ]
string0.__name__ = 'string'

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('comment', RE(r"\/\+"), [RE(r"\+\/")], comment),
    ('string', string),
    ('string', RE(r"\""), [RE(r"\"[cwd]?")], string0),
    ('string', RE(r"[rq]\""), [RE(r"\"[cwd]?")]),
    ('string', RE(r"`"), [RE(r"`[cwd]?")]),
    ('string', RE(r"q\"\{"), [RE(r"\}\"")]),
    ('number', number),
    ('number', number0),
    ('string', RE(r"'(?:\\(['\"\?\\abfnrtv]|u[\dA-Fa-f]{4}|[0-7]{1,3}|x[\dA-Fa-f]{2}|U[\dA-Fa-f]{8})|&[a-zA-Z\d]{2,};|.)"), [RE(r"'")]),
    ('meta', RE(r"^#!"), [RE(r"$")]),
    ('meta', RE(r"#(?:line)"), [RE(r"$")]),
    ('keyword', keyword0),
]
