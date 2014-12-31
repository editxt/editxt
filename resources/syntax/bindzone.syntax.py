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


c = dict(
    # EditXT colors
    gray = "505050",
    blue = "0000CC",

    # named colors commonly used by EditXT
    midnight = "000080",
    clover = "008000",
    plum = "800080",
    teal = "008080",
    cayenne = "800000",
)

name = "Zone"
filepatterns = ["*.zone"]
comment_token = ";"
word_groups = [
    ("""
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
    """.split(), c["blue"]),
    ("@ IN".split(), c["plum"]),
]
delimited_ranges = [
    (RE('\$[A-Z]'), [RE(r"(?=\s)")], c["plum"], None),
    (RE('"'), ['"'], c["teal"], None),                          # TXT-like record values
    (RE('(?<=\sA\s)'), [RE(r"(?=\n)")], c["cayenne"], None),    # A record values
    (RE('(?<=\sCNAME\s)'), [RE(r"(?=\n)")], c["teal"], None),   # CNAME record values
    (";", [RE(r"(?=\n)")], c["clover"], None),
]
del c
