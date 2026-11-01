
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from database import engine, Base, get_db
from models import Student

from datetime import date
import subprocess
import sys
import os


# Create missing tables without deleting existing data
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Face Attendance System")


# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StudentInput(BaseModel):
    name: str
    roll_no: str
    course: str


# ---------------- HOME ----------------

@app.get("/")
def home():
    return {
        "message": "Face Attendance System is working!"
    }


# ---------------- STUDENTS ----------------

@app.get("/students")
def get_students(db: Session = Depends(get_db)):

    students = db.query(Student).order_by(Student.id).all()

    return [
        {
            "id": s.id,
            "name": s.name,
            "roll_no": s.roll_no,
            "course": s.course,
        }
        for s in students
    ]


@app.get("/students/{student_id}")
def get_student(
    student_id: int,
    db: Session = Depends(get_db)
):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    return {
        "id": student.id,
        "name": student.name,
        "roll_no": student.roll_no,
        "course": student.course,
    }


@app.post("/students")
def add_student(
    data: StudentInput,
    db: Session = Depends(get_db)
):

    student = Student(
        name=data.name.strip(),
        roll_no=data.roll_no.strip(),
        course=data.course.strip(),
    )

    db.add(student)

    try:
        db.commit()
        db.refresh(student)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="This roll number already exists."
        )

    return {
        "message": "Student added successfully",
        "student_id": student.id,
    }


@app.put("/students/{student_id}")
def update_student(
    student_id: int,
    data: StudentInput,
    db: Session = Depends(get_db)
):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    student.name = data.name.strip()
    student.roll_no = data.roll_no.strip()
    student.course = data.course.strip()

    try:
        db.commit()
        db.refresh(student)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="This roll number already exists."
        )

    return {
        "message": "Student updated successfully"
    }


@app.delete("/students/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db)
):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    db.delete(student)
    db.commit()

    return {
        "message": "Student deleted successfully"
    }


# ---------------- FACE REGISTRATION ----------------

@app.post("/students/{student_id}/register-face")
def register_student_face(
    student_id: int,
    db: Session = Depends(get_db)
):

    student = db.query(Student).filter(
        Student.id == student_id
    ).first()

    if student is None:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    if student.face_encoding:
        raise HTTPException(
            status_code=400,
            detail="Face already registered for this student"
        )

    backend_folder = os.path.dirname(
        os.path.abspath(__file__)
    )

    script_path = os.path.join(
        backend_folder,
        "register_face.py"
    )

    if not os.path.exists(script_path):
        raise HTTPException(
            status_code=500,
            detail="register_face.py was not found"
        )

    try:
        process = subprocess.Popen(
            [sys.executable, script_path, str(student_id)],
            cwd=backend_folder
        )

        return {
            "message": "Face registration camera started",
            "student_id": student_id,
            "process_id": process.pid
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ---------------- ATTENDANCE HISTORY ----------------

@app.get("/attendance")
def get_attendance(
    date: str | None = None,
    db: Session = Depends(get_db)
):

    query = text("""
        SELECT
            a.id,
            a.student_id,
            s.name AS student_name,
            s.roll_no,
            s.course,
            a.attendance_date,
            a.attendance_time,
            a.status
        FROM attendance AS a
        LEFT JOIN students AS s
            ON s.id = a.student_id
        WHERE (
            :selected_date IS NULL
            OR a.attendance_date = :selected_date
        )
        ORDER BY
            a.attendance_date DESC,
            a.attendance_time DESC
    """)

    rows = db.execute(
        query,
        {"selected_date": date}
    ).mappings().all()

    return [dict(row) for row in rows]


# ---------------- ATTENDANCE SUMMARY ----------------

@app.get("/attendance/summary")
def attendance_summary(
    selected_date: date | None = None,
    db: Session = Depends(get_db)
):

    attendance_date = selected_date or date.today()

    query = text("""
        SELECT
            s.id AS student_id,
            s.name,
            s.roll_no,
            s.course,

            CASE
                WHEN a.id IS NOT NULL THEN 'Present'
                ELSE 'Absent'
            END AS status,

            a.attendance_time

        FROM students s

        LEFT JOIN attendance a
            ON s.id = a.student_id
            AND a.attendance_date = :attendance_date

        ORDER BY s.name
    """)

    rows = db.execute(
        query,
        {
            "attendance_date": attendance_date.isoformat()
        }
    ).mappings().all()

    students = [dict(row) for row in rows]

    total = len(students)

    present = sum(
        1 for student in students
        if student["status"] == "Present"
    )

    absent = total - present

    percentage = (
        round(present * 100 / total, 2)
        if total > 0 else 0
    )

    return {
        "date": attendance_date.isoformat(),
        "total_students": total,
        "present": present,
        "absent": absent,
        "attendance_percentage": percentage,
        "students": students
    }
