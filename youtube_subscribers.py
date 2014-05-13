#!/usr/bin/python

import httplib2
import os
import sys
import time
import random

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow


# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "client_secrets.json"

# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account.
YOUTUBE_READ_WRITE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the Developers Console
https://console.developers.google.com/

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    scope=YOUTUBE_READ_WRITE_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))


# This method calls the API's youtube.subscriptions.insert method to add a
# subscription to the specified channel.
def getUsers(youtube,pageToken = "", maxResults=5,users=[]):
  if pageToken == "":
    response = youtube.subscriptions().list(
      part='snippet',
      mySubscribers=True,
      maxResults=maxResults,
      order = "alphabetical"
        ).execute()
  else:
    response = youtube.subscriptions().list(
      part='snippet',
      mySubscribers=True,
      maxResults=maxResults,
      order = "alphabetical",
      pageToken = pageToken
        ).execute()
  nextPageToken = response.get('nextPageToken')
  processed = [[u['snippet']['channelId'], u['snippet']['publishedAt']] for u in response['items']]

  for u in processed:
    print u
  return [[u['snippet']['channelId'], u['snippet']['publishedAt']] for u in response['items']], nextPageToken
	

if __name__ == "__main__":
  argparser.add_argument("--channel-id", help="ID of the channel to subscribe to.",
    default="UCtVd0c0tGXuTSbU5d8cSBUg")
  args = argparser.parse_args()

  youtube = get_authenticated_service(args)
  master_user_list = []
  nextPageToken = ""
  pageLimit = 750
  pageCount = 0
  errCount = 0
  errLimit = 10
  userTotal = 0
  wait = 1
  regular_wait = 45
  while nextPageToken is not None and pageCount < pageLimit and errCount < errLimit:
    try:
      users, nextPageToken = getUsers(youtube,maxResults=50,pageToken = nextPageToken)
      errCount = 0
      wait = 1
      userTotal += len(users)
      print "%s users collected"%userTotal
      master_user_list += users
      pageCount += 1
      regular_wait = regular_wait * 1.1
    except HttpError,e:
      print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)
      print "%s tries out of %s, waiting %s seconds"%(errCount, errLimit,wait)
      time.sleep(wait)
      wait = (2*random.random())
      errCount += 1
    time.sleep(regular_wait)
      
  outString = ""
  for u in master_user_list:
    outString += "%s,%s\n"%(u[0],u[1])
  print outString
  with open('output.txt', 'w') as f:
    f.write(outString) 
