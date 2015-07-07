#!/usr/bin/python
import os
import sys
import imp

from buildtarget import BuildTarget, Context
from ligament_list import BuildTargetList
from buildcontextfseventhandler import BuildContextFsEventHandler

from time import sleep
from watchdog.observers import Observer


def run_skeleton(ligamentfile_path, tasks, watch=True):
    sys.path.insert(0, '.')
    ligamentfile = imp.load_source('ligamentfile', ligamentfile_path)

    build_context = Context()

    for name, task in ligamentfile.ligament_tasks.iteritems():
        if isinstance(task, BuildTarget):
            print "registered task '%s'" % name
            task.register_with_context(name, build_context)
        elif isinstance(task, list):
            BuildTargetList(task).register_with_context(name, build_context)

    for task in tasks:
        for name in ligamentfile.ligament_tasks[task]:
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
