#!/usr/bin/python

import re
import os
import json
import uuid

from fetchmethods import fetch_pt_wordpress, fetch_gdrive
from helpers import mkdir_recursive, partition

#######################
#                     #
# Metadata Validation #
#                     #
#######################


DATE_REGEXP = re.compile("\d{4}-\d{2}-\d{2} \d{2}:\d{2}")


def valid_date(s):
    return (None
            if DATE_REGEXP.match(s)
            else "date '%s' does not match formant YYYY-MM-DD HH:SS" % s)


def valid_url(s):
    return (None
            if (s.startswith("http://") or
                s.startswith("https://") or
                s.startswith("./"))
            else "url does not start with 'http://', 'https://', or './'")


def valid_source(s):
    return (None
            if (s == "google-drive" or
                s == "pt-wordpress")
            else "is not valid source")


def is_a(*ts):
    return lambda x: type(x) in ts


def of_type(*ts):
    return lambda x: (
        None
        if type(x) in ts
        else "expected type %s, got %s" % (
            ", ".join([str(t) for t in ts]),
            type(x))
    )


def list_of_type(*ts):
    return lambda l: (
        None
        if type(l) == list and all([type(x) in ts for x in l])
        else "expected list of %s, got %s" % (
            ", ".join(ts),
            [type(x) for x in l])
    )


def equal_to(val):
    return lambda x: (
        None
        if x == val
        else "not equal to %s" % val
    )


FIELD_VALIDATORS = {
    "date_posted":             valid_date,
    "date_fetched":            valid_date,
    "source_site":             valid_source,
    "source_link":             valid_url,
    "image_url":               valid_url,
    "description":             of_type(str, unicode),
    "needs_manual_tagging":    of_type(bool),
    "tags":                    list_of_type(str, unicode)
}


def validate_internal_metadata(m):
    """ check that a metadata dict is well-formed
        dict{Valid Metadata} -> (dict | String)

        Valid video objects are of the form
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

        All urls must start with "http://" or "./"
        Urls starting with "./" will be treated as relative to the rehost dir

        The original_url field is optional, and should only be specified if the
        soutce_link is to rehosted content
    """

    for field_name, validator in FIELD_VALIDATORS.iteritems():
        # Call all the validators on the appropriate fields of m. If one fails,
        # return an error message. Otherwise, return the object
        if field_name not in m:
            return "field %s not defined" % field_name

        validator_msg = validator(m[field_name])
        if is_a(str, unicode)(validator_msg):
            return "%s : %s" % (field_name, validator_msg)

    # check if original_url is a url if it exists
    if "original_url" in m:
        validator_msg = valid_url(FIELD_VALIDATORS["original_url"])

        if (is_a(str, unicode)(validator_msg)):
            return "%s : %s" % (field_name, validator_msg)

    return m


def load_and_verify_metadata(path):
    """ loads a video metadata dict by path and verifies it is well formed
        str -> dict{Valid Metadata}

        Takes the path to a json file, and returns either
            - The contents of the file as a python dict, if it passes
                all the validators
            - A str describing what went wrong while trying to validate the
                json

        See validate_internal_metadata for a description of valid video objects

        In addition, the "uuid" field of the object must be the same as the
        filename of the file it is stored in (ignoring the .json extension)
    """

    if path[-5:] != ".json":
        return "%s : filename does not end with '.json'" % path

    with open(path, "r") as f:
        m = validate_internal_metadata(json.load(f))

    if type(m) is str:
        return "%s @ %s" % (path, m)

    basename = os.path.basename(path)
    if of_type(unicode, str)(m["uuid"]) and basename[0:-5] != m["uuid"]:
        return "%s : field 'uuid' (%s) not the same as filename (%s)" % (
            path, m["uuid"], path[0:-5])

    return m


def expand_metadata_urls(m, rehost_dir):
    """ expands short urls in metadata to their full locations
        (dict, string) -> string
    """
    if m["image_url"].startswith("./"):
        m["image_url"] = os.path.join(
            "img",
            m["source_site"],
            m["image_url"][2:])

    if m["source_link"].startswith("./"):
        m["source_link"] = os.path.join(
            "video",
            m["source_site"],
            m["source_link"][2:])
    return m


def format_for_output(rehost_dir, v):
    x = expand_metadata_urls(v, rehost_dir)

    del x["date_fetched"]
    del x["needs_manual_tagging"]

    return x


