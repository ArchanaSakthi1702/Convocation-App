from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Class, ClassName, ProgramType
from app.auth.dependencies import is_admin
from app.schemas.class_schemas import ClassCreate

router = APIRouter(
    tags=["Admin Classes"],
    prefix="/admin",
    dependencies=[Depends(is_admin)]
)



@router.post("/class/create")
async def create_class(class_data: ClassCreate, db: AsyncSession = Depends(get_db)):
    # Check if class with same details already exists
    result = await db.execute(
        select(Class)
        .join(ClassName)
        .join(ProgramType)
        .where(
            ClassName.name == class_data.class_name,
            ProgramType.type_name == class_data.program_type,
            Class.department == class_data.department,
            Class.section == class_data.section,
            Class.regular_or_self == class_data.regular_or_self
        )
    )
    existing_class = result.scalars().first()

    if existing_class:
        raise HTTPException(
            status_code=400,
            detail="Class with same details already exists"
        )

    # Check class name
    result = await db.execute(select(ClassName).where(ClassName.name == class_data.class_name))
    class_name_obj = result.scalars().first()
    if not class_name_obj:
        class_name_obj = ClassName(name=class_data.class_name)
        db.add(class_name_obj)
        await db.flush()

    # Check program type
    result = await db.execute(select(ProgramType).where(ProgramType.type_name == class_data.program_type))
    program_type_obj = result.scalars().first()
    if not program_type_obj:
        program_type_obj = ProgramType(type_name=class_data.program_type)
        db.add(program_type_obj)
        await db.flush()

    # Create class
    new_class = Class(
        class_name_id=class_name_obj.id,
        program_type_id=program_type_obj.id,
        department=class_data.department,
        section=class_data.section,
        regular_or_self=class_data.regular_or_self
    )
    db.add(new_class)
    await db.commit()

    return {
        "message": "Class created successfully",
        "class_id": str(new_class.id),
    }



@router.post("/class/create-via-json")
async def bulk_create_classes(classes: List[ClassCreate], db: AsyncSession = Depends(get_db)):
    created_classes = []
    skipped = []

    for cls in classes:
        # Check duplicate
        result = await db.execute(
            select(Class)
            .join(ClassName)
            .join(ProgramType)
            .where(
                ClassName.name == cls.class_name,
                ProgramType.type_name == cls.program_type,
                Class.department == cls.department,
                Class.section == cls.section,
                Class.regular_or_self == cls.regular_or_self
            )
        )
        existing_class = result.scalars().first()

        if existing_class:
            skipped.append({
                "class_name": cls.class_name,
                "program_type": cls.program_type,
                "reason": "Duplicate class"
            })
            continue

        # ClassName
        result = await db.execute(select(ClassName).where(ClassName.name == cls.class_name))
        class_name_obj = result.scalars().first()
        if not class_name_obj:
            class_name_obj = ClassName(name=cls.class_name)
            db.add(class_name_obj)
            await db.flush()

        # ProgramType
        result = await db.execute(select(ProgramType).where(ProgramType.type_name == cls.program_type))
        program_type_obj = result.scalars().first()
        if not program_type_obj:
            program_type_obj = ProgramType(type_name=cls.program_type)
            db.add(program_type_obj)
            await db.flush()

        # Create
        new_class = Class(
            class_name_id=class_name_obj.id,
            program_type_id=program_type_obj.id,
            department=cls.department,
            section=cls.section,
            regular_or_self=cls.regular_or_self
        )
        db.add(new_class)
        created_classes.append(new_class)

    await db.commit()

    return {
        "message": f"{len(created_classes)} classes created successfully",
        "created_class_ids": [str(c.id) for c in created_classes],
        "skipped": skipped
    }


@router.delete("/delete-class/{class_id}",tags=["Admin Student Deletion"])
async def delete_class(
    class_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Class).where(Class.id == class_id)
    )
    class_obj = result.scalars().first()

    if not class_obj:
        raise HTTPException(
            status_code=404,
            detail="Class not found"
        )

    await db.delete(class_obj)
    await db.commit()

    return {
        "message": "Class deleted successfully",
        "class_id": str(class_id)
    }