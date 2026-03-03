# schemas/seating.py

from pydantic import BaseModel
from uuid import UUID
from typing import List


class SeatingPlanCreate(BaseModel):
    class_id: UUID
    gender: str
    chair_from: int
    chair_to: int


class SeatingPlanBulkCreate(BaseModel):
    seating_plans: List[SeatingPlanCreate]

class SeatingPlanUpdate(BaseModel):
    chair_from: int | None = None
    chair_to: int | None = None


class SeatingPlanResponse(BaseModel):
    id: UUID
    class_id: UUID
    gender: str
    chair_from: int
    chair_to: int

    class Config:
        from_attributes = True


class SeatingInfo(BaseModel):
    gender: str
    chair_from: int
    chair_to: int