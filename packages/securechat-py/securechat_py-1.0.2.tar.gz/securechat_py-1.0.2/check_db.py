import sqlite3

# Connect to database
conn = sqlite3.connect(r'C:\Users\Aspire\.securechat\data\securechat.db')
c = conn.cursor()

# Check users
print("Users in database:")
c.execute('SELECT username, status FROM users')
for row in c.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Check messages
c.execute('SELECT COUNT(*) FROM messages')
print(f"Total messages: {c.fetchone()[0]}")

# Check groups
c.execute('SELECT COUNT(*) FROM groups')
print(f"Total groups: {c.fetchone()[0]}")

conn.close()