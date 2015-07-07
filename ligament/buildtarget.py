import os
import glob
from helpers import (
    remove_dups,
    map_over_glob,
    zip_with_output,
    perror,
    mkdir_recursive)

from buildcontext import Context, DeferredDependency


class BuildTarget(object):

    data_dependencies = {}
    file_watch_targets = []

    def __init__(self,
                 data_dependencies={}):
        self.data_dependencies = data_dependencies

    def register_with_context(self, myname, context):
        for key in self.data_dependencies:
            if type(self.data_dependencies[key]) is DeferredDependency:
                self.data_dependencies[key].parent  = myname
                self.data_dependencies[key].context = context
                for tnmame in self.data_dependencies[key].target_names:
                    context.register_dependency(tnmame, myname)
        self.name = myname
        self.context = context
        context.tasks[myname] = self

    def resolve_dependencies(self):
        return dict(
            [(
                (key, self.data_dependencies[key])
                if type(self.data_dependencies[key]) != DeferredDependency
                else (key, self.data_dependencies[key].resolve())
             ) for key in self.data_dependencies])

    def resolve_and_build(self):
        print "resolving and building task '%s'" % self.name
        return self.build(**self.resolve_dependencies())

    def build(self):
        """ perform some task and return a list of watched files"""
        raise Exception("build not implemented for %s" % type(self))
        pass

    def update_build(self, changedfiles):
        raise Exception("update_build not implemented for %s" % type(self))
        pass