def load_all_metadata(data_path, rehost_dir="rehost"):
    """ loads all metadata files in a directory
        str -> [str]

        Generates a list of metadata dicts from the content of the data
        directory

        Expected contents of the data directory are '<uuid>.json' files, with
        contents matching the format given in load_and_verify_metadata()

    """
    # get a list of paths to load
    files = reduce(
        sum,
        [[os.path.join(p, f) for f in os.listdir(os.path.join(data_path, p))]
         for p in os.listdir(data_path)],
        [])

    metadata_fnames = filter(
        lambda fname: fname.endswith(".json"),
        files)
    metadata_paths = [
        os.path.join(data_path, fname)
        for fname in metadata_fnames]

    # attempt to load each one
    load_attempts = (load_and_verify_metadata(p) for p in metadata_paths)

    # split into successed and failures
    successes, failures = partition(
        lambda (_, parsed_metadata): type(parsed_metadata) is dict,
        zip(metadata_paths, load_attempts))

    # print loading error messages
    for _, reason in failures:
        print "failed parsing:\n  %s" % reason

    # return successfully parsed metadata
    return [expand_metadata_urls(meta, rehost_dir) for (_, meta) in successes]


##############################
# Methods of Fetching Videos #
##############################

    # return [{
    #     "date_fetched": "0000-00-00 00:00",
    #     "needs_manual_tagging": True,

    #     "title": "video 2",
    #     "image_url": "http://www.lorempixel.com/208/117/business/1",
    #     "date_posted": "2015-06-12 15:00",
    #     "description":  "Lorem ipsum dolor sit amet, consectetur "
    #                     "adipiscing elit. Sed tempus ac neque ac semper",
    #     "tags": ["another", "video", "new!"],
    #     "source_site": "google-drive",
    #     "source_link": "http://www.purple.com"
    # }]

    return []


DEFAULT_FETCHERS = {
    "pt-wordpress": fetch_pt_wordpress,
    "google-drive": fetch_gdrive
}


def save_new_video(data_path, video):
    """ saves a video in the data directory with a new unique uuid
        String, dict -> ()

        generates uuids for the video until one is found with no collision,
        then assigns that value to the uuid and saves it as a json file in the
        data_path directory

        data_path:
            Rhe directory to store json objects in

        video:
            A dictionary representing a valid video, checked against
            validate_internal_metadata
    """
    if("uuid" not in video):
        hex_uuid = uuid.uuid4().hex
        # This should take care of the (statistically negligible)
        # chance of a UUID collision
        while (os.path.exists(
                os.path.join(
                    data_path,
                    hex_uuid  + ".json"
                ))):
            hex_uuid = uuid.uuid4().hex()
        video["uuid"] = hex_uuid

    data_path_source = os.path.join(data_path, video["source_site"])
    filepath = os.path.join(data_path_source, video["uuid"] + ".json")
    mkdir_recursive(data_path_source)

    with open(filepath, 'w') as f:
        f.write(json.dumps(video, indent=2))


def validate_and_save(new_videos, data_path):
    for video in new_videos:
        verified = validate_internal_metadata(video)
        if video is verified:
            save_new_video(data_path, video)
        else:
            print "error in generated video from %s:" % video["source_site"]
            print "  %s" % verified


def get_oldest_post(old_videos, source):
    post_src_time_pairs = [(ov["source_site"], (ov["date_posted"]))
                           for ov in old_videos]

    """ get time of oldest post. if no posts, return unix time 0 """
    pairs_from_src = filter(
        lambda (s, _): s == source,
        post_src_time_pairs)

    times_from_src = [time for (_, time) in pairs_from_src]
    if len(times_from_src) > 0:
        return (source, max(times_from_src))
    return (source, "1970-01-01 00:00")


def fetch_videos(data_directory, rehost_directory, fetchers=DEFAULT_FETCHERS):
    """ loads old videos from data_path and
        str, (str->[dict]), <str> -> [dict]

        data_path:
            the directory where the metadata should be stored

        fetchers:
            a list of methods that will

    """

    # Go through the list of old videos already known, and figure out when the
    # last posting of each video waswha

    # get the oldest posts from each fetcher
    old_videos = load_all_metadata(data_directory, rehost_directory)
    oldest_posts = dict(
        [get_oldest_post(old_videos, source) for source in fetchers])

    # get new videos
    new_videos = reduce(
        lambda a, b: a + b,
        (fetchers[site](
            data_directory,
            rehost_directory,
            oldest_posts[site])
         for site in fetchers))

    # verify and save each new video to a file
    validate_and_save(new_videos, data_directory)

    return [format_for_output(rehost_directory, v) for v in old_videos + new_videos]


def fetch_videos_as_json(*args, **vargs):
    return "videoData = %s" % (
        json.dumps(fetch_videos(*args, **vargs), indent=2))


if __name__ == "__main__":
    # this file should not be run as main, this code is for testing purposesc
    # only

    metadata = fetch_videos("data")

    print "all metadata:\n  %s" % json.dumps(metadata, indent=2)
