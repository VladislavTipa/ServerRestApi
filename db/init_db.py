from sqlalchemy import MetaData, Table, Column, Integer, String, ForeignKey, Date
from db.db_config import get_engine

def create_tables():
    engine = get_engine()
    metadata = MetaData()

    faculties = Table("faculties", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("dean", String)
    )

    groups = Table("groups", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("faculty_id", Integer, ForeignKey("faculties.id"))
    )

    curators = Table("curators", metadata,
        Column("id", Integer, primary_key=True),
        Column("full_name", String),
        Column("status", String),
        Column("phone", String),
        Column("email", String),
        Column("group_id", Integer, ForeignKey("groups.id"))
    )

    students = Table("students", metadata,
        Column("id", Integer, primary_key=True),
        Column("full_name", String),
        Column("email", String),
        Column("phone", String),
        Column("record_book", String),
        Column("extra_data", String),
        Column("group_id", Integer, ForeignKey("groups.id"))
    )

    semesters = Table("semesters", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("start_date", Date),
        Column("end_date", Date)
    )

    teachers = Table("teachers", metadata,
        Column("id", Integer, primary_key=True),
        Column("full_name", String),
        Column("email", String),
        Column("phone", String)
    )

    subjects = Table("subjects", metadata,
        Column("id", Integer, primary_key=True),
        Column("name", String),
        Column("semester_id", Integer, ForeignKey("semesters.id")),
        Column("teacher_id", Integer, ForeignKey("teachers.id"))
    )

    grades = Table("grades", metadata,
        Column("id", Integer, primary_key=True),
        Column("student_id", Integer, ForeignKey("students.id")),
        Column("subject_id", Integer, ForeignKey("subjects.id")),
        Column("grade", String)
    )

    metadata.create_all(engine)
