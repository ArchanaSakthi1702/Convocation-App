from fastapi import APIRouter,HTTPException,Depends
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserRole,User,Class
from app.auth.dependencies import get_current_user
from app.database import get_db


router=APIRouter(
    prefix="/hod",
    tags=["HOD Endpoints"]
)



@router.get("/hod/list-present-students")
async def list_present_students_for_hod(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # 🔐 Allow only HOD role
    role_names = [role.name for role in current_user.roles]

    if UserRole.hod not in role_names:
        raise HTTPException(status_code=403, detail="HOD access required")

    # 🔹 Load user with assigned classes + students + class name
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

    hod = result.scalars().first()

    if not hod:
        raise HTTPException(status_code=404, detail="User not found")

    if not hod.assigned_classes:
        return {
            "message": "No classes assigned",
            "classes": []
        }

    response_data = []

    for cls in hod.assigned_classes:
        # ✅ Only present students (no gender filter)
        present_students = [
            {
                "student_id": str(student.id),
                "roll_number": student.roll_number,
                "name": student.name,
                "gender": student.gender,
                "present": student.present
            }
            for student in cls.students
            if student.present is True
        ]

        response_data.append({
            "class_id": str(cls.id),
            "class_name": cls.class_name_ref.name if cls.class_name_ref else None,
            "department": cls.department,
            "section": cls.section,
            "regular_or_self": cls.regular_or_self,
            "students_count": len(present_students),
            "students": present_students
        })

    return {
        "hod_id": str(hod.id),
        "hod_name": hod.staff_name,
        "assigned_classes_count": len(hod.assigned_classes),
        "classes": response_data
    }
