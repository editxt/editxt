# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: cal.js
name = 'C/AL'
file_patterns = ['*.cal']

flags = re.IGNORECASE | re.MULTILINE

keyword = """
    div mod in and or not xor asserterror begin case do downto else end
    exit for if of repeat then to until while with var
    """.split()

#class string:
#    default_text_color = DELIMITER
#    rules = [
#        # ignore {'begin': {'pattern': "''", 'type': 'RegExp'}},
#    ]

string0 = ('string', RE(r"'"), [RE(r"'")]) #, string)

string1 = ('string', [RE(r"(?:#\d+)+")])

title = ('title', [RE(r"[a-zA-Z]\w*")])

class params:
    default_text_color = DELIMITER
    rules = [('keyword', keyword), string0, string1]

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['procedure']),
        ('keyword', ['procedure']),
        title,
        ('params', RE(r"\("), [RE(r"\)")], params),
        ('comment', RE(r"//"), [RE(r"$")], comment),
        ('comment', RE(r"\{"), [RE(r"\}")], comment),
        ('comment', RE(r"\(\*"), [RE(r"\*\)")], comment),
    ]

function0 = ('function', RE(r"\b(?:procedure)"), [RE(r"[:;]")], function)

class class0:
    default_text_color = DELIMITER
    rules = [title, function0]
class0.__name__ = 'class'

rules = [
    ('keyword', keyword),
    ('literal', ['false', 'true']),
    string0,
    string1,
    ('number', [RE(r"\b\d+(?:\.\d+)?(?:DT|D|T)")]),
    ('string', RE(r"\""), [RE(r"\"")]),
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
    ('class', RE(r"(?=OBJECT (?:Table|Form|Report|Dataport|Codeunit|XMLport|MenuSuite|Page|Query) (?:\d+) (?:[^\r\n]+))"), [RE(r"\B|\b")], class0),
    function0,
]
