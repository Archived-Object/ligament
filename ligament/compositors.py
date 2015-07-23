from buildtarget import BuildTarget
from buildcontext import DeferredDependency
import math

from helpers import pdebug
import json


class BuildTargetFn(BuildTarget):
    """ Calls a function on the results of a list of build tasks (positionally)
    """

    def __init__(self, fn, *tasklist):
        self.fn = fn

        tl = ((("%0" + str(math.ceil(math.log(len(tasklist), 10))) + "d") % k, v)
              for k, v in enumerate(tasklist))
        d = dict(tl)

        BuildTarget.__init__(self, d)

    def build(self, **dependencies):
        return self.fn(*(dependencies[key]
                       for key in sorted(dependencies.keys())))


class BuildTargetList(BuildTargetFn):
    """An empty build target meant only to depend on other targets"""

    def __init__(self, tasklist):
        BuildTargetFn.__init__(self, lambda *args: args, *tasklist)


class BuildTargetFold(BuildTarget):
    """Folds a function over the results of a set of build targets"""

    def __init__(self, foldi, foldfn, *tasklist):
        self.foldi = foldi
        """the initial value for the fold"""

        self.foldfn = foldfn
        """the function to fold with"""

        tl = ((("%" + str(len(tasklist)) + "d") % k, v)
              for k, v in enumerate(tasklist))
        d = dict(tl)

        BuildTarget.__init__(self, d)

    def build(self, **dependencies):
        return reduce(
            self.foldfn,
            (dependencies[key] for key in sorted(dependencies.keys())),
            self.foldi)

class BuildTargetMap(BuildTarget):
    """Folds a function over the results of a set of build targets"""

    def __init__(self, task, binding={}):
        self.task = task;

        BuildTarget.__init__(self, binding)

    def register_with_context(self, myname, context):
        BuildTarget.register_with_context(self, myname, context)
        self.task.name = myname + ".mapped_task" 


    def build(self, **binding):
        # print [(key, type(val), len(val) if isinstance(val, list) else "") 
        #        for key, val in binding.iteritems()]

        minlen = -1
        for name, values in binding.iteritems():
            if isinstance(values, list):
                if minlen == -1:
                    minlen = len(values)
                else:
                    minlen = min(minlen, len(values))

        outputs = []
        for index in range(0, minlen):
            calling_args = {}
            for name, values in binding.iteritems():
                calling_args[name] = (values[index]
                                      if isinstance(values, list)
                                      else values)
            outputs.append(self.task.build(**calling_args))


        return outputs
