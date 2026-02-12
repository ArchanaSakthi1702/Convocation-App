from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import User,Role
from app.helpers.class_finder_for_staffs_creation import get_classes_from_request
from app.schemas.staff_schemas import StaffCreate,StaffUpdate
from app.auth.dependencies import is_admin

router = APIRouter(
    tags=["Admin Staff Creation"],
    dependencies=[Depends(is_admin)],
    prefix="/admin"
)


@router.post("/staff/create")
async def create_staff(
    staff_data: StaffCreate,
    db: AsyncSession = Depends(get_db)
):
    # Check duplicate roll number
    result = await db.execute(
        select(User).where(User.staff_roll_number == staff_data.staff_roll_number)
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Staff with this roll number already exists"
        )

    # 🔹 Fetch role objects
    role_result = await db.execute(
        select(Role).where(Role.name.in_(staff_data.roles))
    )
    role_objects = role_result.scalars().all()

    if len(role_objects) != len(staff_data.roles):
        raise HTTPException(
            status_code=400,
            detail="One or more roles are invalid"
        )

    # 🔹 Fetch assigned classes
    assigned_classes = await get_classes_from_request(
        db,
        ids=staff_data.assigned_class_ids,
        names=staff_data.assigned_class_names
    )

    # 🔹 Create user
    new_staff = User(
        staff_name=staff_data.staff_name,
        staff_roll_number=staff_data.staff_roll_number,
        roles=role_objects,  # ✅ attach Role objects
        gender=staff_data.gender.lower(),
        assigned_classes=assigned_classes,
        can_handle_both_genders=staff_data.can_handle_both_genders
    )

    db.add(new_staff)
    await db.commit()

    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == new_staff.id)
    )

    new_staff = result.scalars().first()

    return {
        "message": "Staff created successfully",
        "staff_id": str(new_staff.id),
        "staff_roll_number": new_staff.staff_roll_number,
        "staff_name": new_staff.staff_name,
        "roles": [role.name.value for role in new_staff.roles]
    }

@router.post("/staff/bulk-create")
async def bulk_create_staff(
    staff_list: List[StaffCreate],
    db: AsyncSession = Depends(get_db)
):
    created_staffs = []

    for staff_data in staff_list:

        # Skip duplicates
        result = await db.execute(
            select(User).where(
                User.staff_roll_number == staff_data.staff_roll_number
            )
        )
        existing_user = result.scalars().first()
        if existing_user:
            continue

        # 🔹 Fetch roles
        role_result = await db.execute(
            select(Role).where(Role.name.in_(staff_data.roles))
        )
        role_objects = role_result.scalars().all()

        if len(role_objects) != len(staff_data.roles):
            continue  # Skip invalid role entry

        # 🔹 Fetch classes
        assigned_classes = await get_classes_from_request(
            db,
            ids=staff_data.assigned_class_ids,
            names=staff_data.assigned_class_names
        )

        # 🔹 Create staff
        new_staff = User(
            staff_roll_number=staff_data.staff_roll_number,
            staff_name=staff_data.staff_name,
            roles=role_objects,
            gender=staff_data.gender.lower(),
            assigned_classes=assigned_classes,
            can_handle_both_genders=staff_data.can_handle_both_genders
        )

        db.add(new_staff)
        created_staffs.append(new_staff)

    await db.commit()

    return {
        "message": f"{len(created_staffs)} staffs created successfully",
        "staff_ids": [str(s.id) for s in created_staffs]
    }



@router.patch("/update-staff_roll_no")
async def update_staff_roll_no(
    data: List[StaffUpdate],
    db: AsyncSession = Depends(get_db)
):
    res = {"successes": [], "failures": []}

    try:
        for staff in data:
            result = await db.execute(
                select(User).where(User.staff_roll_number == staff.old)
            )
            db_staff = result.scalar_one_or_none()

            if not db_staff:
                res["failures"].append({
                    "old": staff.old,
                    "reason": "Old roll number not found"
                })
                continue

            # check if new roll number already exists
            result = await db.execute(
                select(User).where(User.staff_roll_number == staff.new)
            )
            if result.scalar_one_or_none():
                res["failures"].append({
                    "old": staff.old,
                    "reason": "New roll number already exists"
                })
                continue

            db_staff.staff_roll_number = staff.new
            res["successes"].append(staff.old)

        await db.commit()

    except IntegrityError:
        await db.rollback()
        return {
            "error": "Database constraint error",
            "detail": "Duplicate roll number detected"
        }

    except Exception as e:
        await db.rollback()
        raise e

    return res

