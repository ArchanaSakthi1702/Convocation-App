from pydantic import BaseModel
from typing import List, Optional

# Student info inside each class
class StudentInfo(BaseModel):
    student_id: str
    roll_number: str
    name: str
    gender: Optional[str] = None
    present: bool

# Class info with list of students
class ClassInfoWithStudents(BaseModel):
    class_id: str
    class_name: str
    department: Optional[str] = None
    section: Optional[str] = None
    regular_or_self: Optional[str] = None
    students_count: int
    students: List[StudentInfo]

# Main response schema for attendance-incharge
class AttendanceStaffResponse(BaseModel):
    staff_id: str
    staff_name: Optional[str] = None
    staff_gender: Optional[str] = None
    assigned_classes_count: int
    classes: List[ClassInfoWithStudents]

    class Config:
        from_attributes = True
