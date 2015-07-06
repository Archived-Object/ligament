from helpers import perror


class Context(object):
    tasks = {}
    value_table = {}
    build_stack = []

    provides_for = {}
    depends_on = {}

    built = []

    def register_dependency(self, data_src, data_sink):
        """ place entries in provides_for and depends_on """
        print "registered dependency %s -> %s" % (data_src, data_sink)

        if data_sink in self.depends_on:
            if data_src not in self.depends_on[data_sink]:
                self.depends_on[data_sink].append(data_src)
        else:
            self.depends_on[data_sink] = [data_src]

        if data_src in self.provides_for:
            if data_sink not in self.provides_for[data_src]:
                self.provides_for[data_src].append(data_sink)
        else:
            self.provides_for[data_src] = [data_sink]

    def build_task(self, name):
        if name not in self.build_stack:
            self.build_stack.append(name)
            self.value_table[name] = self.tasks[name].resolve_and_build()
            self.build_stack = self.build_stack[0:-1]
        else:
            perror("cyclic dependency on %s." % name)
            perror("build stack %s" % ", ".join(self.build_stack))

        if name not in self.built:
            self.built.append(name)

    def is_build_needed(self, data_sink, data_src):
        return (data_src not in self.value_table)

    def deep_dependendants(self, target):
        direct_dependents = (self.provides_for[target]
                             if target in self.provides_for
                             else [])

        return (direct_dependents +
                reduce(
                    lambda a, b: a + b,
                    [self.deep_dependendants(x) for x in direct_dependents],
                    [])
                )

    def resolve_dependency_graph(self, target):
        """ resolves the build order for interdependent build targets

            Assumes no cyclic dependencies
        """
        targets = self.deep_dependendants(target)
        return sorted(targets,
                      cmp=lambda a, b:
                          1  if b in self.deep_dependendants(a) else 
                          -1 if a in self.deep_dependendants(b) else
                          0)

    def update_task(self, taskname, ignore_dependents=[]):
        print "updating task %s" % taskname
        last_value = (None
                      if taskname not in self.value_table
                      else self.value_table[taskname])

        self.build_task(taskname)

        if last_value != self.value_table[taskname]:
            dependent_order = self.resolve_dependency_graph(taskname)
            for index, dependent in enumerate(dependent_order):
                if (dependent not in ignore_dependents and
                        dependent in self.built):
                    self.update_task(
                        dependent,
                        ignore_dependents=dependent_order[index:])


def build_lst(a, b):
        if type(a) is list:
            return a + [b]
        elif a:
            return [a, b]
        else:
            return b


class DeferredDependency(object):
    def __init__(self, *target_names, **kw):
        # python2 2.7 kwargs workaround
        foldfn = kw.get('foldfn', build_lst)
        foldi = kw.get('foldi', None)

        self.target_names = target_names
        # print target_names

        self.last_update = 0
        self.context = None

        self.foldfn = foldfn
        self.foldi = foldi

    def resolve(self):
        value = self.foldi
        for target_name in self.target_names:
            if self.context.is_build_needed(self.parent, target_name):
                self.context.build_task(target_name)

            value = self.foldfn(
                value,
                self.context.value_table[target_name])
        # print self.target_names, type(value)
        return value
