from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String

from database import Base


class Student(Base):

    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    roll_no = Column(
        String,
        unique=True,
        nullable=False
    )

    course = Column(
        String,
        nullable=False
    )

    face_encoding = Column(
        String,
        nullable=True
    )