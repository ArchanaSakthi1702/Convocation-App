from pydantic import BaseModel,Field,ConfigDict
from typing import Optional,List
from uuid import UUID

from app.models import UserRole


# ----------------------------
# Create Staff
# ----------------------------
class StaffCreate(BaseModel):
    staff_roll_number: str
    roles: List[UserRole]              # ✅ plural + required
    staff_name: Optional[str] = None
    gender: str
    assigned_class_ids: Optional[List[UUID]] = None
    assigned_class_names: Optional[List[str]] = None
    can_handle_both_genders: bool = False   # ✅ no need Optional


# ----------------------------
# Full Update Staff
# ----------------------------
class StaffFullUpdate(BaseModel):
    staff_name: Optional[str] = None
    staff_roll_number: Optional[str] = None
    roles: Optional[List[UserRole]] = None   # ✅ plural + optional
    gender: Optional[str] = None
    can_handle_both_genders: Optional[bool] = None

    assigned_class_ids: Optional[List[UUID]] = None
    assigned_class_names: Optional[List[str]] = None

class StaffRead(BaseModel):
    id: str
    staff_name: Optional[str] = None
    staff_roll_number: Optional[str] = None
    roles: List[UserRole]          # ✅ plural + list
    gender: str
    assigned_classes: List[str] = []

    model_config = ConfigDict(from_attributes=True)


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