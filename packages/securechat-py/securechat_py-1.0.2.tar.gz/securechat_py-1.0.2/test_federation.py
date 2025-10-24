#!/usr/bin/env python3
import socket
import time

# Give some time for the client to start
time.sleep(2)

# Try to send federation command to alice's client
# But this is tricky since the client is interactive. Let me modify the test client to automatically send the federation command.

print("Testing federation by sending command to client...")

# For now, let's manually test by checking if we can send commands
# Actually, let me create a modified test client that automatically federates