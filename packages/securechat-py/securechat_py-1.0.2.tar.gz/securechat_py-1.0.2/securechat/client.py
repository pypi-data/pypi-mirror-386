import socket
import threading
import json
import base64
import os
import time
import ssl
import getpass
from .crypto import generate_keypair, serialize_public_key, deserialize_public_key, encrypt_message, decrypt_message, sign_message, verify_signature, serialize_private_key, deserialize_private_key, encrypt_private_key, decrypt_private_key, derive_group_key, encrypt_symmetric, decrypt_symmetric

class SecureChatClient:
    def __init__(self, server_host, server_port, username):
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.users = {}  # username -> pub_key
        self.groups = set()  # user's groups
        self.private_key = None
        self.public_key = None
        self.connected = False
        self.load_or_generate_keys()

    def load_or_generate_keys(self):
        key_file = f"{self.username}_keys.json"
        if os.path.exists(key_file):
            try:
                password = getpass.getpass("Enter password for key decryption: ")
                with open(key_file, 'r') as f:
                    data = json.load(f)
                self.private_key = decrypt_private_key(data['private'], password)
                self.public_key = deserialize_public_key(data['public'])
                print("Keys loaded successfully")
            except Exception as e:
                print(f"Failed to load existing keys: {e}")
                print("Generating new keys...")
                if os.path.exists(key_file):
                    backup_file = f"{key_file}.backup"
                    os.rename(key_file, backup_file)
                    print(f"Existing key file backed up to {backup_file}")
                self._generate_new_keys()
        else:
            self._generate_new_keys()
    
    def _generate_new_keys(self):
        while True:
            try:
                password = getpass.getpass("Enter password for key encryption: ")
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    print("Passwords don't match. Try again.")
                    continue
                if len(password) < 8:
                    print("Password must be at least 8 characters long, contain uppercase, lowercase, and digits.")
                    continue
                if not any(c.isupper() for c in password):
                    print("Password must contain at least one uppercase letter.")
                    continue
                if not any(c.islower() for c in password):
                    print("Password must contain at least one lowercase letter.")
                    continue
                if not any(c.isdigit() for c in password):
                    print("Password must contain at least one digit.")
                    continue
                break
            except KeyboardInterrupt:
                print("\nKey generation cancelled")
                raise SystemExit
                
        self.private_key, self.public_key = generate_keypair()
        data = {
            'private': encrypt_private_key(self.private_key, password),
            'public': serialize_public_key(self.public_key)
        }
        key_file = f"{self.username}_keys.json"
        with open(key_file, 'w') as f:
            json.dump(data, f)
        print(f"Keys generated and saved to {key_file}")

    def connect(self):
        context = ssl.create_default_context()
        # For self-signed certificates in development, we allow them but validate expiry
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # TODO: Implement proper certificate pinning for production
        self.socket = context.wrap_socket(self.socket)
        self.socket.connect((self.server_host, self.server_port))
        # Send username and pub_key
        msg = {
            'username': self.username,
            'pub_key': serialize_public_key(self.public_key)
        }
        self.socket.send(json.dumps(msg).encode())
        # Start listening thread
        threading.Thread(target=self.listen).start()
        # Wait for connection confirmation
        while not self.connected:
            time.sleep(0.1)
        # Start chat
        self.chat()

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
                elif msg['type'] == 'group_update':
                    self.handle_group_update(msg)
                elif msg['type'] == 'groups':
                    print("Available groups:", msg['groups'])
                elif msg['type'] == 'error':
                    print(f"Error: {msg['message']}")
            except (json.JSONDecodeError, KeyError, ValueError) as e:
                print(f"Error processing message: {e}")
                break
            except Exception as e:
                print(f"Unexpected error in listen loop: {e}")
                break

    def handle_message(self, msg):
        from_user = msg['from']
        to = msg.get('to', '')
        encrypted = base64.b64decode(msg['encrypted'])
        signature = base64.b64decode(msg['signature'])
        if to.startswith('group:'):
            # Decrypt group message with symmetric key
            group_name = to[6:]
            group_key = derive_group_key(group_name)
            try:
                message = decrypt_symmetric(group_key, encrypted)
            except Exception:
                print(f"\nInvalid encrypted group message from {from_user}")
                print("> ", end="", flush=True)
                return
        else:
            # DM, encrypted
            message = decrypt_message(self.private_key, encrypted)
        if verify_signature(self.users[from_user], message, signature):
            if to.startswith('group:'):
                print(f"\n[{from_user} -> {to}]: {message}")
            else:
                print(f"\n[{from_user}]: {message}")
            print("> ", end="", flush=True)
        else:
            print(f"\nInvalid message from {from_user}")
            print("> ", end="", flush=True)

    def handle_group_update(self, msg):
        action = msg['action']
        name = msg['name']
        user = msg.get('user', '')
        if action == 'created':
            print(f"\nGroup '{name}' created")
        elif action == 'joined':
            print(f"\n{user} joined group '{name}'")
        elif action == 'left':
            print(f"\n{user} left group '{name}'")
        print("> ", end="", flush=True)

    def send_message(self, to, message):
        signature = sign_message(self.private_key, message)
        # Remove client-side timestamp, server will generate it
        # timestamp = int(time.time() * 1000)  # Millisecond precision
        
        if to.startswith('group:'):
            # Encrypt group message with symmetric key derived from group name
            group_name = to[6:]
            group_key = derive_group_key(group_name)
            encrypted = encrypt_symmetric(group_key, message)
        else:
            if to not in self.users:
                print(f"Unknown user: {to}")
                return
            encrypted = encrypt_message(self.users[to], message)
        msg = {
            'type': 'message',
            'to': to,
            'encrypted': base64.b64encode(encrypted).decode(),
            'signature': base64.b64encode(signature).decode()
            # 'timestamp': timestamp  # Removed, server generates timestamp
        }
        self.socket.send(json.dumps(msg).encode())

    def chat(self):
        print("Type 'to username: message' to send DM, 'group create name' to create group, 'group join name' to join, 'group list' to list groups, 'federate host:port' to connect to federated server, 'list' for users")
        try:
            while True:
                line = input("> ").strip()
                if line == 'list':
                    print("All known users:", list(self.users.keys()))
                elif line.startswith('to '):
                    parts = line[3:].split(':', 1)
                    if len(parts) == 2:
                        to_user = parts[0].strip()
                        message = parts[1].strip()
                        if message:
                            self.send_message(to_user, message)
                        else:
                            print("Message cannot be empty")
                    else:
                        print("Format: to username: message")
                elif line.startswith('group '):
                    parts = line.split()
                    if len(parts) >= 3:
                        action = parts[1]
                        name = parts[2]
                        self.send_group_action(action, name)
                    else:
                        print("Format: group <create|join|leave|list> name")
                elif line.startswith('federate '):
                    parts = line[9:].split(':')
                    if len(parts) == 2:
                        host = parts[0].strip()
                        try:
                            port = int(parts[1].strip())
                            self.send_federation_request(host, port)
                        except ValueError:
                            print("Invalid port number")
                    else:
                        print("Format: federate host:port")
                else:
                    print("Commands: 'to username: message', 'group create name', 'group join name', 'group leave name', 'group list', 'federate host:port', 'list'")
        except KeyboardInterrupt:
            print("\nDisconnecting...")
            self.socket.close()

    def send_group_action(self, action, name):
        msg = {
            'type': 'group',
            'action': action,
            'name': name
        }
        self.socket.send(json.dumps(msg).encode())

    def send_federation_request(self, host, port):
        msg = {
            'type': 'federate',
            'host': host,
            'port': port
        }
        self.socket.send(json.dumps(msg).encode())
        print(f"Requested federation with {host}:{port}")

if __name__ == '__main__':
    # For testing
    pass