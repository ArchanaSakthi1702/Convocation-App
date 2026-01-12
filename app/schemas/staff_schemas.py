from pydantic import BaseModel,Field
from typing import Optional,List
from uuid import UUID

from app.models import UserRole

class StaffCreate(BaseModel):
    staff_roll_number: str
    role: UserRole
    staff_name:Optional[str]=None
    gender: str
    assigned_class_ids: Optional[List[str]] = None
    assigned_class_names: Optional[List[str]] = None


class StaffFullUpdate(BaseModel):
    staff_name: Optional[str] = None
    staff_roll_number: Optional[str] = None
    role: Optional[str] = None
    gender: Optional[str] = None

    # Class assignment
    assigned_class_ids: Optional[List[UUID]] = None
    assigned_class_names: Optional[List[str]] = None
    

class StaffRead(BaseModel):
    id: str
    staff_name: Optional[str]
    staff_roll_number: Optional[str]
    role: str
    gender: str
    assigned_classes: List[str] = []

    class Config:
        orm_mode = True


class AssignedClassRead(BaseModel):
    id: str
    name: str


class StaffRead2(BaseModel):
    id: str
    staff_name: str
    staff_roll_number: str
    role: str
    gender: str
    assigned_classes: List[AssignedClassRead]
    

class StaffListResponse(BaseModel):
    count: int
    staffs: List[StaffRead]


class StaffUpdate(BaseModel):
    old:str
    new:str