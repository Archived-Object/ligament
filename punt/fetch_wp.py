import requests

import datetime
import httplib2
import re
import os

import json

from urllib import unquote

from bs4 import BeautifulSoup


hash_regex = re.compile("#\w+(?=[^\w])")
jvideo_thumbnail_regex = re.compile("\&image=http.*(?:\.jpg)")

placeholder = "./placeholder.png"

def get_tags_from_description(s):
    """ gets #tags from a description """
    hits = hash_regex.findall(s)
    return [m[1:] for m in hits] if hits else []


def get_tags_from_post(post):
    desc_tags = get_tags_from_description(
        get_description_from_post(post))

    metadata_tags = ([tag["name"] for tag in post["terms"]["post_tag"]] if
        "terms" in post and "post_tag" in post["terms"]
        else [])

    return sorted([t.lower() 
            for t 
            in set(desc_tags + metadata_tags)])


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


def get_description_from_post(post):
    dom = BeautifulSoup(post["content"], 'html.parser')
    return "\n".join([p.text for p in dom.select("span, b")])


def get_thumbnail_from_jvidpost(post):
    hits = jvideo_thumbnail_regex.findall(post["content"])
    if len(hits) == 0:
        return None
    else:
        return unquote(hits[0][7:])


def video_from_wp_post(rehost_dir, post):
    """ Converts a video from wordpress post metadata to this format """

    thumbnail_link = get_thumbnail_from_jvidpost(post)
    if not thumbnail_link:
        thumbnail_link = placeholder

    print "thumbnail link: %s" % thumbnail_link

    tfstr = "%Y-%m-%d %H:%M"

    print "finishing up %s" % (post["title"])
    return {
        "uuid":  str(post["ID"]),
        "date_fetched": datetime.date.today().strftime(tfstr),
        "needs_manual_tagging": True,

        "title": post["title"],
        "image_url": thumbnail_link,
        "date_posted": post["date"][0:16].replace("T", " "),
        "description": get_description_from_post(post),
        "tags": get_tags_from_post(post),
        "source_site": "pt-wordpress",
        "source_link": post["link"],
    }

def fetch_wp(data_directory,
             rehost_directory,
             timestring):
    """ timestring:
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

    wp_timestring = "%sT%s:00" % tuple(timestring.split())

    wp_postlist = requests.get(
        "http://pharmablogs.roche.com/pt-multimedia/",
        params={
            "json_route": "/posts",
            "filter[posts_per_page]": "999999",  # just get all vids
            "filter[category_name]": "PTD videos",  # at least the ones in ptd
        }).json()

    return [video_from_wp_post(rehost_directory, wp_post) 
            for wp_post in wp_postlist
            if wp_post["date"] > wp_timestring]


