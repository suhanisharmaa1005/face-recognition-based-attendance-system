
import sqlite3

connection = sqlite3.connect("attendance.db")
cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER NOT NULL,
        attendance_date TEXT NOT NULL,
        attendance_time TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Present',
        FOREIGN KEY (student_id) REFERENCES students(id),
        UNIQUE(student_id, attendance_date)
    )
""")

connection.commit()
connection.close()

print("Attendance table created successfully!")
