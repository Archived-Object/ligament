import os
import glob
import shutil
from videomgr import fetch_videos_as_json
from fetchmethods import fetch_gdrive

class VideoFetch(BuildTarget):

    def __init__(self, filemap, **kwargs):
        BuildTarget.__init__(self, **kwargs)

        self.filemap = filemap

    def build(self, credentials_file=""):
        return "var videoData = "fetch_videos_as_json(credentials_file)
