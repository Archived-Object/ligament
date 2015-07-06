import os
import glob
import shutil
from buildtarget import BuildTarget
from helpers import mkdir_recursive

class Copy(BuildTarget):

    def __init__(self, filemap, **kwargs):
        BuildTarget.__init__(self, **kwargs)

        self.filemap = filemap

    def build(self, template_scripts="", template_styles=""):
        for key in self.filemap:
            targets = glob.glob(key)

            if len(targets) == 1 and key == targets[0]:
                # if it's not a glob, copy to specified filename
                mkdir_recursive(
                    os.path.dirname(self.filemap[key]))
                _copyfile_(targets[0], self.filemap[key])

            else:
                # otherwise, copy it to the folder
                mkdir_recursive(self.filemap[key])
                for f in targets:
                    _copyfile_(f, self.filemap[key])

def _copyfile_(src, dest):
    if os.path.isdir(src):
        if os.path.exists(dest):
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
    else:
        if os.path.isdir(dest):
            bn = os.path.basename(src)
            dest = os.path.join(dest, bn)
        shutil.copyfile(src, dest)

