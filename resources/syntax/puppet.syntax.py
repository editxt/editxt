# -*- coding: UTF-8 -*-
# Syntax definition automatically generated by hljs2xt.py
# source: puppet.js
name = 'Puppet'
file_patterns = ['*.puppet', '*.pp']

class comment:
    default_text_color = DELIMITER
    rules = [
        # ignore {'begin': {'pattern': "\\b(a|an|the|are|I|I'm|isn't|don't|doesn't|won't|but|just|should|pretty|simply|enough|gonna|going|wtf|so|such|will|you|your|like)\\b", 'type': 'RegExp'}},
        ('doctag', [RE(r"(?:TODO|FIXME|NOTE|BUG|XXX):")]),
    ]

comment0 = ('comment', RE(r"#"), [RE(r"$")], comment)

variable = ('variable', [RE(r"\$(?:[A-Za-z_]|::)(?:\w|::)*")])

class string:
    default_text_color = DELIMITER
    rules = [('operator.escape', [RE(r"\\[\s\S]")]), variable]

string1 = ('string', RE(r"'"), [RE(r"'")], string)

string2 = ('string', RE(r"\""), [RE(r"\"")], string)

class _group1:
    default_text_color = DELIMITER
    rules = [
        ('keyword', ['class']),
        ('title', [RE(r"(?:[A-Za-z_]|::)(?:\w|::)*")]),
        comment0,
    ]

class _group2:
    default_text_color = DELIMITER
    rules = [('keyword', ['define']), ('section', [RE(r"[a-zA-Z]\w*")])]

built_in = """
    architecture augeasversion blockdevices boardmanufacturer
    boardproductname boardserialnumber cfkey dhcp_servers domain ec2_
    ec2_userdata facterversion filesystems ldom fqdn gid hardwareisa
    hardwaremodel hostname id interfaces ipaddress ipaddress_ ipaddress6
    ipaddress6_ iphostnumber is_virtual kernel kernelmajversion
    kernelrelease kernelversion kernelrelease kernelversion
    lsbdistcodename lsbdistdescription lsbdistid lsbdistrelease
    lsbmajdistrelease lsbminordistrelease lsbrelease macaddress
    macaddress_ macosx_buildversion macosx_productname
    macosx_productversion macosx_productverson_major
    macosx_productversion_minor manufacturer memoryfree memorysize
    netmask metmask_ network_ operatingsystem operatingsystemmajrelease
    operatingsystemrelease osfamily partitions path
    physicalprocessorcount processor processorcount productname ps
    puppetversion rubysitedir rubyversion selinux selinux_config_mode
    selinux_config_policy selinux_current_mode selinux_current_mode
    selinux_enforced selinux_policyversion serialnumber sp_ sshdsakey
    sshecdsakey sshrsakey swapencrypted swapfree swapsize timezone type
    uniqueid uptime uptime_days uptime_hours uptime_seconds uuid virtual
    vlans xendomains zfs_version zonenae zones zpool_version
    """.split()

keyword2 = """
    and case default else elsif false if in import enherits node or true
    undef unless main settings $string
    """.split()

literal = """
    alias audit before loglevel noop require subscribe tag owner ensure
    group mode name changes context force incl lens load_path onlyif
    provider returns root show_diff type_check en_address ip_address
    realname command environment hour monute month monthday special
    target weekday creates cwd ogoutput refresh refreshonly tries
    try_sleep umask backup checksum content ctime force ignore links
    mtime purge recurse recurselimit replace selinux_ignore_defaults
    selrange selrole seltype seluser source souirce_permissions
    sourceselect validate_cmd validate_replacement allowdupe
    attribute_membership auth_membership forcelocal gid ia_load_module
    members system host_aliases ip allowed_trunk_vlans description
    device_url duplex encapsulation etherchannel native_vlan speed
    principals allow_root auth_class auth_type authenticate_user k_of_n
    mechanisms rule session_owner shared options device fstype enable
    hasrestart directory present absent link atboot blockdevice device
    dump pass remounts poller_tag use message withpath adminfile
    allow_virtual allowcdrom category configfiles flavor install_options
    instance package_settings platform responsefile status
    uninstall_options vendor unless_system_user unless_uid binary
    control flags hasstatus manifest pattern restart running start stop
    allowdupe auths expiry gid groups home iterations key_membership
    keys managehome membership password password_max_age
    password_min_age profile_membership profiles project purge_ssh_keys
    role_membership roles salt shell uid baseurl cost descr enabled
    enablegroups exclude failovermethod gpgcheck gpgkey http_caching
    include includepkgs keepalive metadata_expire metalink mirrorlist
    priority protect proxy proxy_password proxy_username repo_gpgcheck
    s3_enabled skip_if_unavailable sslcacert sslclientcert sslclientkey
    sslverify mounted
    """.split()

class _group5:
    default_text_color = DELIMITER
    rules = [('attr', [RE(r"[a-zA-Z]\w*")])]

number = [
    RE(r"(?:\b0[0-7_]+)|(?:\b0x[0-9a-fA-F_]+)|(?:\b[1-9][0-9_]*(?:\.[0-9_]+)?)|[0_]\b"),
]

class _group4:
    default_text_color = DELIMITER
    rules = [
        ('built_in', built_in),
        ('keyword', keyword2),
        ('literal', literal),
        string1,
        string2,
        comment0,
        ('_group5', RE(r"(?=[a-zA-Z_]+\s*=>)"), [RE(r"=>")], _group5),
        ('number', number),
        variable,
    ]

class _group3:
    default_text_color = DELIMITER
    rules = [
        ('keyword', [RE(r"[a-zA-Z]\w*")]),
        ('_group4', RE(r"\{"), [RE(r"\}")], _group4),
    ]

rules = [
    comment0,
    variable,
    string1,
    string2,
    ('_group1', RE(r"\b(?:class)"), [RE(r"\{|;")], _group1),
    ('_group2', RE(r"\b(?:define)"), [RE(r"\{")], _group2),
    ('_group3', RE(r"(?=[a-zA-Z]\w*\s+\{)"), [RE(r"\S")], _group3),
]
