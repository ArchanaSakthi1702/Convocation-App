# routers/seating.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models import SeatingPlan, User
from app.schemas.seating import (
    SeatingPlanCreate,
    SeatingPlanUpdate,
    SeatingPlanResponse,
    SeatingPlanBulkCreate
)
from app.auth.dependencies import is_admin

router = APIRouter(prefix="/seating", tags=["Seating"])



@router.post("/", response_model=SeatingPlanResponse)
async def create_seating_plan(
    data: SeatingPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    if data.chair_from > data.chair_to:
        raise HTTPException(status_code=400, detail="Invalid chair range")

    # Prevent duplicate class + gender
    existing = db.query(SeatingPlan).filter(
        SeatingPlan.class_id == data.class_id,
        SeatingPlan.gender == data.gender
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="Seating plan already exists")

    seating = SeatingPlan(
        class_id=data.class_id,
        gender=data.gender,
        chair_from=data.chair_from,
        chair_to=data.chair_to
    )

    db.add(seating)
    db.commit()
    db.refresh(seating)

    return seating



@router.put("/{seating_id}", response_model=SeatingPlanResponse)
async def update_seating_plan(
    seating_id: UUID,
    data: SeatingPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    seating = db.query(SeatingPlan).filter(
        SeatingPlan.id == seating_id
    ).first()

    if not seating:
        raise HTTPException(status_code=404, detail="Seating plan not found")

    if data.chair_from is not None:
        seating.chair_from = data.chair_from

    if data.chair_to is not None:
        seating.chair_to = data.chair_to

    if seating.chair_from > seating.chair_to:
        raise HTTPException(status_code=400, detail="Invalid chair range")

    db.commit()
    db.refresh(seating)

    return seating



@router.delete("/{seating_id}")
async def delete_seating_plan(
    seating_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    seating = db.query(SeatingPlan).filter(
        SeatingPlan.id == seating_id
    ).first()

    if not seating:
        raise HTTPException(status_code=404, detail="Seating plan not found")

    db.delete(seating)
    db.commit()

    return {"message": "Seating plan deleted successfully"}


@router.post("/bulk", response_model=list[SeatingPlanResponse])
async def bulk_create_seating_plans(
    data: SeatingPlanBulkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(is_admin)
):
    created_seatings = []

    for item in data.seating_plans:

        # Validate chair range
        if item.chair_from > item.chair_to:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid chair range for class {item.class_id}"
            )

        # Prevent duplicate class + gender
        existing = db.query(SeatingPlan).filter(
            SeatingPlan.class_id == item.class_id,
            SeatingPlan.gender == item.gender
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Seating plan already exists for class {item.class_id} and gender {item.gender}"
            )

        seating = SeatingPlan(
            class_id=item.class_id,
            gender=item.gender,
            chair_from=item.chair_from,
            chair_to=item.chair_to
        )

        db.add(seating)
        created_seatings.append(seating)

    db.commit()

    for seating in created_seatings:
        db.refresh(seating)

    return created_seatings