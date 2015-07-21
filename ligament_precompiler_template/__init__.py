""" An abstract precompiler task for the `ligament` task automator """

import os
import glob
from ligament.helpers import (
    remove_dups,
    zip_with_output,
    mkdir_recursive,
    partition,
    capture_exception)

from ligament.buildtarget import BuildTarget
from ligament.exceptions import TaskExecutionException


class Precompiler(BuildTarget):
    """ A reusable template for a precompiler task

        classes that extend Precompiler must do the following at minimum:

            declare inline_template_string to a template string with a single
            %s, where the value of the compiled filename will be placed

            declare embed_template_string to a template string with a single
            %s, where the compiled file's text will be placed

            declare out_path_of

            declare compile_file

    """

    inline_template_string = None
    embed_template_string = None

    def __init__(self,
                 minify=True,
                 inline=True,
                 source_dir=None,
                 target_dir=None,
                 build_targets=[],
                 relative_directory="./",
                 inline_template_string=None,
                 embed_template_string=None,
                 **kwargs):

        BuildTarget.__init__(self, **kwargs)

        self.relative_directory = relative_directory
        self.input_directory = os.path.abspath(source_dir)
        self.output_directory = os.path.abspath(target_dir)
        self.build_targets = [os.path.abspath(
                              os.path.join(
                                  self.input_directory,
                                  target))
                              for target in build_targets]

        self.file_watch_targets = self.build_targets

        if embed_template_string:
          self.embed_template_string=embed_template_string
        if inline_template_string:
          self.inline_template_string=inline_template_string

        self.minify = minify
        self.embed  = inline

    def out_path_of(self, in_path):
        """given the input path of a file, return the ouput path"""
        raise Exception("Precompiler out_path_of not implemented!")

    def compile_file(self, path):
        """given the path of a file, compile it and return the result"""
        raise Exception("Precompiler compile_file not implemented!")

    @capture_exception
    @zip_with_output(skip_args=[0])
    def compile_and_process(self, in_path):
        """compile a file, save it to the ouput file if the inline flag true"""
        compiled_string = self.compile_file(in_path)

        if not self.embed:
            if compiled_string != "":
                with open(self.out_path_of(in_path), "w") as f:
                    f.write(compiled_string)

        return compiled_string

    def collect_output(self):
        """ helper function to gather the results of `compile_and_process` on
            all target files
        """
        if self.embed:
            concat_scripts = "\n".join(
                [self.compiled_scripts[path]
                 for path in self.collected_build_order])

            return (self.embed_template_string % concat_scripts)
        else:
            return "\n".join(
                [self.inline_template_string %
                 os.path.join(
                     self.relative_directory,
                     os.path.relpath(
                         self.out_path_of(path),
                         self.output_directory))

                 for path in self.collected_build_order
                 if self.compiled_scripts[path] != ""])

    def build(self):
        """build the scripts and return a string"""

        if not self.embed:
            mkdir_recursive(self.output_directory)

        # get list of script files in build order
        self.collected_build_order = remove_dups(
            reduce(lambda a, b: a + glob.glob(b),
                   self.build_targets,
                   []))

        self.compiled_scripts = {}
        exceptions, values = partition(
            lambda x: isinstance(x, Exception),
            [self.compile_and_process(target)
             for target in self.collected_build_order])

        self.compiled_scripts.update(dict(values))

        saneExceptions, insaneExceptions = partition(
            lambda x: isinstance(x, TaskExecutionException),
            exceptions)

        if len(insaneExceptions) != 0:
            raise insaneExceptions[0]

        if len(exceptions) != 0:
            raise TaskExecutionException(
                "Precompiler Errors (%s):" % type(self).__name__,
                "\n".join([
                    x.header + "\n    " +
                    x.message.replace("\n", "\n    ")
                    for x in exceptions]))

        return self.collect_output()

    def update_build(self, updated_files):
        """ updates a build based on updated files
            TODO implement this pls
        """
        for f in updated_files:
            self.compiled_scripts[f] = self.compile_and_process(f)

        return self.collect_output()
