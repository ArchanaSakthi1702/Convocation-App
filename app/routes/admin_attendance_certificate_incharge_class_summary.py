from fastapi import Depends,APIRouter,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User,UserRole,Student,Class
from app.database import get_db
from app.auth.dependencies import get_current_user


router=APIRouter(
    prefix="/class",
    tags=["Class Summary"]
)


@router.get("/summary")
async def attendance_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # --- 1. Fetch current user with assigned classes ---
    user_result = await db.execute(
        select(User)
        .options(selectinload(User.assigned_classes))
        .where(User.id == current_user.id)
    )
    user = user_result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # --- 2. Determine accessible classes based on role ---
    accessible_class_ids = set()

    if current_user.role == UserRole.admin:
        # Admin → all classes
        class_result = await db.execute(select(Class))
        classes = class_result.scalars().all()
        accessible_class_ids = {c.id for c in classes}

    else:
        # Attendance + Certificate incharge → only assigned classes
        accessible_class_ids = {c.id for c in user.assigned_classes}

    if not accessible_class_ids:
        return {"message": "No assigned classes", "summary": []}

    # --- 3. Fetch all students belonging to these classes ---
    student_result = await db.execute(
        select(Student)
        .where(Student.class_id.in_(accessible_class_ids))
    )
    students = student_result.scalars().all()

    # --- 4. Prepare summary structured by class ---
    summary = {}

    for student in students:
        cid = str(student.class_id)

        if cid not in summary:
            summary[cid] = {
                "class_id": cid,
                "class_name": "",   # Will fill later
                "total_students": 0,
                "present_count": 0,
                "absent_count": 0
            }

        summary[cid]["total_students"] += 1
        if student.present:
            summary[cid]["present_count"] += 1
        else:
            summary[cid]["absent_count"] += 1

    # --- 5. Load class names for final summary ---
    class_details = await db.execute(
        select(Class).options(selectinload(Class.class_name_ref))
        .where(Class.id.in_(accessible_class_ids))
    )
    classes = class_details.scalars().all()

    for cls in classes:
        summary[str(cls.id)]["class_name"] = cls.class_name_ref.name

    return {
        "role": current_user.role,
        "summary": list(summary.values())
    }
