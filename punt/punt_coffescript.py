import os
import glob
import coffeescript

from buildtarget import Precompiler
from helpers import (
    map_over_glob,
    zip_with_output,
    perror,
    remove_dups,
    mkdir_recursive)


def read_as_js(path):
    """ opens a js file by path and returns its contents """
    try:
        with open(path, 'r') as f:
            return f.read()
    except EnvironmentError:
        perror("Could not open build target %s." % (path))
        exit(1)


def read_as_coffee(path):
    """ opens a .coffee file by path, compiles and returns its contents """
    try:
        with open(path, 'r') as f:
            coffee = f.read()
            js = coffeescript.compile(coffee, bare=False)
            return js
    except EnvironmentError:
        perror("Could not open build target %s." % (path))
        exit(1)


class CoffeScript(Precompiler):
    inline_template_string = (
        "<script type='text/javascript' src='./js/%s'></script>")

    embed_template_string = (
        "<script type='text/javascript'>%s</script>")

    default_kwargs = {
         "minify": True,
         "inline": True,
         "source_dir": "template/js",
         "target_dir": "build/js",
         "build_targets": ["*.coffee"]
    }

    def __init__(self, **kwargs):
        calling_kwargs = CoffeScript.default_kwargs.copy()
        calling_kwargs.update(**kwargs)
        Precompiler.__init__(self, **calling_kwargs)

        self.file_watch_targets = [
            os.path.join(self.input_directory, "*.coffee"),
            os.path.join(self.input_directory, "*.js")]

    def out_path_of(self, in_path):
        relative_path = os.path.relpath(in_path, self.input_directory)

        if in_path.endswith(".coffee"):
            relative_path = relative_path[:-6] + "js"

        return os.path.join(self.output_directory, relative_path)

    def compile_file(self, path):
        if path.endswith(".coffee"):
            return read_as_coffee(path)
        elif path.endswith(".js"):
            return read_as_js(path)
        else:
            perror("tried to compile non-script file!")
            exit(1)
