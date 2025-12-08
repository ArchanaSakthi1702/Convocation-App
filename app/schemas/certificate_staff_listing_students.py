from pydantic import BaseModel
from typing import List, Optional

# -----------------------------
# Schema for /list-classes
# -----------------------------
class ClassInfoForCertificateIncharge(BaseModel):
    class_id: str
    class_name: str
    department: Optional[str] = None
    section: Optional[str] = None
    regular_or_self: Optional[str] = None

class StaffClassesResponse(BaseModel):
    staff_id: str
    staff_name: Optional[str]=None
    assigned_classes_count: int
    classes: List[ClassInfoForCertificateIncharge]


# -----------------------------
# Schema for /class/{class_id}/students
# -----------------------------
class StudentInfo(BaseModel):
    student_id: str
    roll_number: str
    name: str
    gender: Optional[str] = None
    present: bool

class ClassWithStudentsResponse(BaseModel):
    class_id: str
    class_name: str
    department: Optional[str] = None
    section: Optional[str] = None
    regular_or_self: Optional[str] = None
    students_count: int
    students: List[StudentInfo]
