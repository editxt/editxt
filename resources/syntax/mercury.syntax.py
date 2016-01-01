# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: mercury.js
name = 'Mercury'
file_patterns = ['*.mercury', '*.m', '*.moo']

built_in = """
    some all not if then else true fail false try catch catch_any
    semidet_true semidet_false semidet_fail impure_true impure semipure
    """.split()

keyword = """
    module use_module import_module include_module end_module initialise
    mutable initialize finalize finalise interface implementation pred
    mode func type inst solver any_pred any_func is semidet det nondet
    multi erroneous failure cc_nondet cc_multi typeclass instance where
    pragma promise external trace atomic or_else require_complete_switch
    require_det require_semidet require_multi require_nondet
    require_cc_multi require_cc_nondet require_erroneous require_failure
    """.split()

meta = """
    inline no_inline type_spec source_file fact_table obsolete memo
    loop_check minimal_model terminates does_not_terminate
    check_termination promise_equivalent_clauses foreign_proc
    foreign_decl foreign_code foreign_type foreign_import_module
    foreign_export_enum foreign_export foreign_enum may_call_mercury
    will_not_call_mercury thread_safe not_thread_safe maybe_thread_safe
    promise_pure promise_semipure tabled_for_io local untrailed trailed
    attach_to_io_state can_pass_as_mercury_type stable
    will_not_throw_exception may_modify_trail will_not_modify_trail
    may_duplicate may_not_duplicate affects_liveness
    does_not_affect_liveness doesnt_affect_liveness no_sharing
    unknown_sharing sharing
    """.split()

built_in0 = [RE(r"<=>")]

built_in1 = [RE(r"<=")]

built_in2 = [RE(r"=>")]

built_in3 = [RE(r"/\\")]

built_in4 = [RE(r"\\/")]

built_in5 = [RE(r":-\|-->")]

built_in6 = [RE(r"=")]

number = [RE(r"0'.\|0[box][0-9a-fA-F]*")]

number0 = [RE(r"\b\d+(?:\.\d+)?")]

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

subst = [
    RE(r"\\[abfnrtv]\|\\x[0-9a-fA-F]*\\\|%[-+# *.0-9]*[dioxXucsfeEgGp]"),
]

class string0:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': '\\\\[\\s\\S]', 'relevance': 0},
        ('subst', subst),
    ]
string0.__name__ = 'string'

rules = [
    ('built_in', built_in),
    ('keyword', keyword),
    ('meta', meta),
    ('built_in', built_in0),
    ('built_in', built_in1),
    ('built_in', built_in2),
    ('built_in', built_in3),
    ('built_in', built_in4),
    ('built_in', built_in5),
    ('built_in', built_in6),
    ('comment', RE(r"%"), [RE(r"$")], comment),
    ('comment', RE(r"/\*"), [RE(r"\*/")], comment),
    ('number', number),
    ('number', number0),
    ('string', RE(r"'"), [RE(r"'")], string),
    ('string', RE(r"\""), [RE(r"\"")], string0),
    # ignore {'begin': {'pattern': ':-', 'type': 'RegExp'}},
]
