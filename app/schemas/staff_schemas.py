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