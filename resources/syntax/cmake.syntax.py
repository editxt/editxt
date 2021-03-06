# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: cmake.js
name = 'CMake'
file_patterns = ['*.cmake', '*.cmake.in']

flags = re.IGNORECASE | re.MULTILINE

keyword = """
    add_custom_command add_custom_target add_definitions
    add_dependencies add_executable add_library add_subdirectory
    add_test aux_source_directory break build_command
    cmake_minimum_required cmake_policy configure_file
    create_test_sourcelist define_property else elseif enable_language
    enable_testing endforeach endfunction endif endmacro endwhile
    execute_process export find_file find_library find_package find_path
    find_program fltk_wrap_ui foreach function get_cmake_property
    get_directory_property get_filename_component get_property
    get_source_file_property get_target_property get_test_property if
    include include_directories include_external_msproject
    include_regular_expression install link_directories load_cache
    load_command macro mark_as_advanced message option
    output_required_files project qt_wrap_cpp qt_wrap_ui
    remove_definitions return separate_arguments set
    set_directory_properties set_property set_source_files_properties
    set_target_properties set_tests_properties site_name source_group
    string target_link_libraries try_compile try_run unset
    variable_watch while build_name exec_program
    export_library_dependencies install_files install_programs
    install_targets link_libraries make_directory remove subdir_depends
    subdirs use_mangled_mesa utility_source variable_requires write_file
    qt5_use_modules qt5_use_package qt5_wrap_cpp on off true false and
    or equal less greater strless strgreater strequal matches
    """.split()

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

class string:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")])]

rules = [
    ('keyword', keyword),
    ('variable', RE(r"\${"), [RE(r"}")]),
    ('comment', RE(r"#"), [RE(r"$")], comment),
    ('string', RE(r"\""), [RE(r"\"")], string),
    ('number', [RE(r"\b\d+(?:\.\d+)?")]),
]
