"""
A python task automator, with a focus on task composition
"""
import ligament
import helpers
import buildtarget
import buildcontext
import buildcontextfseventhandler
import exceptions

import sys
import getopt

from helpers import pout

def print_helptext():
    """ print helptext for command-line interface """
    pout("usage: %s [flags] [tasks]\n"
         "    Execute tasks in order. if no tasks are specified, tries to\n"
         "    execute task 'default'\n"
         "    flags:\n"
         "        -w / --watch    watch files/folders for changes and update\n"
         "        -h / --help     display this helptext" % sys.argv[0])


def main():
    """ parse command line opts and run a skeleton file

        when called from the command line, ligament looks in the current 
        working directory for a file called `skeleton.py`. Tasks specified from
        the command line are then executed in order, and if the -w flag was
        specified, ligament then watches the filesystem for changes to
        prompt task re-execution;
    """

    options = None
    try:
        options, args = getopt.gnu_getopt(
            sys.argv[1:],
            "whqv",
            ["watch", "help", "query", "verbose"])
    except getopt.GetoptError as e:
        print e
        print_helptext()
        exit(1)

    should_watch = False
    query_skeleton = False
    verbose = False

    for opt, arg in options:
        if opt == "--watch" or opt == '-w':
            should_watch = True
        elif opt == "--query" or opt == '-q':
            query_skeleton = True
        elif opt == "--help" or opt == '-h':
            print_helptext()
            exit(0)
        elif opt == "--verbose" or opt == '-v':
            verbose = True
        else:
            print "option '%s' not recognized" % opt
            print_helptext()
            exit(1)

    if verbose:
        helpers.set_verbosity(".*")

    if query_skeleton:
        print " ".join(ligament.query_skeleton("./skeleton.py"))
        helpers.set_verbosity()

    else:
        helpers.add_verbosity_groups("build_task")
        ligament.run_skeleton(
            "./skeleton.py",
            ["default"] if len(args) == 0 else args,
            watch=should_watch)
