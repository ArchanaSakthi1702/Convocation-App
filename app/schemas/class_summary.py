from pydantic import BaseModel
from typing import List


class ClassSummaryItem(BaseModel):
    class_id: str
    class_name: str
    total_students: int
    present_count: int
    absent_count: int


class ClassSummaryResponse(BaseModel):
    role: str
    summary: List[ClassSummaryItem]
