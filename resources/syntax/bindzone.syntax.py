# EditXT
# Copyright 2007-2013 Daniel Miller <millerdev@gmail.com>
# 
# This file is part of EditXT, a programmer's text editor for Mac OS X,
# which can be found at http://editxt.org/.
# 
# EditXT is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# EditXT is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with EditXT.  If not, see <http://www.gnu.org/licenses/>.

name = "Bind Zone"
file_patterns = ["*.zone"]
comment_token = ";"
word_groups = [
    ("keyword", """
        A
        AAAA
        AFSDB
        APL
        CAA
        CERT
        CNAME
        DHCID
        DLV
        DNAME
        DNSKEY
        DS
        HIP
        IPSECKEY
        KEY
        KX
        LOC
        MX
        NAPTR
        NS
        NSEC
        NSEC3
        NSEC3PARAM
        PTR
        RP
        RRSIG
        SIG
        SOA
        SPF
        SRV
        SSHFP
        TLSA
        TSIG
        TXT
    """.split()),
    ("operator", "@ IN".split()),
]
# TODO revisit the theme names used for these ranges
delimited_ranges = [
    ("builtin", RE('\$[A-Z]'), [RE(r"(?=\s)")]), # plum
    ("string.txt", RE('"'), ['"']),              # teal, TXT-like record values
    ("value.a-record", RE('(?<=\sA\s)'), [RE(r"(?=\n)")]),      # cayenne, A record values
    ("string.cname", RE('(?<=\sCNAME\s)'), [RE(r"(?=\n)")]),    # teal, CNAME record values
    ("comment", ";", [RE(r"(?=\n)")]),
]
