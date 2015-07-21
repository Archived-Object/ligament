import glob
from watchdog.events import FileSystemEventHandler


class BuildContextFsEventHandler(FileSystemEventHandler):
    """ A file system event handler for WatchDog that updates build tasks
        (specified by glob in task.file_watch_targets).
    """


    def __init__(self, context):
        self.context = context

        self.file_depends = {}
        for name, task in context.tasks.iteritems():
            glob_targets = reduce(
                lambda a, b: a + b,
                [glob.glob(x) for x in task.task.file_watch_targets],
                [])

            for file_target in glob_targets:
                if file_target in self.file_depends:
                    self.file_depends[file_target].append(name)
                else:
                    self.file_depends[file_target] = [name]

    def on_modified(self, event):
        print 
        print "%s modified" % event.src_path
        if event.src_path in self.file_depends:
            for name in self.file_depends[event.src_path]:
                self.context.lock_task(name)
                self.context.update_task(name)
                self.context.unlock_task(name)
