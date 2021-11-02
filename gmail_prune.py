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

import base64
import os.path
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
TIME_BEFORE = 24 * 60 * 60 * 1000  # TIME IN ms
MIN_SIZE = 50 * 1024  # 5
MIN_TIME = time.time() * 1000 - TIME_BEFORE
ROOT_DIR = os.path.dirname(
    os.path.abspath(__file__))  # This is your Project Root
ATTACHMENTS_DIR = "attachments"


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
    results = service.users().messages().list(userId='me').execute()
    messages = results["messages"]  # .get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        print('Messages:')
        for m in messages:
            body = service.users().messages().get(userId='me',
                                                  id=m["id"]).execute()
            if "parts" in body["payload"]:
                parts = body["payload"]["parts"]
                for part in parts:
                    if "filename" in part and part["filename"] != "":
                        print("\n ************************ " + m["id"])
                        print("\"" + part["filename"] + "\"")
                        print(body["internalDate"])
                        GetAttachments(service, "me", m["id"])
                    else:
                        print(".", end=" ")


def create_a_path_by_label(message):
    """
    create a path according to the message label
    """
    if message["labelIds"]:
        for i in range(len(message["labelIds"])):
            new_path = ROOT_DIR + message["labelIds"][i]
            if not os.path.exists(new_path):
                os.makedirs(new_path)
    else:
        print("no labels found")


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
        if part['filename']:
            if part['body']['size'] > MIN_SIZE and \
                    int(message["internalDate"]) < int(MIN_TIME):
                if 'data' in part['body']:
                    data = part['body']['data']
                else:
                    att_id = part['body']['attachmentId']
                    att = service.users().messages().attachments().get(
                        userId=user_id, messageId=msg_id, id=att_id).execute()
                    data = att['data']
                file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
                path = part['filename']

                with open(ATTACHMENTS_DIR + "/" + path, 'wb') as f:
                    f.write(file_data)
            else:
                print("not good, size is:", part['body']['size'], "date is:",
                      message["internalDate"])


if __name__ == '__main__':
    main()
# [END gmail_quickstart]
