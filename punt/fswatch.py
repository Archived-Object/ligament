import buildcontext

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class BuildContextEventHandler(FileSystemEventHandler):

    def __init__(self, context):
        self.context = context

        self.file_depends = {}
        for name, task in context.tasks:
            glob_targets = reduce(
                sum,
                glob.glob(task.file_watch_targets),
                [])

            for file_target in glob_targets:
                if file_target in self.file_depends
                    self.file_depends[file_target].append(name)
                else:
                    self.file_depends[file_target] = [name]

    def on_modified(self, event): 
        print "%s modified" % event.src_path
        if event.src_path in self.file_depends:
            self.context.update_task(self.file_depends[event.src_path])

