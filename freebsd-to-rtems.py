#! /usr/bin/env python
#
#  Copyright (c) 2015-2016 Chris Johns <chrisj@rtems.org>. All rights reserved.
#
#  Copyright (c) 2009-2015 embedded brains GmbH.  All rights reserved.
#
#   embedded brains GmbH
#   Dornierstr. 4
#   82178 Puchheim
#   Germany
#   <info@embedded-brains.de>
#
#  Copyright (c) 2012 OAR Corporation. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions
#  are met:
#  1. Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
#  2. Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# FreeBSD: http://svn.freebsd.org/base/releng/8.2/sys (revision 222485)

from __future__ import print_function

import os
import sys
import getopt

import builder
import libbsd

isForward = True
isEarlyExit = False
statsReport = False
isConfig = False

def usage():
    print("freebsd-to-rtems.py [args]")
    print("  -?|-h|--help      print this and exit")
    print("  -d|--dry-run      run program but no modifications")
    print("  -D|--diff         provide diff of files between trees")
    print("  -e|--early-exit   evaluate arguments, print results, and exit")
    print("  -m|--makefile     Warning: depreciated and will be removed ")
    print("  -S|--stats        Print a statistics report")
    print("  -R|--reverse      default origin -> LibBSD, reverse that")
    print("  -r|--rtems        LibBSD directory (default: '.')")
    print("  -f|--freebsd      FreeBSD origin directory (default: 'freebsd-org')")
    print("  -c|--config       Output the configuration then exit")
    print("  -v|--verbose      enable verbose output mode")

# Parse the arguments
def parseArguments():
    global isForward, isEarlyExit, statsReport, isConfig
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "?hdDembSRr:f:cv",
                                   [ "help",
                                     "help",
                                     "dry-run"
                                     "diff"
                                     "early-exit"
                                     "makefile"
                                     "buildscripts"
                                     "reverse"
                                     "stats"
                                     "rtems="
                                     "freebsd="
                                     "config"
                                     "verbose" ])
    except getopt.GetoptError as err:
        # print help information and exit:
        print(err)
        usage()
        sys.exit(2)
    for o, a in opts:
        if o in ("-v", "--verbose"):
            builder.verboseLevel += 1
        elif o in ("-h", "--help", "-?"):
            usage()
            sys.exit()
        elif o in ("-d", "--dry-run"):
            builder.isDryRun = True
        elif o in ("-D", "--diff"):
            builder.isDiffMode = True
        elif o in ("-e", "--early-exit"):
            isEarlyExit = True
        elif o in ("-S", "--stats"):
            statsReport = True
        elif o in ("-R", "--reverse"):
            isForward = False
        elif o in ("-r", "--rtems"):
            builder.LIBBSD_DIR = a
        elif o in ("-f", "--freebsd"):
            builder.FreeBSD_DIR = a
        elif o in ("-c", "--config"):
            isConfig = True
        else:
            assert False, "unhandled option"

parseArguments()

print("Verbose:                     %s (%d)" % (("no", "yes")[builder.verbose()],
                                                builder.verboseLevel))
print("Dry Run:                     %s" % (("no", "yes")[builder.isDryRun]))
print("Diff Mode Enabled:           %s" % (("no", "yes")[builder.isDiffMode]))
print("LibBSD Directory:            %s" % (builder.LIBBSD_DIR))
print("FreeBSD Directory:           %s" % (builder.FreeBSD_DIR))
print("Direction:                   %s" % (("reverse", "forward")[isForward]))

# Check directory argument was set and exist
def wasDirectorySet(desc, path):
    if path == "not_set":
        print(f"error:{desc} Directory was not specified on command line")
        sys.exit(2)

    if os.path.isdir( path ) != True:
        print(f"error:{desc} Directory ({path}) does not exist")
        sys.exit(2)

try:
    if not isConfig:
        # Were directories specified?
        wasDirectorySet( "LibBSD", builder.LIBBSD_DIR )
        wasDirectorySet( "FreeBSD", builder.FreeBSD_DIR )

        # Are we generating or reverting?
        if isForward == True:
            print("Forward from", builder.FreeBSD_DIR, "into", builder.LIBBSD_DIR)
        else:
            print("Reverting from", builder.LIBBSD_DIR)

        if isEarlyExit == True:
            print("Early exit at user request")
            sys.exit(0)

    build = builder.ModuleManager()
    libbsd.load(build)
    build.loadConfig()
    build.generateBuild(only_enabled=False)

    dups = build.duplicateCheck()
    if len(dups) > 0:
        print()
        print('Duplicates: %d' % (len(dups)))
        mods = list({dup[0] for dup in dups})
        max_mod_len = max(len(dup[1]) for dup in dups)
        for mod in mods:
            print(f' {mod}:')
            for dup in [dup for dup in dups if dup[0] == mod]:
                print('  %-*s %s %s' % (max_mod_len, dup[1], dup[3][0].upper(), dup[2]))
        print()

    if isConfig:
        print()
        print(build)
        sys.exit(0)

    build.processSource(isForward)
    builder.changedFileSummary(statsReport)
except IOError as ioe:
    print(f'error: {str(ioe)}')
except builder.error as be:
    print(f'error: {be}')
except KeyboardInterrupt:
    print('user abort')
