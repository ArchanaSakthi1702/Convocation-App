# app/routes/student_routes.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import get_db
from app.auth.dependencies import is_admin
from app.models import User
from app.schemas.staff_schemas import StaffFullUpdate
from app.helpers.class_finder_for_staffs_creation import get_classes_from_request

router = APIRouter(
    tags=["Admin Staff Updation"],
    dependencies=[Depends(is_admin)],
    prefix="/admin"
)


@router.patch("/staff/update/by-roll/{staff_roll_number}")
async def update_staff_by_roll_number(
    staff_roll_number: str,
    payload: StaffFullUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.staff_roll_number == staff_roll_number)
    )
    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    # 🔐 Roll number uniqueness check
    if payload.staff_roll_number and payload.staff_roll_number != staff.staff_roll_number:
        result = await db.execute(
            select(User).where(User.staff_roll_number == payload.staff_roll_number)
        )
        if result.scalars().first():
            raise HTTPException(
                status_code=400,
                detail="Staff roll number already exists"
            )
        staff.staff_roll_number = payload.staff_roll_number

    if payload.staff_name is not None:
        staff.staff_name = payload.staff_name

    if payload.role is not None:
        staff.role = payload.role

    if payload.gender is not None:
        staff.gender = payload.gender

    # 🔁 Update assigned classes (if provided)
    if payload.assigned_class_ids or payload.assigned_class_names:
        assigned_classes = await get_classes_from_request(
            db,
            ids=payload.assigned_class_ids,
            names=payload.assigned_class_names
        )
        staff.assigned_classes = assigned_classes

    await db.commit()
    await db.refresh(staff)

    return {
        "message": "Staff updated successfully",
        "staff_id": str(staff.id),
        "staff_roll_number": staff.staff_roll_number,
        "staff_name": staff.staff_name,
        "role": staff.role
    }



@router.put("/staff/update/by-id/{staff_id}")
async def update_staff_by_id(
    staff_id: UUID,
    payload: StaffFullUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.id == staff_id)
    )
    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    if payload.staff_roll_number and payload.staff_roll_number != staff.staff_roll_number:
        result = await db.execute(
            select(User).where(User.staff_roll_number == payload.staff_roll_number)
        )
        if result.scalars().first():
            raise HTTPException(status_code=400, detail="Staff roll number already exists")
        staff.staff_roll_number = payload.staff_roll_number

    if payload.staff_name is not None:
        staff.staff_name = payload.staff_name

    if payload.role is not None:
        staff.role = payload.role

    if payload.gender is not None:
        staff.gender = payload.gender

    if payload.assigned_class_ids or payload.assigned_class_names:
        assigned_classes = await get_classes_from_request(
            db,
            ids=payload.assigned_class_ids,
            names=payload.assigned_class_names
        )
        staff.assigned_classes = assigned_classes

    await db.commit()
    await db.refresh(staff)

    return {
        "message": "Staff updated successfully",
        "staff_id": str(staff.id),
        "staff_roll_number": staff.staff_roll_number,
        "staff_name": staff.staff_name,
        "role": staff.role
    }