# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: ruby.js
name = 'Ruby'
file_patterns = ['*.ruby', '*.rb', '*.gemspec', '*.podspec', '*.thor', '*.irb']

keyword = """
    and false then defined module in return redo if BEGIN retry end for
    true self when next until do begin unless END rescue nil else break
    undef not super class case require yield alias while ensure elsif or
    include attr_reader attr_writer attr_accessor
    """.split()

doctag = [RE(r"@[A-Za-z]+")]

doctag0 = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text_color = DELIMITER
    rules = [
        ('doctag', doctag),
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag0),
    ]

class comment0:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag0),
    ]
comment0.__name__ = 'comment'

class _group0:
    default_text_color = DELIMITER
    rules = [('_group0', RE(r"^\s*=>"), [RE(r"\B|\b")])]

symbol = [RE(r"[a-zA-Z_]\w*(?:\!|\?)?:")]

number = [
    RE(r"(?:\b0[0-7_]+)|(?:\b0x[0-9a-fA-F_]+)|(?:\b[1-9][0-9_]*(?:\.[0-9_]+)?)|[0_]\b"),
]

class subst:
    default_text_color = DELIMITER
    rules = [('keyword', keyword)]

class string:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
        ('subst', RE(r"#\{"), [RE(r"}")], subst),
    ]

keyword0 = ['class', 'module']

title = [RE(r"[A-Za-z_]\w*(?:::\w+)*(?:\?|\!)?")]

class _group4:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '([a-zA-Z]\\w*::)?[a-zA-Z]\\w*'},
    ]

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword0),
        ('title', title),
        ('_group4', RE(r"<\s*"), [RE(r"\B\b")], _group4),
        None,  # rules[1],
        None,  # rules[2],
        None,  # rules[3],
    ]
class0.__name__ = 'class'

keyword1 = ['def']

title0 = [
    RE(r"[a-zA-Z_]\w*[!?=]?|[-+~]\@|<<|>>|=~|===?|<=>|[<>]=?|\*\*|[-/+%^&*~`|]|\[\]=?"),
]

class params:
    default_text_color = DELIMITER
    rules = [('keyword', keyword)]

class params0:
    default_text_color = DELIMITER
    rules = [('params', RE(r"\("), [RE(r"\)")], params)]
params0.__name__ = 'params'

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword1),
        ('title', title0),
        None,  # rules[1],
        None,  # rules[2],
        None,  # rules[3],
    ]

class symbol0:
    default_text_color = DELIMITER
    rules = [
        None,  # _group1.rules[0],
        None,  # _group1.rules[1],
        None,  # _group1.rules[2],
        None,  # _group1.rules[3],
        None,  # _group1.rules[4],
        None,  # _group1.rules[5],
        None,  # _group1.rules[6],
        None,  # _group1.rules[7],
        None,  # _group1.rules[8],
        None,  # _group1.rules[9],
        None,  # _group1.rules[10],
        None,  # _group1.rules[11],
        # ignore {'begin': '[a-zA-Z_]\\w*[!?=]?|[-+~]\\@|<<|>>|=~|===?|<=>|[<>]=?|\\*\\*|[-/+%^&*~`|]|\\[\\]=?'},
    ]
symbol0.__name__ = 'symbol'

class regexp:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
        None,  # string.rules[0],
    ]

class _group3:
    default_text_color = DELIMITER
    rules = [
        None,  # _group1.rules[12],
        ('regexp', RE(r"/"), [RE(r"/[a-z]*")], regexp),
        ('regexp', RE(r"%r{"), [RE(r"}[a-z]*")], regexp),
        ('regexp', RE(r"%r\("), [RE(r"\)[a-z]*")], regexp),
        ('regexp', RE(r"%r!"), [RE(r"![a-z]*")], regexp),
        ('regexp', RE(r"%r\["), [RE(r"\][a-z]*")], regexp),
        None,  # rules[1],
        None,  # rules[2],
        None,  # rules[3],
    ]

