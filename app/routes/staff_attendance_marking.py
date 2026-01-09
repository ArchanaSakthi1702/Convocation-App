from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, Student,UserRole
from app.helpers.attendance_time_checker import check_attendance_time_limit
from app.schemas.attendance_marking import MarkAttendanceResponse

router = APIRouter(prefix="/attendance-staff", tags=["Attendance Incharge Marking Attendances"])


# -------------------------
# PUT: Mark Attendance
# -------------------------
@router.put("/mark-attendace", response_model=MarkAttendanceResponse)
async def mark_attendance(
    student_id: str,
    present: bool,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):

    # 1. Only attendance incharge allowed
    if (current_user.role != UserRole.attendance_incharge and 
        not getattr(current_user,"can_access_both",False)):
        raise HTTPException(status_code=403, detail="Not authorized")

    # 2. Time limit check
    check_attendance_time_limit()

    # 3. Convert student_id into UUID bytes (SQLite BLOB)
    try:
        student_uuid = UUID(student_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid student_id format")

    # 4. Fetch student WITH CLASS using selectinload (prevents lazy loading)
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.class_ref))
        .where(Student.id == student_uuid)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # 5. Fetch current_user WITH assigned_classes using selectinload
    user_result = await db.execute(
        select(User)
        .options(selectinload(User.assigned_classes))
        .where(User.id == current_user.id)
    )
    staff = user_result.scalar_one_or_none()

    if not staff:
        raise HTTPException(status_code=404, detail="User not found")

    # 6. Check assigned class constraint
    assigned_class_ids = {c.id for c in staff.assigned_classes}

    if student.class_id not in assigned_class_ids:
        raise HTTPException(
            status_code=403,
            detail="You are not assigned to this student's class"
        )

    # 7. Same gender restriction
    if student.gender != staff.gender:
        raise HTTPException(
            status_code=403,
            detail="You can mark attendance only for same-gender students"
        )

    # 8. Update attendance
    student.present = present
    await db.commit()
    await db.refresh(student)

    return {
        "message": "Attendance updated successfully",
        "student_id": student_id,
        "student_name": student.name,
        "present": present
    }
