
import sqlite3

connection = sqlite3.connect("attendance.db")
cursor = connection.cursor()

cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
)

tables = cursor.fetchall()
print("Database tables:", tables)

connection.close()
