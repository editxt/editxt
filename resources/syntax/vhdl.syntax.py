# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: vhdl.js
name = 'VHDL'
file_patterns = ['*.vhdl']

flags = re.IGNORECASE | re.MULTILINE

built_in = """
    boolean bit character severity_level integer time delay_length
    natural positive string bit_vector file_open_kind file_open_status
    std_ulogic std_ulogic_vector std_logic std_logic_vector unsigned
    signed boolean_vector integer_vector real_vector time_vector
    """.split()

keyword = """
    abs access after alias all and architecture array assert attribute
    begin block body buffer bus case component configuration constant
    context cover disconnect downto default else elsif end entity exit
    fairness file for force function generate generic group guarded if
    impure in inertial inout is label library linkage literal loop map
    mod nand new next nor not null of on open or others out package port
    postponed procedure process property protected pure range record
    register reject release rem report restrict restrict_guarantee
    return rol ror select sequence severity shared signal sla sll sra
    srl strong subtype then to transport type unaffected units until use
    variable vmode vprop vunit wait when while with xnor xor
    """.split()

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

number = [
    RE(r"\b(?:\d(?:_|\d)*#\w+(?:\.\w+)?#(?:[eE][-+]?\d(?:_|\d)*)?|\d(?:_|\d)*(?:\.\d(?:_|\d)*)?(?:[eE][-+]?\d(?:_|\d)*)?)"),
]

class literal:
    default_text_color = DELIMITER
    rules = [
        # ('contains', 2, 'contains', 0) {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

class symbol:
    default_text_color = DELIMITER
    rules = [
        # ('contains', 2, 'contains', 0) {'begin': '\\\\[\\s\\S]', 'relevance': 0},
    ]

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('comment', RE(r"--"), [RE(r"$")], comment),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', number),
    ('literal', RE(r"'(?:U|X|0|1|Z|W|L|H|-)'"), [RE(r"\B\b")], literal),
    ('symbol', RE(r"'[A-Za-z](?:_?[A-Za-z0-9])*"), [RE(r"\B\b")], symbol),
]
