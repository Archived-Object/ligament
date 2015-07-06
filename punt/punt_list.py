import os
import os
import glob
import shutil
from buildtarget import BuildTarget
from helpers import mkdir_recursive
from buildcontext import DeferredDependency

class BuildTargetList(BuildTarget):

    def __init__(self, filelist):
        depend_map = {}
        for d in filelist:
            depend_map[d] = DeferredDependency(d)

        BuildTarget.__init__(self, data_dependencies = depend_map)

    def build(self, template_scripts="", template_styles=""):
        return
