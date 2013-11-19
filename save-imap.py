#!/usr/bin/env python
"""
Proof of concept code for obtaining metrics from Jenkins

usage: save_imap [-h]
                 [-u USERNAME -p PASSWORD]
                 [-a ACCOUNT]
                 [-s VEReacon,mclass,disco,sabuild,all}]

optional arguments:
  -h, --help            show this help message and exit
  -u USERNAME, --username USERNAME
                        User name to run as
  -p PASSWORD, --password PASSWORD
                        Password for login
  -a ACCOUNT, --account ACCOUNT
                        Email account to save
  -s SERVER, --server SERVER
                        IMAP server to test [default: imap.n.mail.yahoo.com]
"""

from __future__ import print_function

from email import message_from_string

from imapclient import IMAPClient

from pymongo import MongoClient
from docopt import docopt


def getargs():
    from getpass import getpass
    options = docopt(__doc__, version="0.8.0")

    server, username = options["--server"], options["--username"]
    password = options.get("--password") or getpass()
    return username, password, server


def main(username, password, host, folders):
    client = MongoClient()
    email = client.email.email
    ssl = False

    server = IMAPClient(host, use_uid=True, ssl=ssl)
    server.login(username, password)

    # for i, folder in enumerate(server.list_folders(), start=1):
    #    print("{0}: {1}".format(i, folder))

    for folder in folders:
        select_info = server.select_folder(folder, readonly=True)
        num_msgs = select_info['EXISTS']
        print("{0}: {1} messages".format(folder, num_msgs))

        messages = server.search(['NOT DELETED'])
        messages = messages[:10]
        print("{0} messages that aren't deleted".format(len(messages)))

        fields = [
            'RFC822',
            'BODY[TEXT]',
            'INTERNALDATE',
            'FLAGS',
            'RFC822.SIZE',
            'BODY[HEADER.FIELDS (SUBJECT FROM)]',
        ]
        response = server.fetch(messages, fields)
        for msgid, data in response.iteritems():
            try:
                parsed = message_from_string(data['RFC822'])
                print(dir(parsed))
                obj = {
                    "folder": folder,
                    "msgid": msgid,
                    "msg": parsed.get_payload(),
                    "date": parsed["date"],
                    "from": parsed["From"],
                    "subject": parsed["Subject"],
                }
                email.insert(obj)
            except Exception as err:
                print(msgid, err)
    server.logout()


if __name__ == '__main__':
    username, password, host = getargs()
    folders = ["Inbox"]
    main(username, password, host, folders)
