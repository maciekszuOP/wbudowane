import sqlite3

conn = sqlite3.connect('blik_users.db')
cursor = conn.cursor()

# Wyświetl wszystkie wiersze z tabeli users
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()

for row in rows:
    print(row)

conn.close()
