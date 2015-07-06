from oauth2client.file import Storage
from apiclient.discovery import build

import datetime
import httplib2
import re
import os

import json

from helpers import urlretrieve


hash_regex = re.compile("#\w+(?=[^\w])")


def get_tags_from_description(s):
    """ gets #tags from a description """
    hits = hash_regex.findall(s)
    return [m[1:] for m in hits] if hits else []


def remove_known_files(save_dir, fileslist):
    """ removes already downloaded data from a sorted list of metadata

        save_dir:
            The path to the save directory

        fileslist:
            A sorted list of metadata objects, in reverse chronological order
    """
    i = 0
    while (i < len(fileslist) and
           not os.path.exists(
            os.path.join(
                save_dir,
                fileslist[i]["uuid"] + ".json"))):
        i += 1
    return fileslist[0:i]


def fetch_pt_wordpress(cfg, time):
    """ fetches new videos from the pt multimedia wordpress blog """
    return []


def video_from_gdrive_file(drive, rehost_dir, vid):
    """ Converts a video from google-drive's metadata format to this format """

    # download and rehost the thumbnail, because thumbnails provided by
    # google expire in ~ 1hr
    thumbnail_link = (vid["thumbnailLink"]
                      if "thumbnailLink" in vid
                      else None)

    # save the thumbnail image locally if it was specified
    vid_uuid = str(vid["id"])
    if thumbnail_link:
        local_img_url = "./%s" % vid["id"]

        urlretrieve(
            thumbnail_link,
            os.path.join(
                rehost_dir,
                "img",
                "google-drive",
                local_img_url))

    # otherwise, download it and generate a thumbnail
    else:
        local_img_url = "./placeholder.gif"

    description = (vid["description"] if
                   "description" in vid
                   else "")

    tfstr = "%Y-%m-%d %H:%M"


    print "finishing up %s" % (vid["title"])
    return {
        "uuid": vid_uuid,
        "date_fetched": datetime.date.today().strftime(tfstr),
        "needs_manual_tagging": True,

        "title": vid["title"],
        "image_url": local_img_url,
        "date_posted": vid["createdDate"][0:16].replace("T", " "),
        "description": description,
        "tags": get_tags_from_description(description),
        "source_site": "google-drive",
        "source_link": vid["alternateLink"],
    }


def gdrive_list_map(drive, query_string, f=lambda a: a):
    """ query drive.list with a given string and map a fn over the result

        drive:
            the built drive api object

        query_string:
            the filter string to query with

        f:
            the function to map over the search results
    """

    output = []

    # go through the list of files
    page_ct = 0
    page_token = None
    while page_ct == 0 or page_token is not None:

        this_page = drive.files().list(
            q=query_string,
            corpus="DOMAIN",  # only query items owned/shared to user
            spaces="drive",   # only query in google-drive
            pageToken=page_token).execute()

        output += filter(
            lambda a: a,
            [f(v) for v in this_page["items"]])

        page_token = (this_page["nextPageToken"]
                      if "nextPageToken" in this_page
                      else None)
        page_ct += 1

    return output


def deferred_fetch_gdrive(credentials_file):
    def wrapper(data_directory,
                rehost_directory,
                timestring):
        return fetch_gdrive(
            credentials_file,
            data_directory,
            rehost_directory,
            timestring)
    return wrapper


def fetch_gdrive(credentials_file,
                 data_directory,
                 rehost_directory,
                 timestring):
    """ fetches new videos from google-drive

        cfg:
            object containing field GOOGLE_DRIVE_CREDENTIALS, the path
            to some stored google drive credentials

        timestring:
            string of form "YYYY-MM-DD HH:MM" for the most recently updated

        returns a list of objects of the form
        {
            uuid: "...",
            date_fetched: "YYYY-MM-DD HH:MM",
            needs_manual_tagging: true/false,

            title: "...",
            image_url: "...",
            date_posted: "YYYY-MM-DD HH:MM",
            description: "...",
            tags: ["...", ...],
            source_site: "google-drive" / "pt-wordpress",
            source_link: "..."
            <original_url: "...">
        }


    """

    # Authorize with google drive
    storage = Storage(credentials_file)
    credentials = storage.get()
    http = credentials.authorize(httplib2.Http())
    drive = build('drive', 'v2', http=http)

    # get a google-format timestring for the last updated object
    google_timestring = "%sT%s:00" % tuple(timestring.split())

    # get a list of folders shared to me
    folder_query_string = "mimeType contains 'folder' and sharedWithMe"
    getfolderid = lambda folder: folder["id"]
    folder_ids = gdrive_list_map(drive, folder_query_string, getfolderid)

    in_shared_query_string = " or ".join(
        ["'%s' in parents" % p for p in folder_ids])

    # get new files in shared folder
    video_query_string = ("modifiedDate >= '%s' "
                          "and mimeType contains 'video'"
                          "and (sharedWithMe or (%s))" %
                          (google_timestring, in_shared_query_string))

    mkvideo = lambda v: video_from_gdrive_file(drive, rehost_directory, v)
    found_files = gdrive_list_map(drive, video_query_string, mkvideo)
    save_dir = os.path.join(data_directory, "google-drive")
    return remove_known_files(save_dir, found_files)
