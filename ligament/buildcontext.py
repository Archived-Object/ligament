from helpers import perror, pdebug, pout
from exceptions import TaskExecutionException
import traceback
import time
import json

""" TODO redo task return values as enums """
""" TODO remove explicit file dependencies and replace them with tasks and
    provides_for relationships
"""


class ContextEntry(object):
    """ A 'dumb' object holding metadata for a given build task """

    def __init__(self, name, task=None):
        self.name = name
        self.task = task
        self.last_build_time = 0
        self.depends_on = []
        self.provides_for = []
        self.value = None
        self.exposed = False

    def __str__(self):
        return json.dumps(dict([(key, str(self.__dict__[key]))
                                for key in filter(
                                lambda s: not s.startswith("_"),
                                self.__dict__)]),
                          indent=2)


class Context(object):
    """ A sandboxed area that manages a set of build tasks and their
        dependencies
    """

    tasks = {}
    """ A dict of ContextEntries by task name """

    def register_task(self, name, task):
        if name not in self.tasks:
            self.tasks[name] = ContextEntry(name, task)
        elif not self.tasks[name].task:
            self.tasks[name].task = task
        else:
            perror("tried to register duplicate tasks under name \"%s\"" %
                   (name))

    def _gettask(self, name):
        if name not in self.tasks:
            self.tasks[name] = ContextEntry(name)
        return self.tasks[name]

    def register_dependency(self, data_src, data_sink):
        """ registers a dependency of data_src -> data_sink
            by placing appropriate entries in provides_for and depends_on
        """

        pdebug("registering dependency %s -> %s" % (data_src, data_sink))

        if (data_src not in self._gettask(data_sink).depends_on):
            self._gettask(data_sink).depends_on.append(data_src)

        if (data_sink not in self._gettask(data_src).provides_for):
            self._gettask(data_src).provides_for.append(data_sink)

    def build_task(self, name):
        """ Builds a task by name, resolving any dependencies on the way """

        try:
            self._gettask(name).value = (
                self._gettask(name).task.resolve_and_build())
        except TaskExecutionException as e:
            perror(e.header, indent="+0")
            perror(e.message, indent="+4")
            self._gettask(name).value = e.payload
        except Exception as e:
            perror("error evaluating target '%s' %s" %
                   (name, type(self._gettask(name).task)))
            perror(traceback.format_exc(e), indent='+4')
            self._gettask(name).value = None

        self._gettask(name).last_build_time = time.time()

    def is_build_needed(self, data_sink, data_src):
        """ returns true if data_src needs to be rebuilt, given that data_sink
            has had a rebuild requested.
        """
        return (self._gettask(data_src).last_build_time == 0 or
                self._gettask(data_src).last_build_time <
                self._gettask(data_sink).last_build_time)

    def verify_valid_dependencies(self):
        """ Checks if the assigned dependencies are valid
            valid dependency graphs are:

            - noncyclic (i.e. no `A -> B -> ... -> A`)
            - Contain no undefined dependencies
              (dependencies referencing undefined tasks)
        """

        unobserved_dependencies = set(self.tasks.keys())
        target_queue = []

        while len(unobserved_dependencies) > 0:
            target_queue = [unobserved_dependencies.pop()]

            while target_queue is not []:
                target_queue += unobserved_dependencies

        # verify_provides_depends_match()

    def deep_dependendants(self, target):
        """ Recursively finds the dependents of a given build target.
            Assumes the dependency graph is noncyclic
        """
        direct_dependents = self._gettask(target).provides_for

        return (direct_dependents +
                reduce(
                    lambda a, b: a + b,
                    [self.deep_dependendants(x) for x in direct_dependents],
                    []))

    def resolve_dependency_graph(self, target):
        """ resolves the build order for interdependent build targets

            Assumes no cyclic dependencies
        """
        targets = self.deep_dependendants(target)
        # print "deep dependants:", targets
        return sorted(targets,
                      cmp=lambda a, b:
                          1 if b in self.deep_dependendants(a) else
                          -1 if a in self.deep_dependendants(b) else
                          0)

    def update_task(self, taskname, ignore_dependents=[]):
        pout("updating task %s" % taskname)
        last_value = self._gettask(taskname).value
        self.build_task(taskname)

        if last_value != self._gettask(taskname).value:
            dependent_order = self.resolve_dependency_graph(taskname)
            for index, dependent in enumerate(dependent_order):
                if (dependent not in ignore_dependents and
                        self.tasks[dependent].last_build_time > 0):
                    self.update_task(
                        dependent,
                        ignore_dependents=dependent_order[index:])
        else:
            pdebug("no change in %s" % taskname)

    def lock_task(self, name):
        pass

    def unlock_task(self, name):
        pass

    def expose_task(self, name):
        self.tasks[name].exposed = True


class DeferredDependency(object):

    def __init__(self, *target_names, **kw):
        # python2 2.7 workaround for kwargs after target_names
        self.function = kw.get(
            'function',
            lambda **k: k.values()[0] if len(k) == 1 else k)
        """A kwarg function to be called on the results of all the dependencies
        """

        self.keyword_chain = kw.get('keyword_chain', [])
        """The chain of attribute accesses on each target"""

        self.parent = None
        """The name of the object this dependency provides for.
           (Assigned in BuildTarget.register_with_context)"""

        self.context = None
        """The context this dependency operates in"""

        self.target_names = target_names
        """The name of buildtargets this DeferredDependency operates on"""

    def resolve(self):
        """Builds all targets of this dependency and returns the result
           of self.function on the resulting values
        """
        values = {}
        for target_name in self.target_names:
            if self.context.is_build_needed(self.parent, target_name):
                self.context.build_task(target_name)

            if len(self.keyword_chain) == 0:
                values[target_name] = self.context.tasks[target_name].value
            else:
                values[target_name] = reduce(
                    lambda task, name: getattr(task, name),
                    self.keyword_chain,
                    self.context.tasks[target_name].task)
        return self.function(**values)

    def get_context(self):
        return self.context

    def get_parent(self):
        return self.context

    def __getattr__(self, name):
        return DeferredDependency(
            *self.target_names,
            function=self.function,
            keyword_chain=(self.keyword_chain + [name]))
