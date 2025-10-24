#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from securechat.client import SecureChatClient
import threading
import time

# Monkey patch getpass to return a fixed password
import getpass
original_getpass = getpass.getpass
def mock_getpass(prompt):
    return "testpassword"
getpass.getpass = mock_getpass

# Create a custom client that auto-federates
class TestClient(SecureChatClient):
    def chat(self):
        print("Auto-federating with localhost:12348...")
        self.send_federation_request("localhost", 12348)
        time.sleep(2)  # Wait for federation
        print("Federation test complete. Users:", list(self.users.keys()))
        self.socket.close()

# Create and connect client
client = TestClient("localhost", 12346, "alice")
client.connect()