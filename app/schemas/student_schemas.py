from pydantic import BaseModel, Field
from typing import List, Optional

class StudentCreate(BaseModel):
    roll_number: str
    name: str
    gender: str = Field(..., pattern="^(male|female)$")

    # Option 1: Direct class_id
    class_id: Optional[str] = None

    # Option 2: Class name data
    class_name: Optional[str] = None       # e.g., "I BCA"
    program_type: Optional[str] = None     # UG / PG
    department: Optional[str] = None
    section: Optional[str] = None


class StudentBulkCreate(BaseModel):
    students: List[StudentCreate]
