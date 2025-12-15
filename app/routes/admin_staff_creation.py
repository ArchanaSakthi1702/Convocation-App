from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from typing import List

from app.database import get_db
from app.models import User
from app.helpers.class_finder_for_staffs_creation import get_classes_from_request
from app.schemas.staff_schemas import StaffCreate
from app.auth.dependencies import is_admin

router = APIRouter(
    tags=["Admin Staff Creation"],
    dependencies=[Depends(is_admin)],
    prefix="/admin"
)



@router.post("/staff/create")
async def create_staff(staff_data: StaffCreate, db: AsyncSession = Depends(get_db)):
    # Check if staff_roll_number already exists
    result = await db.execute(select(User).where(User.staff_roll_number == staff_data.staff_roll_number))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Staff with this roll number already exists")

    # Fetch assigned classes
    assigned_classes = await get_classes_from_request(
        db, ids=staff_data.assigned_class_ids, names=staff_data.assigned_class_names
    )

    new_staff = User(
        staff_name=staff_data.staff_name,
        staff_roll_number=staff_data.staff_roll_number,
        role=staff_data.role,
        gender=staff_data.gender,
        assigned_classes=assigned_classes
    )
    db.add(new_staff)
    await db.commit()
    await db.refresh(new_staff)

    return {
        "message": "Staff created successfully",
        "staff_id": str(new_staff.id),
        "staff_roll_number": new_staff.staff_roll_number,
        "staff_name":new_staff.staff_name,
        "role": new_staff.role
    }


@router.post("/staff/bulk-create")
async def bulk_create_staff(staff_list: List[StaffCreate], db: AsyncSession = Depends(get_db)):
    created_staffs = []

    for staff_data in staff_list:
        # Skip duplicates
        result = await db.execute(select(User).where(User.staff_roll_number == staff_data.staff_roll_number))
        existing_user = result.scalars().first()
        if existing_user:
            continue

        assigned_classes = await get_classes_from_request(
            db, ids=staff_data.assigned_class_ids, names=staff_data.assigned_class_names
        )

        new_staff = User(
            staff_roll_number=staff_data.staff_roll_number,
            staff_name=staff_data.staff_name,
            role=staff_data.role,
            gender=staff_data.gender.lower(),
            assigned_classes=assigned_classes
        )
        db.add(new_staff)
        created_staffs.append(new_staff)

    await db.commit()

    return {
        "message": f"{len(created_staffs)} staffs created successfully",
        "staff_ids": [str(s.id) for s in created_staffs]
    }
