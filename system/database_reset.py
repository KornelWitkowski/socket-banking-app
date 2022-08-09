import sqlite3

con = sqlite3.connect('Database.db')
cur = con.cursor()


cur.execute('DROP TABLE IF EXISTS ClientData')
cur.execute('DROP TABLE IF EXISTS Connections')


cur.execute('''CREATE TABLE IF NOT EXISTS ClientData
                (ID INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 surname TEXT,
                 phone INTEGER,
                 login TEXT,
                 password TEXT,
                 balance FLOAT,
                 attempts INTEGER DEFAULT 0,
                 activity INTEGER DEFAULT 0,
                 status INTEGER,
                 history TEXT DEFAULT "")''')


cur.execute('''CREATE TABLE IF NOT EXISTS Connections
              (ID INTEGER PRIMARY KEY AUTOINCREMENT,
               ip TEXT,
               port INTEGER,
               user TEXT,
               time TEXT,
               activity INTEGER default 0)''')
