import sqlite3

def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            cpf TEXT UNIQUE,
            address TEXT,
            interests TEXT,
            activities TEXT,
            identity_verified BOOLEAN,
            esports_verified BOOLEAN
        )
    ''')
    conn.commit()
    conn.close()