#!/usr/bin/env python3
import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

from securechat.client import SecureChatClient
from securechat.crypto import deserialize_public_key
import threading
import time

# Monkey patch getpass to return a fixed password
import getpass
original_getpass = getpass.getpass
def mock_getpass(prompt):
    return "testpassword"
getpass.getpass = mock_getpass

# Create a custom client that waits for federation and sends a test message
class TestClient(SecureChatClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.federated = False
    
    def listen(self):
        while True:
            try:
                data = self.socket.recv(4096)
                if not data:
                    break
                msg = json.loads(data.decode())
                if msg['type'] == 'users':
                    for u, pk in msg['users'].items():
                        self.users[u] = deserialize_public_key(pk)
                    self.connected = True
                    print("Connected successfully!")
                    print("Online users:", list(self.users.keys()))
                elif msg['type'] == 'new_user':
                    self.users[msg['username']] = deserialize_public_key(msg['pub_key'])
                    print(f"User joined: {msg['username']}")
                    print("Online users:", list(self.users.keys()))
                elif msg['type'] == 'pending_messages':
                    for pending_msg in msg['messages']:
                        self.handle_message(pending_msg)
                    print(f"Delivered {len(msg['messages'])} pending messages.")
                elif msg['type'] == 'federated_users':
                    for u, pk in msg['users'].items():
                        self.users[u] = deserialize_public_key(pk)
                    print(f"Added {len(msg['users'])} users from federated server")
                    print("All known users:", list(self.users.keys()))
                    self.federated = True
                elif msg['type'] == 'group_update':
                    self.handle_group_update(msg)
                elif msg['type'] == 'groups':
                    print("Available groups:", msg['groups'])
                elif msg['type'] == 'error':
                    print(f"Error: {msg['message']}")
            except:
                break

    def chat(self):
        print("Auto-federating with localhost:12348...")
        self.send_federation_request("localhost", 12348)
        
        # Wait for federation to complete
        timeout = 10
        while not self.federated and timeout > 0:
            time.sleep(1)
            timeout -= 1
        
        if self.federated:
            print("Federation complete. Sending test message to bob...")
            self.send_message("bob", "Hello from alice on federated server!")
            print("Message sent successfully!")
        else:
            print("Federation timed out")
        
        time.sleep(2)
        self.socket.close()

# Create and connect client
client = TestClient("localhost", 12346, "alice")
client.connect()