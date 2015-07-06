import os
import glob
import shutil

from helpers import mkdir_recursive
from videomgr import fetch_videos_as_json
from fetch_gdrive import deferred_fetch_gdrive
from fetch_wp import fetch_wp
from buildtarget import BuildTarget

class VideoFetch(BuildTarget):

    def __init__(self, 
            data_directory="data",
            rehost_directory="rehost",
            google_credentials_file="", 
            wordpress_credentials_file="",
            **kwargs):
        
        BuildTarget.__init__(self, **kwargs)
        self.google_credentials_file = google_credentials_file
        self.wordpress_credentials_file = wordpress_credentials_file

        self.data_directory = data_directory
        self.rehost_directory = rehost_directory

    def build(self):
        mkdir_recursive(self.data_directory)

        return "<script>" + fetch_videos_as_json(
            self.data_directory,
            self.rehost_directory,
            fetchers={
                "google-drive": deferred_fetch_gdrive(self.google_credentials_file),
                "pt-wordpress": fetch_wp
            }) + "</script>"
