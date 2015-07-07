import ligament
import helpers
import buildtarget
import buildcontext
import buildcontextfseventhandler
import buildexception

import sys
import getopt


def main():
    options, args = getopt.gnu_getopt(
        sys.argv[1:],
        "w",
        "watch")

    should_watch = False

    for opt, arg in options:
        if opt == "--watch" or opt == '-w':
            should_watch = True
        else:
            print "opt %s not recognized" % opt

    ligament.run_skeleton(
        "./skeleton.py",
        ["default"] if len(args) == 0 else args,
        watch=should_watch)
