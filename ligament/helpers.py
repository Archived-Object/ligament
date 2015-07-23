import os
import re
import sys
import glob
import urllib2
import collections

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
    """decorater that zips the input of a function with its output 
        only zips positional arguments.

        skip_args : list
            a list of indexes of arguments to exclude from the skip

            @zip_with_output(skip_args=[0])
            def foo(bar, baz):
                return baz

        will decorate foo s.t.

            foo(x, y) = y
    """
    def decorator(fn):
        def wrapped(*args, **vargs):
            g = [arg for i, arg in enumerate(args) if i not in skip_args]
            if len(g) == 1:
                return(g[0], fn(*args, **vargs))
            else:
                return (g, fn(*args, **vargs))
        return wrapped
    return decorator


def capture_exception(fn):
    """decorator that catches and returns an exception from wrapped function"""
    def wrapped(*args):
        try:
            return fn(*args)
        except Exception as e:
            return e
    return wrapped


def compose(*funcs):
    """compose a list of functions"""
    return lambda x: reduce(lambda v, f: f(v), reversed(funcs), x)


def build_lst(a, b):
    """ function to be folded over a list (with initial value `None`)
        produces one of:

        1. `None`
        2. A single value
        3. A list of all values
    """
    if type(a) is list:
        return a + [b]
    elif a:
        return [a, b]
    else:
        return b

def flatten_list(strs):
    return ([str(strs)]
            if not isinstance(strs, list) 
            else reduce(
                lambda a, b: a + b,
                [flatten_list(s) for s in strs],
                []))

###############
#             #
#   File IO   #
#             #
###############


def map_over_glob(fn, path, pattern):
    """map a function over a glob pattern, relative to a directory"""
    return [fn(x) for x in glob.glob(os.path.join(path, pattern))]


def mkdir_recursive(dirname):
    """makes all the directories along a given path, if they do not exist"""
    parent = os.path.dirname(dirname)
    if parent != "":
        if not os.path.exists(parent):
            mkdir_recursive(parent)
        if not os.path.exists(dirname):
            os.mkdir(dirname)
    elif not os.path.exists(dirname):
        os.mkdir(dirname)

default_verbosity_filter = ["normal", "error", "warning"]
verbosity_filter = []
"""level of verboseness represented numerically"""


def should_msg(groups):
    return any(
        any(p.match(g) for g in groups)
        for p in verbosity_filter)


def set_verbosity(*groups):
    global verbosity_filter
    verbosity_filter = [re.compile(g) for g in groups]


def add_verbosity_groups(*groups):
    global verbosity_filter
    verbosity_filter += [re.compile(g) for g in groups]


set_verbosity(*default_verbosity_filter)

lasting_indent = 0
"""lasting indent for text printed with perror/pout/pwarning/pdebug"""

def indent_text(*strs, **kwargs):
    """ indents text according to an operater string and a global indentation 
        level. returns a tuple of all passed args, indented according to the
        operator string

        indent: [defaults to +0]
            The operator string, of the form
            ++n : increments the global indentation level by n and indents
            +n  : indents with the global indentation level + n
            --n : decrements the global indentation level by n
            -n  : indents with the global indentation level - n
            ==n : sets the global indentation level to exactly n and indents
            =n  : indents with an indentation level of exactly n
    """
    # python 2.7 workaround
    indent = kwargs["indent"] if "indent" in kwargs else"+0"
    autobreak = kwargs.get("autobreak", False)
    char_limit = kwargs.get("char_limit", 80)
    split_char = kwargs.get("split_char", " ")

    strs = list(strs)

    if autobreak:
        for index, s in enumerate(strs):
            if len(s) > char_limit:
                strs[index] = []
                spl =  s.split(split_char)
                result = []
                collect = ""
                for current_block in spl:
                    if len(current_block) + len(collect) > char_limit:
                        strs[index].append(collect[:-1] + "\n") 
                        collect = "    "
                    collect += current_block + split_char
                strs[index].append(collect + "\n")

        strs = flatten_list(strs)

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
    return tuple([" " * cur_indent] + [elem.replace("\n", "\n" + " " * cur_indent) 
                  for elem in strs])


colorama_init = False
"""State tracker for if the colorama module has been initialized"""

def perror(*args, **kwargs):
    """print formatted output to stderr with indentation control"""

    if should_msg(kwargs.get("groups", ["error"])):
        # initialize colorama only if uninitialized
        global colorama_init
        if not colorama_init:
            colorama_init = True
            colorama.init()

        args = indent_text(*args, **kwargs)

        # write to stdout
        sys.stderr.write(colorama.Fore.RED)
        sys.stderr.write("".join(args))
        sys.stderr.write(colorama.Fore.RESET)
        sys.stderr.write("\n")


def pwarning(*args, **kwargs):
    """print formatted output to stderr with indentation control"""
    if should_msg(kwargs.get("groups", ["warning"])):

        # initialize colorama only if uninitialized
        global colorama_init
        if not colorama_init:
            colorama_init = True
            colorama.init()

        args = indent_text(*args, **kwargs)

        # write to stdout
        sys.stderr.write(colorama.Fore.YELLOW)
        sys.stderr.write("".join(args))
        sys.stderr.write(colorama.Fore.RESET)
        sys.stderr.write("\n")


def pdebug(*args, **kwargs):
    """print formatted output to stdout with indentation control"""
    if should_msg(kwargs.get("groups", ["debug"])):
        # initialize colorama only if uninitialized
        global colorama_init
        if not colorama_init:
            colorama_init = True
            colorama.init()

        args = indent_text(*args, **kwargs)

        # write to stdout
        sys.stderr.write(colorama.Fore.CYAN)
        sys.stderr.write("".join(args))
        sys.stderr.write(colorama.Fore.RESET)
        sys.stderr.write("\n")


def pout(*args, **kwargs):
    """print to stdout, maintaining indent level"""
    if should_msg(kwargs.get("groups", ["normal"])):
        args = indent_text(*args, **kwargs)

        # write to stdout
        sys.stderr.write("".join(args))
        sys.stderr.write("\n")


def urlretrieve(url, dest, write_mode="w"):
    """save a file to disk from a given url"""
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
    """remove duplicates from a sequence, preserving order"""
    seen = set()
    seen_add = seen.add
    return [x for x in seq if not (x in seen or seen_add(x))]


def merge_dicts(*dicts):
    super_dict = collections.defaultdict(set)
    for d in dicts:
        for k, v in d.iteritems():
            super_dict[k] = v
    return super_dict

