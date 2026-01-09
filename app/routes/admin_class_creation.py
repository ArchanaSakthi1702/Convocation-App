from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import List
from uuid import UUID

from app.database import get_db
from app.models import Class, ClassName, ProgramType,Student
from app.auth.dependencies import is_admin
from app.schemas.class_schemas import ClassCreate,ClassUpdate

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


@router.delete("/delete-class/{class_id}")
async def delete_class(
    class_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """Used Only for Development Purpose"""
    result = await db.execute(
        select(Class).where(Class.id == class_id)
        .options(selectinload(Class.students))
    )
    class_obj = result.scalars().first()

    if not class_obj:
        raise HTTPException(
            status_code=404,
            detail="Class not found"
        )
    
    if class_obj.students:
        stud_len=len(class_obj.students)
        for stud in class_obj.students:
            await db.delete(stud)

    await db.delete(class_obj)
    await db.commit()

    return {
        "message": "Class deleted successfully",
        "class_id": str(class_id),
        "No.of Students Deleted":stud_len
    }


@router.patch("/class/{class_id}")
async def update_class(
    class_id: UUID,
    data: ClassUpdate,
    db: AsyncSession = Depends(get_db)
):
    # Fetch class
    result = await db.execute(
        select(Class).where(Class.id == class_id)
    )
    db_class = result.scalar_one_or_none()

    if not db_class:
        raise HTTPException(status_code=404, detail="Class not found")

    try:
        # Update class name
        if data.class_name:
            result = await db.execute(
                select(ClassName).where(ClassName.name == data.class_name)
            )
            class_name_obj = result.scalar_one_or_none()

            if not class_name_obj:
                class_name_obj = ClassName(name=data.class_name)
                db.add(class_name_obj)
                await db.flush()

            db_class.class_name_id = class_name_obj.id

        # Update program type
        if data.program_type:
            result = await db.execute(
                select(ProgramType).where(
                    ProgramType.type_name == data.program_type
                )
            )
            program_type_obj = result.scalar_one_or_none()

            if not program_type_obj:
                program_type_obj = ProgramType(type_name=data.program_type)
                db.add(program_type_obj)
                await db.flush()

            db_class.program_type_id = program_type_obj.id

        # Simple fields
        if data.department is not None:
            db_class.department = data.department

        if data.section is not None:
            db_class.section = data.section

        if data.regular_or_self is not None:
            db_class.regular_or_self = data.regular_or_self

        await db.commit()

    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Duplicate or invalid class data"
        )

    return {
        "message": "Class updated successfully",
        "class_id": str(db_class.id)
    }