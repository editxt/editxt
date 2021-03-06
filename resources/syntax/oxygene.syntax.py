# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: oxygene.js
name = 'Oxygene'
file_patterns = ['*.oxygene']

flags = re.IGNORECASE | re.MULTILINE

keyword = """
    abstract add and array as asc aspect assembly async begin break
    block by case class concat const copy constructor continue create
    default delegate desc distinct div do downto dynamic each else empty
    end ensure enum equals event except exit extension external false
    final finalize finalizer finally flags for forward from function
    future global group has if implementation implements implies in
    index inherited inline interface into invariants is iterator join
    locked locking loop matching method mod module namespace nested new
    nil not notify nullable of old on operator or order out override
    parallel params partial pinned private procedure property protected
    public queryable raise read readonly record reintroduce remove
    repeat require result reverse sealed select self sequence set shl
    shr skip static step soft take then to true try tuple type union
    unit unsafe until uses using var virtual raises volatile where while
    with write xor yield await mapped deprecated stdcall cdecl pascal
    register safecall overload library platform reference packed strict
    published autoreleasepool selector strong weak unretained
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"{"), [RE(r"}")], comment)

comment1 = ('comment', RE(r"\(\*"), [RE(r"\*\)")], comment)

comment2 = ('comment', RE(r"//"), [RE(r"$")], comment)

#class string:
#    default_text_color = DELIMITER
#    rules = [
#        # ignore {'begin': "''"},
#    ]

string0 = ('string', RE(r"'"), [RE(r"'")]) #, string)

string1 = ('string', [RE(r"(?:#\d+)+")])

class params:
    default_text_color = DELIMITER
    rules = [('keyword', keyword), string0, string1]

class function:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['function', 'constructor', 'destructor', 'procedure', 'method']),
        ('keyword', ['function', 'constructor', 'destructor', 'procedure', 'method']),
        ('title', [RE(r"[a-zA-Z]\w*")]),
        ('params', RE(r"\("), [RE(r"\)")], params),
        comment0,
        comment1,
    ]

function0 = ('function', RE(r"\b(?:function|constructor|destructor|procedure|method)"), [RE(r"[:;]")], function)

class class0:
    default_text_color = DELIMITER
    rules = [
        ('keyword', keyword),
        string0,
        string1,
        comment0,
        comment1,
        comment2,
        function0,
    ]
class0.__name__ = 'class'

rules = [
    ('keyword', keyword),
    comment0,
    comment1,
    comment2,
    string0,
    string1,
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
    function0,
    ('class', RE(r"=\bclass\b"), [RE(r"end;")], class0),
]
