# app/routes/student_routes.py
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.auth.dependencies import is_admin
from app.models import User,Role
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

    # 🔹 Load with roles to avoid future lazy loading
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.staff_roll_number == staff_roll_number)
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

    if payload.gender is not None:
        staff.gender = payload.gender.lower()

    if payload.can_handle_both_genders is not None:
        staff.can_handle_both_genders = payload.can_handle_both_genders

    # 🔹 Update roles
    if payload.roles is not None:
        role_result = await db.execute(
            select(Role).where(Role.name.in_(payload.roles))
        )
        role_objects = role_result.scalars().all()

        if len(role_objects) != len(payload.roles):
            raise HTTPException(status_code=400, detail="Invalid roles provided")

        staff.roles = role_objects

    # 🔹 Update assigned classes
    if payload.assigned_class_ids or payload.assigned_class_names:
        assigned_classes = await get_classes_from_request(
            db,
            ids=payload.assigned_class_ids,
            names=payload.assigned_class_names
        )
        staff.assigned_classes = assigned_classes

    await db.commit()

    # 🔥 Reload again with roles after commit
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == staff.id)
    )
    staff = result.scalars().first()

    return {
        "message": "Staff updated successfully",
        "staff_id": str(staff.id),
        "staff_roll_number": staff.staff_roll_number,
        "staff_name": staff.staff_name,
        "roles": [role.name.value for role in staff.roles]
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

    if payload.gender is not None:
        staff.gender = payload.gender.lower()

    if payload.can_handle_both_genders is not None:
        staff.can_handle_both_genders = payload.can_handle_both_genders

    # 🔹 Update roles
    if payload.roles is not None:
        role_result = await db.execute(
            select(Role).where(Role.name.in_(payload.roles))
        )
        role_objects = role_result.scalars().all()

        if len(role_objects) != len(payload.roles):
            raise HTTPException(status_code=400, detail="Invalid roles provided")

        staff.roles = role_objects

    # 🔹 Update classes
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
        "roles": [role.name.value for role in staff.roles]
    }
