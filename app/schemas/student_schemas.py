from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

class StudentCreate(BaseModel):
    roll_number: str
    name: str
    gender: str

    # Option 1: Direct class_id
    class_id: Optional[str] = None

    # Option 2: Class name data
    class_name: Optional[str] = None       # e.g., "I BCA"
    program_type: Optional[str] = None     # UG / PG
    department: Optional[str] = None
    section: Optional[str] = None


class StudentUpdate(BaseModel):
    roll_number: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    present: Optional[bool] = None
    class_id: Optional[UUID] = None

class StudentBulkCreate(BaseModel):
    students: List[StudentCreate]


class StudentItem(BaseModel):
    student_id: str
    roll_number: str
    name: str
    gender: Optional[str] = None
    present: bool


class StudentListByClassResponse(BaseModel):
    class_id: str
    total_students: int
    filtered_by_present: Optional[bool] = None
    students: List[StudentItem]


class StudentItem2(BaseModel):
    student_id: str
    roll_number: str
    name: str
    gender: Optional[str] = None
    present: bool
    class_id: str   # 🔥 added to match update API


class StudentListByClassResponse2(BaseModel):
    class_id: str
    total_students: int
    filtered_by_present: Optional[bool] = None
    students: List[StudentItem2]