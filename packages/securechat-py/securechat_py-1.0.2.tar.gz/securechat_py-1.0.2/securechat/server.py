import socket
import threading
import json
import base64
import ssl
import time
import datetime
import logging
from .crypto import deserialize_public_key, serialize_public_key, validate_certificate, get_certificate_expiry, get_certificate_fingerprint, validate_certificate_pin
from .database import SecureChatDatabase

class SecureChatServer:
    def __init__(self, host='0.0.0.0', port=12346, cert_file='server.crt', key_file='server.key', db_path=None):
        # Configure logging
        logging.basicConfig(
            filename=f'server_{port}.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(f'SecureChat-{port}')
        
        self.host = host
        self.port = port
        self.cert_file = cert_file
        self.key_file = key_file
        
        # Initialize database
        if db_path is None:
            db_path = f'server_{port}.db'
        self.db = SecureChatDatabase(db_path)
        
        # Load configuration from database or use defaults
        self.max_clients = self.db.get_config('max_clients', 1000)
        self.max_message_size = self.db.get_config('max_message_size', 1024 * 1024)  # 1MB
        self.federation_timeout = self.db.get_config('federation_timeout', 30)
        self.message_ttl = self.db.get_config('message_ttl_days', 7) * 24 * 3600
        self.federation_password = self.db.get_config('federation_password', 'default_federation_password')  # TODO: Change this!
        self.pinned_certificates = self.db.get_config('pinned_certificates', [])  # List of SHA256 fingerprints
        
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Load persistent data
        self.clients = {}  # username -> (socket, pub_key) - runtime only
        self.groups = {}  # group_name -> set of usernames - loaded from DB
        self.federated_servers = {}  # server_id -> (socket, server_info) - runtime only
        self.known_users = {}  # username -> (server_id, pub_key) - loaded from DB
        self.server_id = f"localhost:{port}"
        self.lock = threading.Lock()
        
        # Rate limiting
        self.last_message_times = {}  # username -> last_message_timestamp for replay prevention
        self.rate_limits = {}  # username -> {'count': int, 'window_start': float}
        
        self.logger.info(f"Server initialized on {host}:{port} with database: {db_path}")
        
        # Load persistent data
        self._load_persistent_data()

    def _load_persistent_data(self):
        """Load persistent data from database"""
        try:
            # Load federation servers
            fed_servers = self.db.get_federation_servers()
            for server in fed_servers:
                self.known_users.update(self._get_server_users(server['server_id']))
            
            # Load groups
            # Note: We'll load group members on demand to avoid loading all at startup
            
            self.logger.info("Persistent data loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load persistent data: {e}")

    def _get_server_users(self, server_id: str) -> dict:
        """Get users for a server (placeholder - would need federation sync)"""
        # This would be populated during federation handshakes
        return {}

    def start(self):
        # Validate certificates before starting
        try:
            with open(self.cert_file, 'r') as f:
                cert_pem = f.read()
            valid, reason = validate_certificate(cert_pem, 'localhost')
            if not valid:
                print(f"Certificate validation failed: {reason}")
                return
            
            expiry = get_certificate_expiry(cert_pem)
            if expiry:
                days_until_expiry = (expiry - datetime.datetime.now(datetime.timezone.utc)).days
                if days_until_expiry < 30:
                    print(f"WARNING: Certificate expires in {days_until_expiry} days")
                    
        except FileNotFoundError:
            print(f"Certificate files not found: {self.cert_file}, {self.key_file}")
            return
        except Exception as e:
            print(f"Certificate validation error: {e}")
            return
            
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
        self.server_socket = context.wrap_socket(self.server_socket, server_side=True)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Secure server started on {self.host}:{self.port}")
        # Start federation listener
        threading.Thread(target=self.listen_for_federation).start()
        # Start cleanup thread
        threading.Thread(target=self.periodic_cleanup, daemon=True).start()
        while True:
            client_socket, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

    def handle_client(self, client_socket):
        username = None
        client_ip = client_socket.getpeername()[0]
        message_count = 0
        last_message_time = time.time()
        
        try:
            # Receive username and pub_key
            data = client_socket.recv(4096).decode().strip()
            if not data or len(data) > self.max_message_size:
                return
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                print("Invalid JSON for initial message")
                return
            username = msg['username']
            
            # Validate username (prevent injection attacks)
            if not username or not isinstance(username, str) or len(username) > 50 or not username.isalnum():
                client_socket.send(json.dumps({'type': 'error', 'message': 'Invalid username'}).encode())
                return
            if username in self.clients:
                client_socket.send(json.dumps({'type': 'error', 'message': 'Username already taken'}).encode())
                return
                
            pub_key_pem = msg['pub_key']
            if not isinstance(pub_key_pem, str) or len(pub_key_pem) > 10000:  # Reasonable limit for PEM
                return
            try:
                pub_key = deserialize_public_key(pub_key_pem)
            except Exception:
                return
            
            # Store user in database
            if not self.db.add_user(username, pub_key_pem, self.server_id):
                client_socket.send(json.dumps({'type': 'error', 'message': 'Failed to register user'}).encode())
                return
            
            with self.lock:
                if len(self.clients) >= self.max_clients:
                    client_socket.send(json.dumps({'type': 'error', 'message': 'Server full'}).encode())
                    return
                    
                self.clients[username] = (client_socket, pub_key)
                self.db.update_user_status(username, 'online')
                
                # Send current users to new client
                users = {}
                for u in self.clients.keys():
                    user_data = self.db.get_user(u)
                    if user_data:
                        users[u] = user_data['public_key']
                
                client_socket.send(json.dumps({'type': 'users', 'users': users}).encode())
                
                # Send pending messages
                pending = self.db.get_pending_messages(username)
                if pending:
                    client_socket.send(json.dumps({'type': 'pending_messages', 'messages': pending}).encode())
                    # Mark messages as delivered
                    for msg_data in pending:
                        self.db.mark_message_delivered(msg_data['id'])
                
                # Broadcast new user to others
                for u, (s, _) in self.clients.items():
                    if u != username:
                        s.send(json.dumps({'type': 'new_user', 'username': username, 'pub_key': pub_key_pem}).encode())
                        
            # Message handling loop
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                    
                # Rate limiting: max 10 messages per second per user
                current_time = time.time()
                with self.lock:
                    if username not in self.rate_limits:
                        self.rate_limits[username] = {'count': 0, 'window_start': current_time}
                    
                    user_rate = self.rate_limits[username]
                    # Reset window if more than 1 second has passed
                    if current_time - user_rate['window_start'] >= 1.0:
                        user_rate['count'] = 0
                        user_rate['window_start'] = current_time
                    
                    if user_rate['count'] >= 10:
                        self.logger.warning(f"Rate limit exceeded for {username} from {client_ip}")
                        break
                    
                    user_rate['count'] += 1
                
                if len(data) > self.max_message_size:
                    print(f"Message too large from {username}")
                    continue
                    
                try:
                    msg = json.loads(data.decode())
                except json.JSONDecodeError:
                    print("Invalid JSON in message")
                    continue
                    
                # Validate message structure
                required_fields = ['type']
                if not isinstance(msg, dict) or not all(field in msg for field in required_fields):
                    continue
                    
                if msg['type'] == 'message':
                    required_msg_fields = ['to', 'encrypted', 'signature']
                    if not all(field in msg for field in required_msg_fields):
                        continue
                    if not isinstance(msg['to'], str) or len(msg['to']) > 100:
                        continue
                    if not isinstance(msg['encrypted'], str) or len(msg['encrypted']) > self.max_message_size:
                        continue
                    if not isinstance(msg['signature'], str) or len(msg['signature']) > 10000:
                        continue
                    self.handle_message(username, msg)
                elif msg['type'] == 'group':
                    self.handle_group_action(username, msg)
                elif msg['type'] == 'federate':
                    # Validate federation request
                    if 'host' not in msg or 'port' not in msg:
                        continue
                    if not isinstance(msg['host'], str) or not isinstance(msg['port'], int):
                        continue
                    if msg['port'] < 1024 or msg['port'] > 65535:  # Valid port range
                        continue
                    remote_host = msg['host']
                    remote_port = msg['port']
                    threading.Thread(target=self.connect_to_federated_server, args=(remote_host, remote_port)).start()
                    
        except Exception as e:
            print(f"Error handling client {username or 'unknown'}: {e}")
        finally:
            with self.lock:
                if username and username in self.clients:
                    del self.clients[username]
                    self.db.update_user_status(username, 'offline')

    def handle_message(self, from_user, msg):
        to = msg['to']
        encrypted = base64.b64decode(msg['encrypted'])
        signature = base64.b64decode(msg['signature'])
        # Use server-generated timestamp instead of client-provided
        server_timestamp = int(time.time() * 1000)
        message_id = msg.get('id', f"{from_user}_{server_timestamp}")
        
        # Replay prevention: check timestamp is not too old or duplicate
        current_time = int(time.time() * 1000)
        with self.lock:
            last_time = self.last_message_times.get(from_user, 0)
            if server_timestamp <= last_time or abs(current_time - server_timestamp) > 300000:  # 5 minutes tolerance
                self.logger.warning(f"Rejected replayed or stale message from {from_user}: timestamp {server_timestamp}, last {last_time}")
                return
            self.last_message_times[from_user] = server_timestamp
            
        # Store message in database
        expires_at = time.time() + self.message_ttl if self.message_ttl > 0 else None
        if not self.db.store_message(message_id, from_user, to if not to.startswith('group:') else None,
                                   to[6:] if to.startswith('group:') else None,
                                   base64.b64encode(encrypted).decode(),
                                   base64.b64encode(signature).decode(), server_timestamp / 1000, expires_at):
            self.logger.error(f"Failed to store message {message_id}")
            return
            
        if to.startswith('group:'):
            group_name = to[6:]
            # Load group members from database
            group_members = self.db.get_group_members(group_name)
            with self.lock:
                for u in group_members:
                    if u != from_user:
                        if u in self.clients:
                            to_socket, _ = self.clients[u]
                            to_socket.send(json.dumps({'type': 'message', 'from': from_user, 'to': to, 'encrypted': base64.b64encode(encrypted).decode(), 'signature': base64.b64encode(signature).decode()}).encode())
                        elif u in self.known_users:
                            # Forward to federated server
                            target_server = self.known_users[u][0]
                            if target_server in self.federated_servers:
                                fed_socket, _ = self.federated_servers[target_server]
                                try:
                                    fed_socket.send(json.dumps({'type': 'message', 'from': from_user, 'to': to, 'encrypted': base64.b64encode(encrypted).decode(), 'signature': base64.b64encode(signature).decode()}).encode())
                                except (OSError, BrokenPipeError):
                                    # Federation server disconnected
                                    pass
        else:
            with self.lock:
                if to in self.clients:
                    to_socket, _ = self.clients[to]
                    to_socket.send(json.dumps({'type': 'message', 'from': from_user, 'encrypted': base64.b64encode(encrypted).decode(), 'signature': base64.b64encode(signature).decode()}).encode())
                elif to in self.known_users:
                    # Forward to federated server
                    target_server = self.known_users[to][0]
                    if target_server in self.federated_servers:
                        fed_socket, _ = self.federated_servers[target_server]
                        try:
                            fed_socket.send(json.dumps(msg).encode())
                        except:
                            pass

    def handle_group_action(self, username, msg):
        action = msg['action']
        group_name = msg['name']
        
        if action == 'create':
            if self.db.create_group(group_name, username):
                with self.lock:
                    self.groups[group_name] = {username}  # Cache in memory
                self.broadcast({'type': 'group_update', 'action': 'created', 'name': group_name})
            else:
                if username in self.clients:
                    self.clients[username][0].send(json.dumps({'type': 'error', 'message': 'Group already exists'}).encode())
        elif action == 'join':
            if self.db.add_user_to_group(group_name, username):
                with self.lock:
                    if group_name not in self.groups:
                        self.groups[group_name] = set()
                    self.groups[group_name].add(username)
                self.broadcast({'type': 'group_update', 'action': 'joined', 'name': group_name, 'user': username})
            else:
                if username in self.clients:
                    self.clients[username][0].send(json.dumps({'type': 'error', 'message': 'Group does not exist or join failed'}).encode())
        elif action == 'leave':
            if self.db.remove_user_from_group(group_name, username):
                with self.lock:
                    if group_name in self.groups:
                        self.groups[group_name].discard(username)
                self.broadcast({'type': 'group_update', 'action': 'left', 'name': group_name, 'user': username})
        elif action == 'list':
            # Get all groups from database
            groups = []
            with self.lock:
                groups = list(self.groups.keys())
            if username in self.clients:
                self.clients[username][0].send(json.dumps({'type': 'groups', 'groups': groups}).encode())

    def broadcast(self, msg):
        for u, (s, _) in self.clients.items():
            try:
                s.send(json.dumps(msg).encode())
            except (OSError, BrokenPipeError):
                # Client disconnected, will be cleaned up by handle_client
                pass

    def listen_for_federation(self):
        """Listen for incoming federation connections on port + 1"""
        federation_port = self.port + 1
        federation_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            context.load_cert_chain(certfile=self.cert_file, keyfile=self.key_file)
            federation_socket = context.wrap_socket(federation_socket, server_side=True)
            federation_socket.bind((self.host, federation_port))
            federation_socket.listen(5)
            print(f"Federation listener started on {self.host}:{federation_port}")
            
            while True:
                client_socket, addr = federation_socket.accept()
                threading.Thread(target=self.handle_federation_client, args=(client_socket,)).start()
        except Exception as e:
            print(f"Federation listener error: {e}")

    def handle_federation_client(self, client_socket):
        """Handle incoming federation connections"""
        try:
            data = client_socket.recv(4096).decode().strip()
            if not data:
                return
            try:
                msg = json.loads(data)
            except json.JSONDecodeError:
                print("Invalid JSON in federation message")
                return
            
            if msg.get('type') == 'federation_handshake':
                # Check federation password
                if msg.get('federation_password') != self.federation_password:
                    print(f"Invalid federation password from {client_socket.getpeername()}")
                    return
                    
                remote_server_id = msg['server_id']
                remote_host = msg['host']
                remote_port = msg['port']
                
                with self.lock:
                    self.federated_servers[remote_server_id] = (client_socket, {
                        'host': remote_host,
                        'port': remote_port,
                        'users': msg.get('users', {})
                    })
                    
                    # Update known users
                    for username, pub_key_pem in msg.get('users', {}).items():
                        self.known_users[username] = (remote_server_id, deserialize_public_key(pub_key_pem))
                
                # Send our server info back
                response_users = {u: serialize_public_key(pk) for u, (_, pk) in self.clients.items()}
                print(f"Sending response with users: {list(response_users.keys())}")
                response = {
                    'type': 'federation_response',
                    'server_id': self.server_id,
                    'host': self.host,
                    'port': self.port,
                    'users': response_users
                }
                client_socket.send(json.dumps(response).encode())
                
                print(f"Federated with server: {remote_server_id}")
                self.logger.info(f"Established federation with server: {remote_server_id}")
                
                # Broadcast federated users to all clients
                federated_users = {u: serialize_public_key(pk) for u, (s, pk) in self.known_users.items() if s == remote_server_id}
                print(f"Broadcasting {len(federated_users)} federated users to {len(self.clients)} clients")
                self.broadcast({'type': 'federated_users', 'users': federated_users})
                
                # Keep connection alive for message forwarding
                while True:
                    data = client_socket.recv(4096)
                    if not data:
                        break
                    try:
                        fed_msg = json.loads(data.decode())
                        self.handle_federated_message(fed_msg, remote_server_id)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"Federation client error: {e}")
        finally:
            with self.lock:
                # Remove disconnected server
                for sid, (sock, _) in list(self.federated_servers.items()):
                    if sock == client_socket:
                        del self.federated_servers[sid]
                        # Remove users from that server
                        self.known_users = {u: (s, pk) for u, (s, pk) in self.known_users.items() if s != sid}
                        break

    def handle_federated_message(self, msg, from_server):
        """Handle messages from federated servers"""
        if msg['type'] == 'message':
            to = msg['to']
            from_user = msg['from']
            
            # If message is for a user on this server
            if to in self.clients:
                to_socket, _ = self.clients[to]
                to_socket.send(json.dumps(msg).encode())
            elif to in self.pending_messages:
                # Store for offline user
                self.pending_messages[to].append(msg)
            else:
                # Forward to appropriate server if known
                if to in self.known_users:
                    target_server = self.known_users[to][0]
                    if target_server in self.federated_servers:
                        fed_socket, _ = self.federated_servers[target_server]
                        try:
                            fed_socket.send(json.dumps(msg).encode())
                        except (OSError, BrokenPipeError):
                            # Federation server disconnected
                            pass

    def connect_to_federated_server(self, remote_host, remote_port):
        """Connect to another server for federation"""
        remote_server_id = f"{remote_host}:{remote_port}"
        
        # Check if already connected
        with self.lock:
            if remote_server_id in self.federated_servers:
                print(f"Already federated with: {remote_server_id}")
                return
        
        try:
            context = ssl.create_default_context()
            # Enable certificate validation for federation
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED
            
            federation_socket = context.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            )
            federation_socket.settimeout(self.federation_timeout)
            federation_socket.connect((remote_host, remote_port + 1))  # Federation port
            
            # Validate certificate pinning if configured
            if self.pinned_certificates:
                try:
                    peer_cert_der = federation_socket.getpeercert(binary_form=True)
                    if peer_cert_der:
                        peer_cert_pem = ssl.DER_cert_to_PEM_cert(peer_cert_der).encode()
                        pin_valid, pin_reason = validate_certificate_pin(peer_cert_pem.decode(), self.pinned_certificates)
                        if not pin_valid:
                            print(f"Certificate pinning failed: {pin_reason}")
                            federation_socket.close()
                            return
                    else:
                        print("No peer certificate received")
                        federation_socket.close()
                        return
                except Exception as e:
                    print(f"Certificate pinning check error: {e}")
                    federation_socket.close()
                    return
            
            # Send handshake
            handshake = {
                'type': 'federation_handshake',
                'server_id': self.server_id,
                'host': self.host,
                'port': self.port,
                'federation_password': self.federation_password,
                'users': {u: serialize_public_key(pk) for u, (_, pk) in self.clients.items()}
            }
            federation_socket.send(json.dumps(handshake).encode())
            
            # Wait for response
            data = federation_socket.recv(4096).decode()
            response = json.loads(data)
            
            if response['type'] == 'federation_response':
                remote_server_id = response['server_id']
                print(f"Received federation response from {remote_server_id} with users: {list(response.get('users', {}).keys())}")
                with self.lock:
                    self.federated_servers[remote_server_id] = (federation_socket, {
                        'host': response['host'],
                        'port': response['port'],
                        'users': response.get('users', {})
                    })
                    
                    # Update known users
                    for username, pub_key_pem in response.get('users', {}).items():
                        if username not in self.known_users:  # Avoid conflicts
                            self.known_users[username] = (remote_server_id, deserialize_public_key(pub_key_pem))
                
                print(f"Successfully federated with: {remote_server_id}")
                
                # Broadcast federated users to all clients
                federated_users = {u: serialize_public_key(pk) for u, (s, pk) in self.known_users.items() if s == remote_server_id}
                print(f"Broadcasting {len(federated_users)} federated users to {len(self.clients)} clients")
                self.broadcast({'type': 'federated_users', 'users': federated_users})
                
                # Start listening for messages from this server
                threading.Thread(target=self.listen_federated_server, args=(federation_socket, remote_server_id)).start()
                
        except socket.timeout:
            print(f"Federation connection timed out: {remote_host}:{remote_port}")
        except Exception as e:
            print(f"Failed to connect to federated server {remote_host}:{remote_port}: {e}")

    def listen_federated_server(self, fed_socket, server_id):
        """Listen for messages from a specific federated server"""
        try:
            while True:
                data = fed_socket.recv(4096)
                if not data:
                    break
                try:
                    msg = json.loads(data.decode())
                    self.handle_federated_message(msg, server_id)
                except json.JSONDecodeError:
                    continue
        except (OSError, ConnectionError):
            # Federation server disconnected
            pass
        finally:
            with self.lock:
                if server_id in self.federated_servers:
                    del self.federated_servers[server_id]
                    # Remove users from that server
                    self.known_users = {u: (s, pk) for u, (s, pk) in self.known_users.items() if s != server_id}

    def periodic_cleanup(self):
        """Periodic cleanup of expired messages and old data"""
        while True:
            time.sleep(3600)  # Run every hour
            current_time = time.time()
            
            # Database cleanup
            expired_count = self.db.cleanup_expired_messages(current_time)
            
            with self.lock:
                # Clean up old message timestamps (keep last 1000 users)
                if len(self.last_message_times) > 1000:
                    # Keep only recent timestamps
                    cutoff_time = current_time - 86400  # 24 hours ago
                    self.last_message_times = {
                        u: t for u, t in self.last_message_times.items() 
                        if t > cutoff_time
                    }
                
                # Clean up rate limiting data for inactive users
                if len(self.rate_limits) > 1000:
                    cutoff_time = current_time - 3600  # 1 hour ago
                    self.rate_limits = {
                        u: data for u, data in self.rate_limits.items()
                        if data['window_start'] > cutoff_time
                    }
                
                stats = self.db.get_stats()
                print(f"Cleanup completed. Expired messages: {expired_count}, "
                      f"Stats: {stats}")

if __name__ == '__main__':
    server = SecureChatServer()
    server.start()