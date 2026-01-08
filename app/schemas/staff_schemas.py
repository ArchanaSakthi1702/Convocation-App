from pydantic import BaseModel,Field
from typing import Optional,List

from app.models import UserRole

class StaffCreate(BaseModel):
    staff_roll_number: str
    role: UserRole
    staff_name:Optional[str]=None
    gender: str
    assigned_class_ids: Optional[List[str]] = None
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


class StaffListResponse(BaseModel):
    count: int
    staffs: List[StaffRead]


class StaffUpdate(BaseModel):
    old:str
    new:str