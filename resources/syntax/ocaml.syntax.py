# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: ocaml.js
name = 'OCaml'
file_patterns = ['*.ocaml', '*.ml']

built_in = """
    array bool bytes char exn float int int32 int64 list lazy_t
    nativeint string unit in_channel out_channel ref
    """.split()

keyword = """
    and as assert asr begin class constraint do done downto else end
    exception external for fun function functor if in include inherit!
    inherit initializer land lazy let lor lsl lsr lxor match method!
    method mod module mutable new object of open! open or private rec
    sig struct then to try type val! val virtual when while with parser
    value
    """.split()

literal = ['true', 'false']

literal0 = [RE(r"\[(?:\|\|)?\]|\(\)")]

symbol = [RE(r"'[A-Za-z_](?!')[\w']*")]

type = [RE(r"`[A-Z][\w']*")]

type0 = [RE(r"\b[A-Z][\w']*")]

number = [
    RE(r"\b(?:0[xX][a-fA-F0-9_]+[Lln]?|0[oO][0-7_]+[Lln]?|0[bB][01_]+[Lln]?|[0-9][0-9_]*(?:[Lln]|(?:\.[0-9_]*)?(?:[eE][-+]?[0-9_]+)?)?)"),
]

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

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('literal', literal0),
    ('comment', RE(r"\(\*"), [RE(r"\*\)")], comment),
    ('symbol', symbol),
    ('type', type),
    ('type', type0),
    # ignore {'begin': "[a-z_]\\w*'[\\w']*", 'relevance': 0},
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    # ignore {'begin': {'pattern': '[-=]>', 'type': 'RegExp'}},
]
