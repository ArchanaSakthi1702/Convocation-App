from pydantic import BaseModel
from typing import List
from typing import Optional


# ----------------------
#  ProgramType Schema
# ----------------------
class ProgramTypeItem(BaseModel):
    id: str
    type_name: str


class ProgramTypeListResponse(BaseModel):
    count: int
    program_types: List[ProgramTypeItem]


# ----------------------
#  Class Info Schema
# ----------------------
class ClassItem(BaseModel):
    id: str
    class_name: str
    program_type: str
    department: Optional[str] = None
    section: Optional[str] = None
    regular_or_self: Optional[str] = None


class ClassListByProgramTypeResponse(BaseModel):
    program_type: str
    count: int
    classes: List[ClassItem]