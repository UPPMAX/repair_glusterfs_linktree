#!/usr/bin/env python
#
# Pontus Freyhult, UPPMAX
# 
# See README.md for details.
#

import os
import os.path
import xattr
import base64
import stat
import sys
from stat import S_ISDIR,S_ISLNK,S_ISREG


def format_gfid(gfid):
    s = ''.join( [ '%02x' % ord(x) for x in gfid ] )

    linkname = "%s/%s/%s-%s-%s-%s-%s" % (s[0:2], s[2:4], s[0:8], s[8:12], s[12:16], s[16:20], s[20:32])

    return linkname

def gfid_to_path(gfid_string):
 
    linkdata = os.readlink("%s/%s/%s" % (gfid_string[0:2], gfid_string[2:4], gfid_string))

    rightmost = os.path.basename(linkdata)
    uplevel = os.path.dirname(linkdata)

    if uplevel == '../../00/00/00000000-0000-0000-0000-000000000001':
        return rightmost
    else:
        # Recurse 
        return os.path.join(
            gfid_to_path(
                os.path.basename(
                    uplevel
                )),
        rightmost)


def walk_link_tree(pgfid, pgpath):
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

                        ltr = os.path.basename(links_to)
                        ltl = os.path.basename(os.path.dirname(links_to))

                        print "Unexpected: %s links to %s (%s) not %s (%s) as expected" % (ln_full,                                                                                     
                                                                                           links_to,                                                                                    
                                                                                           os.path.join(gfid_to_path(ltl),                                                              
                                                                                                        ltr),                                                                           
                                                                                           pgfid_path,                                                                                  
                                                                                           os.path.join(pgpath[43:], 
                                                                                                        direntry))      


                else:
                    print "Unexpected: %s is not a symbolic link" % ln_full


                walk_link_tree(ln[6:], depath)
                
            except OSError,e:
                print "Exception %s " % e
                print "Missing link for %s in %s" % (direntry, pgpath) 
                print "You should probably run "
                print "ln -s '%s' '%s'" % (pgfid_path, ln_full)


def walk_data_tree(current_path, toplevel=False, pgfid_path='00/00/00000000-0000-0000-0000-000000000001'):
    l = os.listdir(current_path)

    for direntry in l:

        if direntry in ('.', '..') or toplevel and direntry == '.glusterfs':
            continue


        ln = None
        ln_full = None
        link_stat = None

        depath = os.path.join(current_path, direntry)
        data_stat = os.lstat(depath)

        if not S_ISLNK(data_stat.st_mode):
            # Links don't have a gfid of their own.

            try:
                x = xattr.get(depath, 'trusted.gfid')
                ln = format_gfid(x)
                ln_full = os.path.join(os.getcwd(),ln)
            
                try: 
                    link_stat = os.lstat(ln)
                except OSError, e:
                    print "Missing expected link tree object at %s" % ln_full

            except IOError, e:
                print "Missing trusted.gfid extended attribute for %s" % depath
        
        if S_ISDIR(data_stat.st_mode):
            # This is a directory, link tree object should be a symbolinc link to it's directory in the parent structure
            #
            if not link_stat:
                print "Missing link for directory for %s, you should probably run " % depath
                print "ln -s '../../%s/%s' '%s'" % (pgfid_path, direntry, ln_full)
            else:
                if not S_ISLNK(link_stat.st_mode) or not os.readlink(ln) == '../../%s/%s' % (pgfid_path, direntry):
                    print "Unexpected: %s does not link to what we expected it to (../../%s/%s)." % (ln_full, pgfid_path, direntry) 
                    
            walk_data_tree(depath, pgfid_path = ln)
            
        if S_ISREG(data_stat.st_mode):
            if not link_stat:
                print "Missing hard link for file %s, you should probably run " % depath
                print "ln  '%s' '%s'" % (depath, ln_full)
            else:
                if link_stat.st_dev != data_stat.st_dev or link_stat.st_ino != data_stat.st_ino:
                    print "Unexpected: %s is not what we expected (hard link to %s)" % (ln_full, depath)

            
if len(sys.argv) > 1:
    trees_to_walk =  sys.argv[1:]
else:
    trees_to_walk = ['.']

startdir = os.getcwd()
   
for current_dir in trees_to_walk:
    os.chdir(startdir)
    os.chdir(os.path.join(current_dir, '.glusterfs'))
    print "Working on %s " % current_dir

    walk_link_tree('00000000-0000-0000-0000-000000000001','00/00/00000000-0000-0000-0000-000000000001')
    walk_data_tree(os.path.realpath('..'), toplevel=True)

