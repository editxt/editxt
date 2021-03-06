# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: tp.js
name = 'TP'
file_patterns = ['*.tp']

keyword = """
    ABORT ACC ADJUST AND AP_LD BREAK CALL CNT COL CONDITION CONFIG DA DB
    DIV DETECT ELSE END ENDFOR ERR_NUM ERROR_PROG FINE FOR GP GUARD INC
    IF JMP LINEAR_MAX_SPEED LOCK MOD MONITOR OFFSET Offset OR OVERRIDE
    PAUSE PREG PTH RT_LD RUN SELECT SKIP Skip TA TB TO TOOL_OFFSET
    Tool_Offset UF UT UFRAME_NUM UTOOL_NUM UNLOCK WAIT X Y Z W P R
    STRLEN SUBSTR FINDSTR VOFFSET PROG ATTR MN POS
    """.split()

literal = """
    ON OFF max_speed LPOS JPOS ENABLE DISABLE START STOP RESET
    """.split()

number = ('number', [RE(r"[1-9][0-9]*")])

symbol = ('symbol', [RE(r":[^\]]+")])

class built_in:
    default_text_color = DELIMITER
    rules = [number, symbol]

class string:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")])]

string0 = ('string', RE(r"\""), [RE(r"\"")], string)

class built_in1:
    default_text_color = DELIMITER
    rules = [number, string0, symbol]
built_in1.__name__ = 'built_in'

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

number1 = [
    RE(r"(?:\b0[xX][a-fA-F0-9]+|(?:\b\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)"),
]

rules = [
    ('keyword', keyword),
    ('literal', literal),
    ('built_in', RE(r"(?:AR|P|PAYLOAD|PR|R|SR|RSR|LBL|VR|UALM|MESSAGE|UTOOL|UFRAME|TIMER|    TIMER_OVERFLOW|JOINT_MAX_SPEED|RESUME_PROG|DIAG_REC)\["), [RE(r"\]")], built_in),
    ('built_in', RE(r"(?:AI|AO|DI|DO|F|RI|RO|UI|UO|GI|GO|SI|SO)\["), [RE(r"\]")], built_in1),
    ('keyword', [RE(r"/(?:PROG|ATTR|MN|POS|END)\b")]),
    ('keyword', [RE(r"(?:CALL|RUN|POINT_LOGIC|LBL)\b")]),
    ('keyword', [RE(r"\b(?:ACC|CNT|Skip|Offset|PSPD|RT_LD|AP_LD|Tool_Offset)")]),
    ('number', [RE(r"\d+(?:sec|msec|mm/sec|cm/min|inch/min|deg/sec|mm|in|cm)?\b")]),
    ('comment', RE(r"//"), [RE(r"[;$]")], comment),
    ('comment', RE(r"!"), [RE(r"[;$]")], comment),
    ('comment', RE(r"--eg:"), [RE(r"$")], comment),
    string0,
    ('string', RE(r"'"), [RE(r"'")]),
    ('number', number1),
    ('variable', [RE(r"\$[A-Za-z0-9_]+")]),
]
