import os
import sys
import glob
import urllib2

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


def zip_with_output(fn):
    def wrapped(*args):
        if len(args) == 1:
            return(args[0], fn(*args))
        else:
            return (args, fn(*args))
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


def perror(*args):
    """ print to stderr """
    sys.stderr.write(*args)
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


