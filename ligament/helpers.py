import os
import sys
import glob
import urllib2

import colorama

########################
#                      #
#   Functional Tools   #
#                      #
########################


def partition(pred, iterable):
    """ split the results of an iterable based on a predicate """
    trues = []
    falses = []
    for item in iterable:
        if pred(item):
            trues.append(item)
        else:
            falses.append(item)
    return trues, falses


def zip_with_output(skip_args=[]):
    def decorator(fn):
        def wrapped(*args):
            g = [arg for i, arg in enumerate(args) if i not in skip_args]
            if len(g) == 1:
                return(g[0], fn(*args))
            else:
                return (g, fn(*args))
        return wrapped
    return decorator


def capture_exception(fn):
    def wrapped(*args):
        try:
            return fn(*args)
        except Exception as e:
            return e
    return wrapped


def compose(*funcs):
    return lambda x: reduce(lambda v, f: f(v), reversed(funcs), x)


###############
#             #
#   File IO   #
#             #
###############


def map_over_glob(fn, path, pattern):
    return [fn(x) for x in glob.glob(os.path.join(path, pattern))]


def mkdir_recursive(dirname):
    """ makes all the directories along a given path, if they do not exist
    """
    parent = os.path.dirname(dirname)
    if parent != "":
        if not os.path.exists(parent):
            mkdir_recursive(parent)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
    elif not os.path.exists(dirname):
        os.mkdir(dirname)


colorama_init = False
lasting_indent = 0
def perror(*args, **kwargs):
    """ print to stderr """

    # python 2.7 workaround
    indent = kwargs["indent"] if "indent" in kwargs else"+0"

    # initialize colorama only if uninitialized
    global colorama_init
    if not colorama_init:
        colorama_init = True
        colorama.init()

    global lasting_indent
    if indent.startswith("++"):
        lasting_indent = lasting_indent + int(indent[2:])
        cur_indent = lasting_indent
    elif indent.startswith("+"):
        cur_indent = lasting_indent + int(indent[1:])
    elif indent.startswith("--"):
        lasting_indent = lasting_indent - int(indent[2:])
        cur_indent = lasting_indent
    elif indent.startswith("-"):
        cur_indent = lasting_indent - int(indent[1:])
    elif indent.startswith("=="):
        lasting_indent = int(indent[2:])
        cur_indent = lasting_indent
    elif indent.startswith("="):
        lasting_indent = int(indent[1:])
        cur_indent = int(indent[1:])
    else:
        raise Exception(
            "indent command format '%s' unrecognized (see the docstring)")

    # mutate indentation level if needed
    args = [elem.replace("\n", "\n" + " " * cur_indent) for elem in args]

    # write to stdout
    sys.stderr.write(colorama.Fore.RED)
    sys.stderr.write(" " * cur_indent)
    sys.stderr.write(*args)
    sys.stderr.write(colorama.Fore.RESET)
    sys.stderr.write("\n")



def urlretrieve(url, dest, write_mode="w"):
    response = urllib2.urlopen(url)
    mkdir_recursive(os.path.dirname(dest))
    with open(dest, write_mode) as f:
        f.write(response.read())
        f.close()


############
#          #
#   Misc   #
#          #
############


def remove_dups(seq):
    """ remove duplicates from a sequence, preserving order """
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


