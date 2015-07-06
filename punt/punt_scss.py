import os
import scss

from buildtarget import Precompiler
from helpers import mkdir_recursive, map_over_glob, zip_with_output


class Scss(Precompiler):
    inline_template_string = (
        "<link rel='stylesheet' type='text/css' href='./css/%s'></link>")

    embed_template_string = "<style>%s</style>"

    default_kwargs = {
        "minify": True,
        "inline": True,
        "source_dir": "template/css",
        "target_dir": "build/css",
        "build_targets": ["*"]
    }

    def __init__(self, **kwargs):
        calling_kwargs = Scss.default_kwargs.copy()
        calling_kwargs.update(**kwargs)
        Precompiler.__init__(self, **calling_kwargs)

        self.compiler = scss.Scss({"compress": self.minify})

        self.file_watch_targets = [
            os.path.join(self.input_directory, "*.scss"),
            os.path.join(self.input_directory, "*.css")]

    def out_path_of(self, in_path):
        relative_path = os.path.relpath(in_path, self.input_directory)

        if relative_path.endswith(".scss"):
            relative_path = relative_path[0:-4]+"css"

        return os.path.join(self.output_directory, relative_path)

    def compile_file(self, in_path):
        compiled_string = self.compiler.compile(scss_file=in_path)
        return compiled_string