class _group1:
    default_text_color = DELIMITER
    rules = [
        ('string', RE(r"'"), [RE(r"'")], string),
        ('string', RE(r"\""), [RE(r"\"")], string),
        ('string', RE(r"`"), [RE(r"`")], string),
        ('string', RE(r"%[qQwWx]?\("), [RE(r"\)")], string),
        ('string', RE(r"%[qQwWx]?\["), [RE(r"\]")], string),
        ('string', RE(r"%[qQwWx]?{"), [RE(r"}")], string),
        ('string', RE(r"%[qQwWx]?<"), [RE(r">")], string),
        ('string', RE(r"%[qQwWx]?/"), [RE(r"/")], string),
        ('string', RE(r"%[qQwWx]?%"), [RE(r"%")], string),
        ('string', RE(r"%[qQwWx]?-"), [RE(r"-")], string),
        ('string', RE(r"%[qQwWx]?\|"), [RE(r"\|")], string),
        ('string', RE(r"\B\?(?:\\\d{1,3}|\\x[A-Fa-f0-9]{1,2}|\\u[A-Fa-f0-9]{4}|\\?\S)\b"), [RE(r"\B\b")], string),
        ('_group2', RE(r"#<"), [RE(r">")]),
        ('class', RE(r"\b(?:class|module)"), [RE(r"$|;")], class0),
        ('function', RE(r"\b(?:def)"), [RE(r"$|;"), params0], function),
        ('symbol', symbol),
        ('symbol', RE(r":"), [RE(r"\B\b")], symbol0),
        ('number', number),
        # ignore {'begin': '(\\$\\W)|((\\$|\\@\\@?)(\\w+))'},
        ('_group3', RE(r"(?:!|!=|!==|%|%=|&|&&|&=|\*|\*=|\+|\+=|,|-|-=|/=|/|:|;|<<|<<=|<=|<|===|==|=|>>>=|>>=|>=|>>>|>>|>|\?|\[|\{|\(|\^|\^=|\||\|=|\|\||~)\s*"), [RE(r"\B\b")], _group3),
        None,  # rules[1],
        None,  # rules[2],
        None,  # rules[3],
    ]

class meta:
    default_text_color = DELIMITER
    rules = [
        ('meta', RE(r"^(?:[>?]>|[\w#]+\(\w+\):\d+:\d+>|(?:\w+-)?\d+\.\d+\.\d(?:p\d+)?[^>]+>)"), [RE(r"\B|\b")]),
    ]

class _group5:
    default_text_color = DELIMITER
    rules = []

rules = [
    ('keyword', keyword),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('comment', RE(r"^\=begin"), [RE(r"^\=end")], comment),
    ('comment', RE(r"^__END__"), [RE(r"\n$")], comment0),
    ('_group0', _group0, [RE(r"$")], _group1),
    ('meta', meta, [RE(r"$")], _group5),
    _group1.rules[0],
    _group1.rules[1],
    _group1.rules[2],
    _group1.rules[3],
    _group1.rules[4],
    _group1.rules[5],
    _group1.rules[6],
    _group1.rules[7],
    _group1.rules[8],
    _group1.rules[9],
    _group1.rules[10],
    _group1.rules[11],
    _group1.rules[12],
    _group1.rules[13],
    _group1.rules[14],
    ('symbol', symbol),
    _group1.rules[16],
    ('number', number),
    # ignore {'begin': '(\\$\\W)|((\\$|\\@\\@?)(\\w+))'},
    _group1.rules[18],
    None,  # rules[1],
    None,  # rules[2],
    None,  # rules[3],
]

class0.rules[3] = rules[1]
class0.rules[4] = rules[2]
class0.rules[5] = rules[3]
function.rules[2] = rules[1]
function.rules[3] = rules[2]
function.rules[4] = rules[3]
symbol0.rules[0] = _group1.rules[0]
symbol0.rules[1] = _group1.rules[1]
symbol0.rules[2] = _group1.rules[2]
symbol0.rules[3] = _group1.rules[3]
symbol0.rules[4] = _group1.rules[4]
symbol0.rules[5] = _group1.rules[5]
symbol0.rules[6] = _group1.rules[6]
symbol0.rules[7] = _group1.rules[7]
symbol0.rules[8] = _group1.rules[8]
symbol0.rules[9] = _group1.rules[9]
symbol0.rules[10] = _group1.rules[10]
symbol0.rules[11] = _group1.rules[11]
regexp.rules[1] = string.rules[0]
_group3.rules[0] = _group1.rules[12]
_group3.rules[6] = rules[1]
_group3.rules[7] = rules[2]
_group3.rules[8] = rules[3]
_group1.rules[19] = rules[1]
_group1.rules[20] = rules[2]
_group1.rules[21] = rules[3]
rules[26] = rules[1]
rules[27] = rules[2]
rules[28] = rules[3]
subst.rules.extend(_group1.rules)
params.rules.extend(_group1.rules)
