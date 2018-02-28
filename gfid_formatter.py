#!/usr/bin/env python
#
# Pontus Freyhult, UPPMAX
# 
# See README.md for details.
#

import os
import xattr
import base64
import stat
import sys

def format_gfid(gfid):
    s = ''.join( [ '%02x' % ord(x) for x in gfid ] )

    linkname = "%s/%s/%s-%s-%s-%s-%s" % (s[0:2], s[2:4], s[0:8], s[8:12], s[12:16], s[16:20], s[20:32])

    return linkname

if len(sys.argv)<2:
    print "You need to give something to format gfid for."
    raise SystemExit


for p in sys.argv[1:]:
    gfid = xattr.get(p, 'trusted.gfid')
    s = ''.join( [ '%02x' % ord(x) for x in gfid ] )
    print "%s-%s-%s-%s-%s"% (s[0:8], s[8:12], s[12:16], s[16:20], s[20:32])

