# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: ceylon.js
name = 'Ceylon'
file_patterns = ['*.ceylon']

keyword = """
    assembly module package import alias class interface object given
    value assign void function new of extends satisfies abstracts in out
    return break continue throw assert dynamic if else switch case for
    while try catch finally then let this outer super is exists nonempty
    shared abstract formal default actual variable late native
    deprecatedfinal sealed annotation suppressWarnings small
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

string = ('string', RE(r"\"\"\""), [RE(r"\"\"\"")])

class _subst:
    default_text_color = DELIMITER
    rules = [('subst', [RE(r"``")])]

keyword1 = """
    assembly module package import alias class interface object given
    value assign void function new of extends satisfies abstracts in out
    return break continue throw assert dynamic if else switch case for
    while try catch finally then let this outer super is exists nonempty
    """.split()

string0 = ('string', RE(r"'"), [RE(r"'")])

number = [
    RE(r"#[0-9a-fA-F_]+|\$[01_]+|[0-9_]+(?:\.[0-9_](?:[eE][+-]?\d+)?)?[kMGTPmunpf]?"),
]

number0 = ('number', number)

class subst0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword1),
        string,
        None, # string2,
        string0,
        number0,
    ]
subst0.__name__ = 'subst'

class string1:
    default_text_color = DELIMITER
    rules = [('subst', _subst, [_subst], subst0)]
string1.__name__ = 'string'

string2 = ('string', RE(r"\""), [RE(r"\"")], string1)

rules = [
    ('keyword', keyword),
    ('meta', ['doc', 'by', 'license', 'see', 'throws', 'tagged']),
    ('comment', RE(r"//"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('meta', [RE(r"@[a-z]\w*(?:\:\"[^\"]*\")?")]),
    string,
    string2,
    string0,
    number0,
]

subst0.rules[2] = string2
