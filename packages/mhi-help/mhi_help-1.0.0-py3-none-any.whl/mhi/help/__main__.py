"""
MHI Help - Command Line Interface
"""

import sys

import mhi.help

if len(sys.argv) > 2:
    print("mhi.help: too many arguments: ", *sys.argv[2:], file=sys.stderr)
    sys.exit(1)

mhi.help.open_help(*sys.argv[1:])
