# Copyright 2018 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START gmail_quickstart]
from __future__ import print_function

import os
import argparse
import base64
import datetime

from dateutil.parser import parse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

parser = argparse.ArgumentParser(description='Process some values.')


parser.add_argument('--tags', metavar='tags', action='append', nargs='+',
                    help='list of tags')

parser.add_argument('--size', metavar='min_size<GB>', type=float,
                    help='the minimum size of the attachment to process')

parser.add_argument('--age', metavar='min-age<number of days>', type=int,
                    help='the youngest email to process')

parser.add_argument('--until', metavar='until<date>',
                    help='only messages before <date> will be processed')

parser.add_argument('--location', metavar='location', required=True,
                    help='the location to storage')

parser.add_argument('--account', metavar='account',
                    help='email account to use')

args = parser.parse_args()

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


MIN_SIZE = args.size
MIN_TIME = args.age
ROOT_DIR = os.path.dirname(
    os.path.abspath(__file__))  # This is your Project Root
ATTACHMENTS_DIR = args.location
if args.age and args.until:
    min_age = datetime.datetime.now() - datetime.timedelta(args.age)
    MIN_TIME = min(min_age, parse(args.until))
elif args.age:
    MIN_TIME = datetime.datetime.now() - datetime.timedelta(args.age)
    print("using age, date is ", MIN_TIME)
elif args.until:
    MIN_TIME = parse(args.until)
    print("using until, date is ", MIN_TIME)
else:
    print("must specify either ---until or --age")


def legal_name(str):
    new_str = ""
    for ch in str:
        if ch.isalpha() or ch == '_':
            new_str += ch
    return new_str


LIST_OF_TAGS = []
for smallList in args.tags:
    for part in smallList:
        list_part = part.split(',')
        for tag in list_part:
            LIST_OF_TAGS.append(legal_name(tag))



def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail messages.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().messages().list(userId=args.account).execute()
    messages = results["messages"]  # .get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        print('Messages:')
        for m in messages:
            message = service.users().messages().get(userId='me',
                                                     id=m["id"]).execute()
            if "parts" in message["payload"]:
                parts = message["payload"]["parts"]
                for part in parts:
                    if "filename" in part and part["filename"] != "":
                        print("\n ************************ " + m["id"])
                        print("\"" + part["filename"] + "\"")
                        print(message["internalDate"])
                        GetAttachments(service, "me", m["id"])
                    else:
                        print(".", end=" ")


def GetAttachments(service, user_id, msg_id):
    """Get and store attachment from Message with given id.

    :param service: Authorized Gmail API service instance.
    :param user_id: User's email address. The special value "me" can be used to
     indicate the authenticated user.
    :param msg_id: ID of Message containing attachment.
    """

    message = service.users().messages().get(userId=user_id,
                                             id=msg_id).execute()

    for part in message['payload']['parts']:
        message_until = datetime.datetime.fromtimestamp(
            (int(message["internalDate"])) / 1000)
        if part['filename']:
            if part['body']['size'] > MIN_SIZE and \
                    message_until < MIN_TIME:
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(
                        userId=user_id, messageId=msg_id, id=att_id).execute()
                    data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                name_with_label = part["filename"]
                if "labelIds" in message:
                    for label in message["labelIds"]:
                        name_with_label += "-" + label

                path = name_with_label
                print(message["internalDate"])
                try:
                    os.makedirs(ATTACHMENTS_DIR + "/" + path)
                except FileExistsError:
                    # directory already exists
                    pass
                with open(ATTACHMENTS_DIR + "/" + path, 'wb') as f:
                    f.write(file_data)
            else:
                print("not good, size is:", part['body']['size'], "date is:",
                      message_until, " until is ", MIN_TIME)


if __name__ == '__main__':
    main()
# [END gmail_quickstart]
