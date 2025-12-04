from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Class, UserRole

router = APIRouter(
    prefix="/certificate-staff",
    tags=["Certificate Incharge Attendance Listing"]
)


@router.get("/list-students")
async def list_students_for_certificate_incharge(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 1. Only certificate_incharge is allowed
    if current_user.role != UserRole.certificate_incharge:
        raise HTTPException(status_code=403, detail="Not authorized")

    # 2. Load user with assigned classes + students
    result = await db.execute(
        select(User)
        .options(
            selectinload(User.assigned_classes)
            .selectinload(Class.students),
            selectinload(User.assigned_classes)
            .selectinload(Class.class_name_ref)
        )
        .where(User.id == current_user.id)
    )

    staff = result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="User not found")

    if not staff.assigned_classes:
        return {
            "message": "No classes assigned",
            "classes": []
        }

    response_data = []

    # 3. Build output grouped by class (NO gender filter)
    for c in staff.assigned_classes:
        response_data.append({
            "class_id": c.id,
            "class_name": c.class_name_ref.name,
            "department": c.department,
            "section": c.section,
            "regular_or_self": c.regular_or_self,
            "students_count": len(c.students),
            "students": [
                {
                    "student_id": s.id,
                    "roll_number": s.roll_number,
                    "name": s.name,
                    "gender": s.gender,
                    "present": s.present
                }
                for s in c.students
            ]
        })

    return {
        "staff_id": current_user.id,
        "staff_name": current_user.staff_name,
        "assigned_classes_count": len(staff.assigned_classes),
        "classes": response_data
    }
