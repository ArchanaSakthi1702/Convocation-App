from pydantic import BaseModel
from typing import Optional,List

class ClassCreate(BaseModel):
    class_name: str
    program_type: str  # UG / PG
    department: str = None
    section: str = None
    regular_or_self: str = None  # "Regular" / "Self-Financed"

class ClassUpdate(BaseModel):
    class_name: Optional[str] = None
    program_type: Optional[str] = None
    department: Optional[str] = None
    section: Optional[str] = None
    regular_or_self: Optional[str] = None


class ClassItem(BaseModel):
    id: str
    class_name: str
    program_type: str
    department: str | None
    section: str | None
    regular_or_self: str | None

class ClassListResponse(BaseModel):
    count: int
    classes: List[ClassItem]