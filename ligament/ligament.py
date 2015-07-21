#!/usr/bin/python
import os
import sys
import imp
import json

from buildcontext import Context, DeferredDependency
from buildtarget import BuildTarget
from compositors import BuildTargetList
from buildcontextfseventhandler import BuildContextFsEventHandler
from helpers import pout, perror

from time import sleep
from watchdog.observers import Observer

from privacy import *

def load_context_from_skeleton(skeleton_path):
    try:
        sys.path.insert(0, '.')
        ligamentfile = imp.load_source('ligamentfile', skeleton_path)
    except IOError:
        perror("Error importing skeleton.py file found in current directory")
        exit (1)

    build_context = Context()

    for name, task in ligamentfile.ligament_tasks.iteritems():
        if isinstance(task, BuildTarget):
            pout("registered task '%s'" % name, groups=["debug"])
            task.register_with_context(name, build_context)
        elif isinstance(task, list):
            BuildTargetList(
                DeferredDependency(t) for t in task
                ).register_with_context(name, build_context)

    to_expose = (
        ligamentfile.exposed_tasks 
            if "exposed_tasks" in dir(ligamentfile)
            else build_context.tasks)

    for name in to_expose:
        if name in build_context.tasks:
            build_context.expose_task(name)
        else:
            perror("task '%s' not declared in ligament file" % name)

    return build_context

def run_skeleton(skeleton_path, tasks, watch=True):
    """loads and executes tasks from a given skeleton file

        skeleton_path:
            path to the skeleton file

        tasks:
            a list of string identifiers of tasks to be executed

        watch:
            boolean flag of if the skeleton should be watched for changes and
            automatically updated
    """

    build_context = load_context_from_skeleton(skeleton_path);

    # for t in build_context.tasks:
    #     print t, str(build_context.tasks[t])

    for task in tasks:
        build_context.build_task(task)


    # print json.dumps(
    #     dict((name,
    #          str(task.value)[0:100] + "..."
    #          if 100 < len(str(task.value))
    #          else str(task.value))

    #          for name, task in build_context.tasks.iteritems()),
    #     indent=2)

    if watch:
        print
        print "resolving watch targets"

        # establish watchers
        observer = Observer()
        buildcontexteventhandler = BuildContextFsEventHandler(build_context)
        built_tasks = ((taskname, task) 
                       for taskname, task in build_context.tasks.iteritems()
                       if task.last_build_time > 0)
        for taskname, task in built_tasks:
            for f in task.task.file_watch_targets:
                if os.path.isdir(f):
                    print "%s: watching %s" % (taskname, f)
                    observer.schedule(
                        buildcontexteventhandler,
                        f,
                        recursive=True)
                else:
                    print "%s: watching %s for %s" % (taskname, os.path.dirname(f),
                                                      os.path.basename(f))
                    dirname = os.path.dirname(f)
                    observer.schedule(
                        buildcontexteventhandler,
                        dirname if dirname != "" else ".",
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

def query_skeleton(skeleton_path):
    build_context = load_context_from_skeleton(skeleton_path);

    return [name 
            for name, task in build_context.tasks.iteritems() 
            if task.exposed]
