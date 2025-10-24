"""
SecureChat Database Module
Handles persistent storage of messages, users, and configuration
"""

import sqlite3
import json
import time
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

class SecureChatDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.lock = threading.Lock()
        self.logger = logging.getLogger('SecureChatDB')

        # Create database and tables
        self._create_tables()

    def _create_tables(self):
        """Create all necessary database tables"""
        with self.lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    username TEXT PRIMARY KEY,
                    public_key TEXT NOT NULL,
                    server_id TEXT,
                    last_seen REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    status TEXT DEFAULT 'offline'
                )
            ''')

            # Messages table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT UNIQUE,
                    from_user TEXT NOT NULL,
                    to_user TEXT,
                    to_group TEXT,
                    encrypted_content TEXT NOT NULL,
                    signature TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    delivered BOOLEAN DEFAULT FALSE,
                    expires_at REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            # Groups table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS groups (
                    name TEXT PRIMARY KEY,
                    creator TEXT NOT NULL,
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    description TEXT
                )
            ''')

            # Group members table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS group_members (
                    group_name TEXT NOT NULL,
                    username TEXT NOT NULL,
                    joined_at REAL DEFAULT (strftime('%s', 'now')),
                    PRIMARY KEY (group_name, username),
                    FOREIGN KEY (group_name) REFERENCES groups (name) ON DELETE CASCADE
                )
            ''')

            # Federation servers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS federation_servers (
                    server_id TEXT PRIMARY KEY,
                    host TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    connected BOOLEAN DEFAULT FALSE,
                    last_connected REAL,
                    created_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            # File transfers table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_transfers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transfer_id TEXT UNIQUE,
                    filename TEXT NOT NULL,
                    file_size INTEGER NOT NULL,
                    from_user TEXT NOT NULL,
                    to_user TEXT NOT NULL,
                    encrypted_hash TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at REAL DEFAULT (strftime('%s', 'now')),
                    completed_at REAL
                )
            ''')

            # Configuration table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at REAL DEFAULT (strftime('%s', 'now'))
                )
            ''')

            # Message receipts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS message_receipts (
                    message_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    received_at REAL DEFAULT (strftime('%s', 'now')),
                    read_at REAL
                )
            ''')

            conn.commit()
            conn.close()

    # User management methods
    def add_user(self, username: str, public_key: str, server_id: str = None) -> bool:
        """Add or update a user"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO users (username, public_key, server_id, last_seen)
                    VALUES (?, ?, ?, ?)
                ''', (username, public_key, server_id, time.time()))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to add user {username}: {e}")
                return False
            finally:
                conn.close()

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user information"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
                row = cursor.fetchone()

                if row:
                    return {
                        'username': row[0],
                        'public_key': row[1],
                        'server_id': row[2],
                        'last_seen': row[3],
                        'created_at': row[4],
                        'status': row[5]
                    }
                return None
            except Exception as e:
                self.logger.error(f"Failed to get user {username}: {e}")
                return None
            finally:
                conn.close()

    def update_user_status(self, username: str, status: str) -> bool:
        """Update user online status"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    UPDATE users SET status = ?, last_seen = ?
                    WHERE username = ?
                ''', (status, time.time(), username))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to update user status {username}: {e}")
                return False
            finally:
                conn.close()

    def get_online_users(self) -> List[str]:
        """Get list of online users"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute("SELECT username FROM users WHERE status = 'online'")
                return [row[0] for row in cursor.fetchall()]
            except Exception as e:
                self.logger.error(f"Failed to get online users: {e}")
                return []
            finally:
                conn.close()

    # Message management methods
    def store_message(self, message_id: str, from_user: str, to_user: str = None,
                     to_group: str = None, encrypted_content: str = None,
                     signature: str = None, timestamp: float = None,
                     expires_at: float = None) -> bool:
        """Store a message persistently"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO messages
                    (message_id, from_user, to_user, to_group, encrypted_content,
                     signature, timestamp, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (message_id, from_user, to_user, to_group, encrypted_content,
                      signature, timestamp, expires_at))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to store message {message_id}: {e}")
                return False
            finally:
                conn.close()

    def get_pending_messages(self, username: str) -> List[Dict[str, Any]]:
        """Get pending messages for a user"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    SELECT message_id, from_user, to_user, to_group, encrypted_content,
                           signature, timestamp
                    FROM messages
                    WHERE (to_user = ? OR to_group IN (
                        SELECT group_name FROM group_members WHERE username = ?
                    )) AND delivered = FALSE
                    ORDER BY timestamp ASC
                ''', (username, username))

                messages = []
                for row in cursor.fetchall():
                    messages.append({
                        'id': row[0],
                        'from': row[1],
                        'to': row[2],
                        'group': row[3],
                        'encrypted': row[4],
                        'signature': row[5],
                        'timestamp': row[6]
                    })

                return messages
            except Exception as e:
                self.logger.error(f"Failed to get pending messages for {username}: {e}")
                return []
            finally:
                conn.close()

    def mark_message_delivered(self, message_id: str) -> bool:
        """Mark a message as delivered"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('UPDATE messages SET delivered = TRUE WHERE message_id = ?',
                             (message_id,))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to mark message delivered {message_id}: {e}")
                return False
            finally:
                conn.close()

    def cleanup_expired_messages(self, current_time: float = None) -> int:
        """Clean up expired messages"""
        if current_time is None:
            current_time = time.time()

        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('DELETE FROM messages WHERE expires_at < ?', (current_time,))
                deleted_count = cursor.rowcount

                conn.commit()
                return deleted_count
            except Exception as e:
                self.logger.error(f"Failed to cleanup expired messages: {e}")
                return 0
            finally:
                conn.close()

    # Group management methods
    def create_group(self, name: str, creator: str, description: str = None) -> bool:
        """Create a new group"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('INSERT INTO groups (name, creator, description) VALUES (?, ?, ?)',
                             (name, creator, description))

                # Add creator as first member
                cursor.execute('INSERT INTO group_members (group_name, username) VALUES (?, ?)',
                             (name, creator))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to create group {name}: {e}")
                return False
            finally:
                conn.close()

    def add_user_to_group(self, group_name: str, username: str) -> bool:
        """Add user to group"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('INSERT INTO group_members (group_name, username) VALUES (?, ?)',
                             (group_name, username))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to add user {username} to group {group_name}: {e}")
                return False
            finally:
                conn.close()

    def remove_user_from_group(self, group_name: str, username: str) -> bool:
        """Remove user from group"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('DELETE FROM group_members WHERE group_name = ? AND username = ?',
                             (group_name, username))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to remove user {username} from group {group_name}: {e}")
                return False
            finally:
                conn.close()

    def get_group_members(self, group_name: str) -> List[str]:
        """Get group members"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT username FROM group_members WHERE group_name = ?',
                             (group_name,))
                return [row[0] for row in cursor.fetchall()]
            except Exception as e:
                self.logger.error(f"Failed to get group members for {group_name}: {e}")
                return []
            finally:
                conn.close()

    def get_user_groups(self, username: str) -> List[str]:
        """Get groups for a user"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT group_name FROM group_members WHERE username = ?',
                             (username,))
                return [row[0] for row in cursor.fetchall()]
            except Exception as e:
                self.logger.error(f"Failed to get groups for {username}: {e}")
                return []
            finally:
                conn.close()

    # Federation methods
    def add_federation_server(self, server_id: str, host: str, port: int) -> bool:
        """Add a federation server"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO federation_servers (server_id, host, port)
                    VALUES (?, ?, ?)
                ''', (server_id, host, port))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to add federation server {server_id}: {e}")
                return False
            finally:
                conn.close()

    def get_federation_servers(self) -> List[Dict[str, Any]]:
        """Get all federation servers"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM federation_servers')
                servers = []
                for row in cursor.fetchall():
                    servers.append({
                        'server_id': row[0],
                        'host': row[1],
                        'port': row[2],
                        'connected': bool(row[3]),
                        'last_connected': row[4],
                        'created_at': row[5]
                    })
                return servers
            except Exception as e:
                self.logger.error(f"Failed to get federation servers: {e}")
                return []
            finally:
                conn.close()

    # Configuration methods
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT OR REPLACE INTO config (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, json.dumps(value), time.time()))

                conn.commit()
                return True
            except Exception as e:
                self.logger.error(f"Failed to set config {key}: {e}")
                return False
            finally:
                conn.close()

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT value FROM config WHERE key = ?', (key,))
                row = cursor.fetchone()

                if row:
                    return json.loads(row[0])
                return default
            except Exception as e:
                self.logger.error(f"Failed to get config {key}: {e}")
                return default
            finally:
                conn.close()

    # Statistics and monitoring
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                stats = {}

                # User stats
                cursor.execute('SELECT COUNT(*) FROM users')
                stats['total_users'] = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM users WHERE status = 'online'")
                stats['online_users'] = cursor.fetchone()[0]

                # Message stats
                cursor.execute('SELECT COUNT(*) FROM messages')
                stats['total_messages'] = cursor.fetchone()[0]

                cursor.execute('SELECT COUNT(*) FROM messages WHERE delivered = FALSE')
                stats['pending_messages'] = cursor.fetchone()[0]

                # Group stats
                cursor.execute('SELECT COUNT(*) FROM groups')
                stats['total_groups'] = cursor.fetchone()[0]

                # Federation stats
                cursor.execute('SELECT COUNT(*) FROM federation_servers')
                stats['federation_servers'] = cursor.fetchone()[0]

                return stats
            except Exception as e:
                self.logger.error(f"Failed to get stats: {e}")
                return {}
            finally:
                conn.close()

    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database"""
        with self.lock:
            try:
                # SQLite backup
                conn = sqlite3.connect(self.db_path)
                backup_conn = sqlite3.connect(backup_path)

                with backup_conn:
                    conn.backup(backup_conn)

                backup_conn.close()
                conn.close()
                return True
            except Exception as e:
                self.logger.error(f"Failed to backup database: {e}")
                return False