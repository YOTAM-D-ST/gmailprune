# from __future__ import print_function

import os
import argparse
import base64
import datetime

from dateutil.parser import parse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

global args


def set_args():
    global args
    parser = argparse.ArgumentParser(description='Process some values.')
    parser.add_argument('--account', metavar='account', required=True,
                        help='email account to use')
    parser.add_argument('--location', metavar='location', required=True,
                        help='the location to storage')
    parser.add_argument('--tags', metavar='tags', action='append', nargs='+',
                        help='list of tags')
    parser.add_argument('--size', metavar='min_size', type=int,
                        help='the minimum size of the attachment to process',
                        default=10 * 1024 * 1024)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--age', metavar='min-age<number of days>', type=int,
                       help='the youngest email to process')
    group.add_argument('--until', metavar='until<date>',
                       help='only messages before <date> will be processed')
    parser.add_argument('--tags-exclude', metavar='tags-exclude',
                        help='email account to use')
    args = parser.parse_args()
    # If modifying these scopes, delete the file token.json.
    now = datetime.datetime.now()
    if args.age and args.until:
        min_age = now - datetime.timedelta(args.age)
        args.MIN_TIME = min(min_age, parse(args.until))
    elif args.age:
        args.MIN_TIME = datetime.datetime.now() - datetime.timedelta(args.age)
        print("using age, date is ", args.MIN_TIME)
    elif args.until:
        args.MIN_TIME = parse(args.until)
        print("using until, date is ", args.MIN_TIME)
    else:
        args.MIN_TIME = datetime.datetime(now.year - 1, now.month, now.day, now.hour, now.minute)
        print("using default, date is ", args.MIN_TIME)


def parse_size(size):
    units = {"B": 1, "K": 2 ** 10, "M": 2 ** 20, "G": 2 ** 30, "T": 2 ** 40}
    sp = size.split()
    number, unit = [print(string) for string in sp]
    return int(float(number)*units[unit.upper()])


def legal_name(name):
    new_str = ""
    for ch in name:
        if ch.isalpha() or ch == '_':
            new_str += ch
    return new_str


# LIST_OF_TAGS = []
# for smallList in args.tags:
#     for part in smallList:
#         list_part = part.split(',')
#         for tag in list_part:
#             LIST_OF_TAGS.append(legal_name(tag))


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail messages.
    """
    set_args()
    creds = get_creds()

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().messages().list(userId=args.account, q="has:attachment").execute()
    messages = results["messages"]  # .get('messages', [])

    if not messages:
        print('No messages found.')
    else:
        print(len(messages), ' Messages:')
        for m in messages:
            message = service.users().messages().get(userId='me',
                                                     id=m["id"]).execute()
            process_message(message, service)
            print(".", end='')
    print("\nDone.")


def get_creds():
    scopes = ['https://www.googleapis.com/auth/gmail.readonly']
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', scopes)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', scopes)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def process_message(message, service):
    if "parts" in message["payload"]:
        parts = message["payload"]["parts"]
        if not parts:
            return 'p'
        for part in parts:
            print(part)
            if "filename" not in part or part["filename"] == "":
                continue
                # print("\n ************************ " + message["id"])
                # print("\"" + part["filename"] + "\"")
                # print(message["internalDate"])
            if part['body']['size'] < args.size:
                continue
            message_until = datetime.datetime.fromtimestamp(
                (int(message["internalDate"])) / 1000)
            if message_until > args.MIN_TIME:
                continue

            get_attachments(service, part, "me", message["id"])
    return


def get_attachments(service, part, user_id, msg_id):
    """Get and store attachment from Message with given id.

    :param service: Authorized Gmail API service instance.
    :param part
    :param user_id: User's email address. The special value "me" can be used to
     indicate the authenticated user.
    :param msg_id: ID of Message containing attachment.
    """

    if 'data' in part['body']:
        data = part['body']['data']
    else:
        att_id = part['body']['attachmentId']
        att = service.users().messages().attachments().get(
            userId=user_id, messageId=msg_id, id=att_id).execute()
        data = att['data']
    file_data = base64.urlsafe_b64decode(data.encode('UTF-8'))
    path = part["filename"]
    print(path)
    try:
        os.makedirs(path)
    except FileExistsError:
        # directory already exists
        pass
    with open(args.location + "/" + path, 'wb') as f:
        f.write(file_data)


if __name__ == '__main__':
    main()
# [END gmail_quickstart]
