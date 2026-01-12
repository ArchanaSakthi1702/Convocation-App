from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.auth.dependencies import is_admin
from uuid import UUID

from app.database import get_db
from app.models import Class, Student
from app.schemas.student_schemas import StudentListByClassResponse


router = APIRouter(
    prefix="/student",
    tags=["Admin Student Listing"],
    dependencies=[Depends(is_admin)]
)




# ---------------------------------------------------------
# List all students in a class (with optional ?present=bool)
# ---------------------------------------------------------
@router.get("/list-by-class/{class_id}",response_model=StudentListByClassResponse)
async def get_students_by_class(
    class_id: str,
    present: bool | None = Query(None),
    db: AsyncSession = Depends(get_db)
):

    # Validate UUID format
    try:
        class_uuid = UUID(class_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid class_id format")

    # Confirm class exists
    class_query = await db.execute(select(Class).where(Class.id == class_uuid))
    class_obj = class_query.scalars().first()

    if not class_obj:
        raise HTTPException(status_code=404, detail="Class not found")

    # Build query
    query = (
        select(Student)
        .where(Student.class_id == class_uuid)
        .order_by(Student.roll_number.asc())
    )

    # Optional filter
    if present is not None:
        query = query.where(Student.present == present)

    # Execute query (async-safe, no lazy loading)
    result = await db.execute(query)
    students = result.scalars().all()

    # Response
    return {
        "class_id": str(class_id),
        "total_students": len(students),
        "filtered_by_present": present,
        "students": [
            {
                "student_id": str(s.id),
                "roll_number": s.roll_number,
                "name": s.name,
                "gender": s.gender,
                "present": s.present,
            }
            for s in students
        ],
    }
