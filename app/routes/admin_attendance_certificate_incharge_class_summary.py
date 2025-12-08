from fastapi import Depends,APIRouter,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User,UserRole,Student,Class
from app.database import get_db
from app.schemas.class_summary import ClassSummaryResponse,ClassSummaryItem
from app.auth.dependencies import get_current_user


router=APIRouter(
    prefix="/class",
    tags=["Class Summary"]
)


@router.get("/summary", response_model=ClassSummaryResponse)
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

    # --- 2. Determine accessible classes ---
    if current_user.role == UserRole.admin:
        class_result = await db.execute(select(Class))
        classes_list = class_result.scalars().all()
        accessible_class_ids = {c.id for c in classes_list}
    else:
        classes_list = user.assigned_classes
        accessible_class_ids = {c.id for c in classes_list}

    if not accessible_class_ids:
        return ClassSummaryResponse(role=current_user.role, summary=[])

    # --- 3. INIT summary for all classes ---
    summary_dict = {
        str(cls.id): {
            "class_id": str(cls.id),
            "class_name": "",
            "total_students": 0,
            "present_count": 0,
            "absent_count": 0,
        }
        for cls in classes_list
    }

    # --- 4. Fetch students ---
    student_result = await db.execute(
        select(Student).where(Student.class_id.in_(accessible_class_ids))
    )
    students = student_result.scalars().all()

    # Count students
    for student in students:
        cid = str(student.class_id)
        summary_dict[cid]["total_students"] += 1
        if student.present:
            summary_dict[cid]["present_count"] += 1
        else:
            summary_dict[cid]["absent_count"] += 1

    # --- 5. Load class names ---
    class_details = await db.execute(
        select(Class)
        .options(selectinload(Class.class_name_ref))
        .where(Class.id.in_(accessible_class_ids))
    )
    classes = class_details.scalars().all()

    for cls in classes:
        summary_dict[str(cls.id)]["class_name"] = cls.class_name_ref.name

    # Convert dict → Pydantic models
    final_summary = [
        ClassSummaryItem(**item) for item in summary_dict.values()
    ]

    return ClassSummaryResponse(
        role=current_user.role.value,
        summary=final_summary
    )