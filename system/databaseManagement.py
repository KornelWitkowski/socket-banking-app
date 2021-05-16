import sqlite3

con = sqlite3.connect('Database.db')
cur = con.cursor()

#cur.execute('''DROP TABLE IF EXISTS History''')
#cur.execute('''DROP TABLE IF EXISTS ClientData''')
cur.execute('''DROP TABLE IF EXISTS Connections''')

#cur.execute('''CREATE TABLE IF NOT EXISTS History
#               (ID INTEGER, type text, amount float, time text)''')

#cur.execute('''CREATE TABLE IF NOT EXISTS ClientData
#                (ID INTEGER PRIMARY KEY AUTOINCREMENT, name text, surname text, PESEL integer, login text,
#                password text, balance float, status integer,
#                 attempts integer default 0, activity integer default 0, his History)''')


cur.execute('''CREATE TABLE IF NOT EXISTS Connections
              (ID INTEGER PRIMARY KEY AUTOINCREMENT, ip text, port integer, user text, time text, activity integer default 0)''')