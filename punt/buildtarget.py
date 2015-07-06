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


class Precompiler(BuildTarget):
    """ A reusable """

    inline_template_string = None
    embed_template_string = None

    def __init__(self,
                 minify=True,
                 inline=True,
                 source_dir=None,
                 target_dir=None,
                 build_targets=[],
                 **kwargs):

        BuildTarget.__init__(self, **kwargs)

        self.input_directory = os.path.abspath(source_dir)
        self.output_directory = os.path.abspath(target_dir)
        self.build_targets = [os.path.abspath(
                                os.path.join(
                                    self.input_directory,
                                    target))
                              for target in build_targets]

        self.minify = minify
        self.embed  = inline

    def out_path_of(self, in_path):
        raise Exception("Precompiler out_path_of not implemented!")

    def compile_file(self, path):
        raise Exception("Precompiler compile_file not implemented!")

    def compile_and_process(self, in_path):
        compiled_string = self.compile_file(in_path)

        if not self.embed:
            if compiled_string != "":
                with open(self.out_path_of(in_path), "w") as f:
                    f.write(compiled_string)

        return compiled_string

    def collect_output(self):

        if self.embed:
            concat_scripts = "\n".join(
                [self.compiled_scripts[path]
                 for path in self.collected_build_order])

            return (self.embed_template_string %
                    concat_scripts)
        else:
            return "\n".join(
                    [self.inline_template_string %
                        os.path.relpath(
                            self.out_path_of(path),
                            self.output_directory)
                     for path in self.collected_build_order
                     if self.compiled_scripts[path] != ""])

    def build(self):
        if not self.embed:
            mkdir_recursive(self.output_directory)

        # get list of script files in build order
        self.collected_build_order = remove_dups(
            reduce(lambda a, b: a + glob.glob(b),
                   self.build_targets,
                   []))

        self.compiled_scripts = {}
        for target in self.build_targets:
            self.compiled_scripts.update(dict(
                map_over_glob(
                    zip_with_output(self.compile_and_process),
                    self.input_directory,
                    target)))

        return self.collect_output()

    def update_build(self, updated_files):
        for f in updated_files:
            self.compiled_scripts[f] = self.compile_and_process(f)

        return self.collect_output()


class PuntEcho(BuildTarget):
    """ A simple test build target for pringing information """

    def __init__(self, **kwargs):
        BuildTarget.__init__(self, **kwargs)

    def build(self, **kwargs):
        print "echo called with kwargs = %s" % kwargs
