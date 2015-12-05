# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: vbscript.js
name = 'VBScript'
file_patterns = ['*.vbscript', '*.vbs']

flags = re.IGNORECASE | re.MULTILINE

built_in = """
    lcase month vartype instrrev ubound setlocale getobject rgb getref
    string weekdayname rnd dateadd monthname now day minute isarray
    cbool round formatcurrency conversions csng timevalue second year
    space abs clng timeserial fixs len asc isempty maths dateserial atn
    timer isobject filter weekday datevalue ccur isdate instr datediff
    formatdatetime replace isnull right sgn array snumeric log cdbl hex
    chr lbound msgbox ucase getlocale cos cdate cbyte rtrim join hour
    oct typename trim strcomp int createobject loadpicture tan
    formatnumber mid scriptenginebuildversion scriptengine split
    scriptengineminorversion cint sin datepart ltrim sqr
    scriptenginemajorversion time derived eval date formatpercent exp
    inputbox left ascw chrw regexp server response request cstr err
    """.split()

keyword = """
    call class const dim do loop erase execute executeglobal exit for
    each next function if then else on error option explicit new private
    property let get public randomize redim rem select case set stop sub
    while wend with end to elseif is or xor and not class_initialize
    class_terminate default preserve in me byval byref step resume goto
    """.split()

literal = ['true', 'false', 'null', 'nothing', 'empty']

class string:
    default_text = DELIMITER
    rules = [
        # {'begin': '""'},
    ]

doctag = [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]

class comment:
    default_text = DELIMITER
    rules = [
        # {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', doctag),
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', literal),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('comment', RE(r"'"), [RE(r"$")], comment),
    ('number', number),
]

# TODO merge "word_groups" and "delimited_ranges" into "rules" in editxt.syntax
assert "__obj" not in globals()
assert "__fixup" not in globals()
def __fixup(obj):
    groups = []
    ranges = []
    rules = getattr(obj, "rules", [])
    for i, rng in reversed(list(enumerate(rules))):
        if len(rng) == 2:
            groups.append(rng)
        else:
            assert len(rng) > 2, rng
            ranges.append(rng)
    return groups, ranges

class __obj:
    rules = globals().get("rules", [])
word_groups, delimited_ranges = __fixup(__obj)

for __obj in globals().values():
    if hasattr(__obj, "rules"):
        __obj.word_groups, __obj.delimited_ranges = __fixup(__obj)

del __obj, __fixup
