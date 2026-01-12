from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ProgramType,Class
from app.auth.dependencies import is_admin  # your admin dependency
from app.schemas.class_schemas import ClassItem,ClassListResponse

from app.schemas.program_types import (
    ProgramTypeListResponse,
    ProgramTypeItem,
    ClassItem,
    ClassListByProgramTypeResponse
)

router = APIRouter(
    prefix="/admin/program-types",
    tags=["Admin Program Types Listing"],
    dependencies=[Depends(is_admin)]
)


# ---------------------------------------------------
# 1. List Program Types
# ---------------------------------------------------
@router.get("/list-program-types", response_model=ProgramTypeListResponse)
async def list_program_types(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProgramType))
    program_types = result.scalars().all()

    return ProgramTypeListResponse(
        count=len(program_types),
        program_types=[
            ProgramTypeItem(
                id=str(pt.id),
                type_name=pt.type_name
            )
            for pt in program_types
        ]
    )


# ---------------------------------------------------
# 2. Get Classes by Program Type Name
# ---------------------------------------------------
@router.get("/get-classes-by-program-type-name/{program_type_name}",
            response_model=ClassListByProgramTypeResponse)
async def get_classes_by_program_type_name(
    program_type_name: str,
    db: AsyncSession = Depends(get_db)
):

    result = await db.execute(
        select(ProgramType).where(ProgramType.type_name == program_type_name)
    )
    program_type = result.scalars().first()

    if not program_type:
        raise HTTPException(
            status_code=404,
            detail=f"Program type '{program_type_name}' not found"
        )

    result = await db.execute(
        select(Class)
        .options(
            selectinload(Class.class_name_ref),
            selectinload(Class.program_type_ref),
        )
        .where(Class.program_type_id == program_type.id)
    )

    classes = result.scalars().all()

    return ClassListByProgramTypeResponse(
        program_type=program_type.type_name,
        count=len(classes),
        classes=[
            ClassItem(
                id=str(c.id),
                class_name=c.class_name_ref.name,
                program_type=c.program_type_ref.type_name,
                department=c.department,
                section=c.section,
                regular_or_self=c.regular_or_self,
            )
            for c in classes
        ]
    )


# ---------------------------------------------------
# 3. Get Classes by Program Type ID
# ---------------------------------------------------
@router.get("/get-classes-by-program-type-id/{program_type_id}",
            response_model=ClassListByProgramTypeResponse)
async def get_classes_by_program_type_id(
    program_type_id: str,
    db: AsyncSession = Depends(get_db)
):

    try:
        program_type_uuid = UUID(program_type_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid program_type_id")

    result = await db.execute(
        select(ProgramType).where(ProgramType.id == program_type_uuid)
    )
    program_type = result.scalars().first()

    if not program_type:
        raise HTTPException(status_code=404, detail="Program type not found")

    result = await db.execute(
        select(Class)
        .options(
            selectinload(Class.class_name_ref),
            selectinload(Class.program_type_ref),
        )
        .where(Class.program_type_id == program_type_uuid)
    )

    classes = result.scalars().all()

    return ClassListByProgramTypeResponse(
        program_type=program_type.type_name,
        count=len(classes),
        classes=[
            ClassItem(
                id=str(c.id),
                class_name=c.class_name_ref.name,
                program_type=c.program_type_ref.type_name,
                department=c.department,
                section=c.section,
                regular_or_self=c.regular_or_self,
            )
            for c in classes
        ]
    )



@router.get("/list-classes", response_model=ClassListResponse)
async def list_all_classes(db: AsyncSession = Depends(get_db)):
    """
    Fetch all classes from the database
    """

    result = await db.execute(
        select(Class)
        .options(
            selectinload(Class.class_name_ref),
            selectinload(Class.program_type_ref)
        )
    )

    classes = result.scalars().all()

    class_list = []
    for c in classes:
        class_list.append({
            "id": str(c.id),
            "class_name": c.class_name_ref.name if c.class_name_ref else "",
            "program_type": c.program_type_ref.type_name if c.program_type_ref else "",
            "department": c.department or "",
            "section": c.section or "",
            "regular_or_self": c.regular_or_self or ""
        })

    return ClassListResponse(count=len(class_list), classes=class_list)