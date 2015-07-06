#!/usr/bin/python
# Python 2.7
# a simple script for generating an authorization token for google services

import sys
import traceback
from oauth2client import client
from oauth2client.file import Storage


def exit_with_helptext():
    print
    print "usage: %s <clientsecret>" % (sys.argv[0])
    print "    clientsecret:"
    print "        A clientsecret.json file generated from google, make one @"
    print "        https://console.developers.google.com/"


if __name__ == "__main__":
    secret_path = sys.argv[1] if len(sys.argv) == 2 else exit_with_helptext()

    print secret_path

    try:
        flow = client.flow_from_clientsecrets(
            secret_path,
            scope='https://www.googleapis.com/auth/drive.readonly',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')

        print "opening broswer pointed at auth server.."
        auth_uri = flow.step1_get_authorize_url()
        print "open '%s' in browser " % auth_uri

        auth_code = ""
        while auth_code == "":
            auth_code = raw_input("\nauth code: ")

        credentials = flow.step2_exchange(auth_code)
        strcredentials = credentials.to_json()

        print strcredentials

        out_path = ""
        while out_path == "":
            out_path = raw_input("\save as: ")

        storage = Storage(out_path)
        storage.put(credentials)

    except Exception as e:
        print "error: %s" % e
        traceback.print_exception(*sys.exc_info())
        exit_with_helptext()
