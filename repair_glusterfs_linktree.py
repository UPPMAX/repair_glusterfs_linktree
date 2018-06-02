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

def walk_tree(pgfid, pgpath):
    l = os.listdir(pgpath)

    for direntry in l:
        depath = os.path.join(pgpath, direntry)

        if direntry[0] != '.' and stat.S_ISDIR(os.lstat(depath).st_mode):
            # We should traverse this
            x = xattr.get(depath, 'trusted.gfid')
            ln = format_gfid(x)
            ln_full = os.path.join(os.getcwd(),ln)

            pgfid_path = "../../%s/%s/%s/%s" % (pgfid[0:2], pgfid[2:4], pgfid, direntry)

            try:
                # Check if path link exists
                st = os.lstat(ln)
                
                if stat.S_ISLNK(st.st_mode):
                    links_to = os.readlink(ln)

                    if links_to != pgfid_path:
                        print "Unexpected: %s links to %s not %s as expected" % (ln_full, links_to, pgfid_path)

                else:
                    print "Unexpected: %s is not a symbolic link" % ln_full


                walk_tree(ln[6:], depath)
                
            except Exception,e:
                print "Missing link for %s in %s" % (direntry, pgpath) 
                print "You should probably run "
                print "ln -s '%s' '%s'" % (pgfid_path, ln_full)
            
            
if len(sys.argv) > 1:
    trees_to_walk =  sys.argv[1:]
else:
    trees_to_walk = ['.']

startdir = os.getcwd()
   
for current_dir in trees_to_walk:
    os.chdir(startdir)
    os.chdir(os.path.join(current_dir, '.glusterfs'))
    print "Working on %s " % current_dir

    walk_tree('00000000-0000-0000-0000-000000000001','00/00/00000000-0000-0000-0000-000000000001')

