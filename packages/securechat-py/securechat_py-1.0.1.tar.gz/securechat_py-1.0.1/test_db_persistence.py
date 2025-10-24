#!/usr/bin/env python3
"""
Test script to verify database persistence
"""
import socket
import ssl
import json
import time
import base64
from securechat.crypto import generate_keypair, serialize_public_key, encrypt_message, sign_message

def test_database_persistence():
    # Generate keys
    private_key, public_key = generate_keypair()
    public_key_pem = serialize_public_key(public_key)

    # Connect to server
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    sock = context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    sock.connect(('localhost', 12346))

    # Send registration
    registration = {
        'username': 'testclient',
        'pub_key': public_key_pem
    }
    sock.send(json.dumps(registration).encode())

    # Wait for response
    response = sock.recv(4096).decode()
    print(f"Registration response: {response}")

    # Send a test message to self
    message = "Hello from test client!"
    encrypted = encrypt_message(public_key, message)
    signature = sign_message(private_key, message)

    msg_data = {
        'type': 'message',
        'to': 'testclient',
        'encrypted': base64.b64encode(encrypted).decode(),
        'signature': base64.b64encode(signature).decode(),
        'timestamp': int(time.time() * 1000),
        'id': f"test_{int(time.time())}"
    }

    sock.send(json.dumps(msg_data).encode())
    print("Sent test message")

    # Wait a bit
    time.sleep(1)

    # Close connection
    sock.close()
    print("Test completed")

if __name__ == '__main__':
    test_database_persistence()