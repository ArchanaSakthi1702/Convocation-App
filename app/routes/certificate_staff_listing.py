from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Class, UserRole
from app.schemas.certificate_staff_listing_students import StaffClassesResponse,ClassWithStudentsResponse

router = APIRouter(
    prefix="/certificate-staff",
    tags=["Certificate Incharge Attendance Listing"]
)

@router.get("/list-classes",response_model=StaffClassesResponse)
async def list_classes_for_certificate_incharge(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Allowed only for certificate incharge
    if current_user.role != UserRole.certificate_incharge:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(
        select(User)
        .options(
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

    classes = [
        {
            "class_id": str(c.id),
            "class_name": c.class_name_ref.name,
            "department": c.department,
            "section": c.section,
            "regular_or_self": c.regular_or_self
        }
        for c in staff.assigned_classes
    ]

    return {
        "staff_id": str(current_user.id),
        "staff_name": current_user.staff_name,
        "assigned_classes_count": len(classes),
        "classes": classes
    }



@router.get("/class/{class_id}/students", response_model=ClassWithStudentsResponse)
async def get_students_by_class(
    class_id: str,
    present: Optional[bool] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Allowed only for certificate incharge
    if current_user.role != UserRole.certificate_incharge:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    try:
        class_uuid = UUID(class_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staff ID format")


    # Load class with students
    result = await db.execute(
        select(Class)
        .options(
            selectinload(Class.students),
            selectinload(Class.class_name_ref)
        )
        .where(Class.id == class_uuid)
    )
    cls = result.scalar_one_or_none()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    # Check staff actually has access to this class
    result_staff = await db.execute(
        select(User)
        .options(selectinload(User.assigned_classes))
        .where(User.id == current_user.id)
    )
    staff = result_staff.scalar_one()

    if cls not in staff.assigned_classes:
        raise HTTPException(status_code=403, detail="You are not incharge of this class")

    # Apply present filter
    if present is None:
        filtered_students = cls.students
    else:
        filtered_students = [s for s in cls.students if s.present == present]

    return {
        "class_id": str(cls.id),
        "class_name": cls.class_name_ref.name,
        "department": cls.department,
        "section": cls.section,
        "regular_or_self": cls.regular_or_self,
        "students_count": len(filtered_students),
        "students": [
            {
                "student_id": str(s.id),
                "roll_number": s.roll_number,
                "name": s.name,
                "gender": s.gender,
                "present": s.present
            }
            for s in filtered_students
        ]
    }
