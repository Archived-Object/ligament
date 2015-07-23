from buildcontext import DeferredDependency
from helpers import pdebug, indent_text


class BuildTarget(object):
    """ An action in ligament
        BuildTargets exist within Build Contexts
           (see ligament.buildcontext.Context)

        Tasks extending buildtarget are expected to pass the keyword argument
        data_dependencies up from their declaration.    
    """

    @property
    def name(self):
        return (self._name 
                if self._name is not None
                else "<unnamed>")

    @name.setter
    def name(self, name):
        self._name = name

    def __init__(self,
                 data_dependencies={}):
        
        self.data_dependencies = data_dependencies
        """ A dict of names -> (DeferredDependencies or values).
            when a build is requested, the DeferredDependencies are evaluated,
            and the resulting dict is passed as kwargs to self.build()

            for example

                SomeBuildTarget(
                    data_dependencies={
                        "foo": DeferredDependency("bar"),
                        "baz": DeferredDependency("quod"),
                        "bul": 4
                    })

            will mean that `SomeBuildTarget.build` is called with kwargs

                SomeBuildTarget.build(
                    foo=<value of bar>,
                    baz=<value of quod>,
                    bul=4)
        """

        self._name = None
        """ The name of this task in its registered build context """

        self.context = None
        """ The build context this target is registered with """

        self.file_watch_targets = []
        """ The list of files this build target wants to be notified of """

    def register_with_context(self, myname, context):
        """ registers this build target (exclusively) with a given context """

        if self.context is not None:
            raise Exception("attempted to register BuildTarget with multiple "
                            "BuildContexts")

        context.register_task(myname, self)
        self._name = myname
        self.context = context

        for key in self.data_dependencies:
            if type(self.data_dependencies[key]) is DeferredDependency:
                self.data_dependencies[key].parent  = myname
                self.data_dependencies[key].context = context
                for tnmame in self.data_dependencies[key].target_names:
                    context.register_dependency(tnmame, myname)

    def resolve_dependencies(self):
        """ evaluate each of the data dependencies of this build target,
            returns the resulting dict"""
        return dict(
            [((key, self.data_dependencies[key])
                if type(self.data_dependencies[key]) != DeferredDependency
                else (key, self.data_dependencies[key].resolve()))
             for key in self.data_dependencies])

    def resolve_and_build(self):
        """ resolves the dependencies of this build target and builds it """
        pdebug("resolving and building task '%s'" % self.name,
                groups=["build_task"])
        indent_text(indent="++2")
        toret = self.build(**self.resolve_dependencies())
        indent_text(indent="--2")
        return toret

    def build(self):
        """ (abstract) perform some task and return the result.
            Also assigns the value f self.file_watch_targets """
        raise Exception("build not implemented for %s" % type(self))
        pass

    def update_build(self, changedfiles):
        """ (abstract) updates the task given a list of changed files """
        raise Exception("update_build not implemented for %s" % type(self))
        pass
