#!/bin/python

import imaplib
import email
from email.header import decode_header
import webbrowser
import os
import re

def main():
    # account credentials
    username = "nakulthythottathil@gmail.com"
    password = "Coppermine123*"
    # create an IMAP4 class with SSL 
    imap = imaplib.IMAP4_SSL("imap.gmail.com")
    # authenticate
    imap.login(username, password)


    status, messages = imap.select("INBOX")
    #print("status is "+status)
    # number of top emails to fetch
    N = 3
    # total number of emails
    total_mails_count = int(messages[0])
    for i in range(total_mails_count, total_mails_count-N, -1):
        #print(i)
        res, msg = imap.fetch(str(i), "(RFC822)")
        if res == 'OK':
            #print("success")
            for response in msg:
                #print(response)
                #print("==============")
                if isinstance(response, tuple):
                    #print("tuple")
                    #print(response[1])
                    # parse a bytes email into a message object
                    msg = email.message_from_bytes(response[1])
                    subject = decode_header(msg["Subject"])[0][0]
                    if isinstance(subject, bytes):
                        # if it's a bytes, decode to str
                        subject = subject.decode()
                    #from_addr = decode_header(msg["From"])[0][0]
                    #print(from_addr)
                    #email_addrs = re.findall(r"[a-z0-9\.\-+_]+@[a-z0-9\.\-+_]+\.[a-z]+", from_addr)
                    #print(email_addrs)
                    from_ = msg.get("From")
                    #print(from_)
                    #print(subject)
                    #subject = subject.decode()
                    #print(subject)
                    content_type = msg.get_content_type()
                    print(content_type)
                    print(msg.is_multipart())

        else:
            print("error reading "+i+"th mail")

if __name__ == "__main__":
    main()