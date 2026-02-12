from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List,Optional
from uuid import UUID

from app.models import Class,ClassName


async def get_classes_from_request(
    db: AsyncSession,
    ids: Optional[List[UUID]] = None,
    names: Optional[List[str]] = None
) -> List[Class]:

    classes: List[Class] = []

    # -----------------------
    # If UUIDs provided
    # -----------------------
    if ids:
        result = await db.execute(
            select(Class).where(Class.id.in_(ids)).options(selectinload(Class.class_name_ref))
        )

        found_classes = result.scalars().all()

        found_ids = {cls.id for cls in found_classes}
        missing_ids = [str(cid) for cid in ids if cid not in found_ids]

        if missing_ids:
            raise HTTPException(
                status_code=404,
                detail=f"Classes not found for IDs: {missing_ids}"
            )

        classes.extend(found_classes)

    # -----------------------
    # If class names provided
    # -----------------------
    if names:
        for class_name in names:
            result = await db.execute(
                select(Class)
                .join(Class.class_name_ref)
                .where(ClassName.name == class_name)
            )

            matched_classes = result.scalars().all()

            if len(matched_classes) > 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate class names found for '{class_name}'"
                )

            if not matched_classes:
                raise HTTPException(
                    status_code=404,
                    detail=f"No class found with name '{class_name}'"
                )

            classes.append(matched_classes[0])
            print(classes)
    return classes
