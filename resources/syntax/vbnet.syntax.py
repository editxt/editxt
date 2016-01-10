# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: vbnet.js
name = 'VB.NET'
file_patterns = ['*.vbnet', '*.vb']

flags = re.IGNORECASE | re.MULTILINE

built_in = """
    boolean byte cbool cbyte cchar cdate cdec cdbl char cint clng cobj
    csbyte cshort csng cstr ctype date decimal directcast double gettype
    getxmlnamespace iif integer long object sbyte short single string
    trycast typeof uinteger ulong ushort
    """.split()

keyword = """
    addhandler addressof alias and andalso aggregate ansi as assembly
    auto binary by byref byval call case catch class compare const
    continue custom declare default delegate dim distinct do each equals
    else elseif end enum erase error event exit explicit finally for
    friend from function get global goto group handles if implements
    imports in inherits interface into is isfalse isnot istrue join key
    let lib like loop me mid mod module mustinherit mustoverride mybase
    myclass namespace narrowing new next not notinheritable
    notoverridable of off on operator option optional or order orelse
    overloads overridable overrides paramarray partial preserve private
    property protected public raiseevent readonly redim rem
    removehandler resume return select set shadows shared skip static
    step stop structure strict sub synclock take text then throw to try
    unicode until using when where while widening with withevents
    writeonly xor
    """.split()

#class string:
#    default_text_color = DELIMITER
#    rules = [
#        # ignore {'begin': '""'},
#    ]

#class doctag:
#    default_text_color = DELIMITER
#    rules = [
#        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
#    ]

class comment:
    default_text_color = DELIMITER
    rules = [
        ('doctag', RE(r"'''|<!--|-->"), [RE(r"\B\b")]), #, doctag),
        ('doctag', RE(r"</?"), [RE(r">")]), #, doctag),
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

number = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

class meta:
    default_text_color = DELIMITER
    rules = [
        ('meta-keyword', ['if', 'else', 'elseif', 'end', 'region', 'externalsource']),
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('literal', ['true', 'false', 'nothing']),
    ('string', RE(r"\""), [RE(r"\"")]), #, string),
    ('comment', RE(r"(?=')"), [RE(r"$")], comment),
    ('number', number),
    ('meta', RE(r"#"), [RE(r"$")], meta),
]
