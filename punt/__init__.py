#!/usr/bin/python
import os
import sys
import imp
import getopt

from buildtarget import BuildTarget, Context
from punt_list import BuildTargetList
from buildcontextfseventhandler import BuildContextFsEventHandler

from time import sleep
from watchdog.observers import Observer


import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')


def run_puntfile(puntfile_path, tasks, watch=True):
    sys.path.insert(0, '.')
    puntfile = imp.load_source('puntfile', puntfile_path)

    build_context = Context()

    for name, task in puntfile.punt_tasks.iteritems():
        if isinstance(task, BuildTarget):
            print "registered task '%s'" % name
            task.register_with_context(name, build_context)
        elif isinstance(task, list):
            BuildTargetList(task).register_with_context(name, build_context)

    for task in tasks:
        for name in puntfile.punt_tasks[task]:
            build_context.build_task(name)

    if watch:

        print
        print "resolving watch targets"

        # establish watchers
        observer = Observer()
        buildcontexteventhandler = BuildContextFsEventHandler(build_context)
        for task in build_context.built:
            for f in build_context.tasks[task].file_watch_targets:
                print "%s: watching %s" % (task, f)
                if os.path.isdir(f):
                    observer.schedule(
                        buildcontexteventhandler,
                        f,
                        recursive=True)
                else:
                    observer.schedule(
                        buildcontexteventhandler,
                        os.path.dirname(f),
                        recursive=True)

        print
        print "watching for changes"

        observer.start()
        try:
            while True:
                sleep(0.5)
        except KeyboardInterrupt:
            observer.stop()
        observer.join()


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

    run_puntfile(
        "./puntfile.py",
        ["default"] if len(args) == 0 else args,
        watch=should_watch)

