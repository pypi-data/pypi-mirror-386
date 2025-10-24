#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from securechat.client import SecureChatClient
import threading

# Monkey patch getpass to return a fixed password
import getpass
original_getpass = getpass.getpass
def mock_getpass(prompt):
    return "testpassword"
getpass.getpass = mock_getpass

# Create and connect client
client = SecureChatClient("localhost", 12348, "bob")
client.connect()