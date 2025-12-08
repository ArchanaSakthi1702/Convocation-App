from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List,Optional
import uuid

from app.models import Class,ClassName

async def get_classes_from_request(
    db: AsyncSession, ids: Optional[List[str]] = None, names: Optional[List[str]] = None
) -> List[Class]:
    classes = []
    count:int=0

    invalid_ids = []

    # If UUIDs provided
    if ids:
        for class_id in ids:
            count+=1
            try:
                class_bytes = uuid.UUID(class_id)
                print(f"{count} Id:{class_bytes}")
            except (ValueError, TypeError):
                invalid_ids.append(class_id)
                continue

            result = await db.execute(select(Class).where(Class.id == class_bytes))
            cls = result.scalars().first()
            if not cls:
                raise HTTPException(status_code=404, detail=f"Class with id {class_id} not found")
            classes.append(cls)

        if invalid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"The following class IDs are not valid UUIDs: {invalid_ids}"
            )

    # If class names provided
    if names:
        for class_name in names:
            result = await db.execute(
                select(Class).join(Class.class_name_ref).where(ClassName.name == class_name)
            )
            matched_classes = result.scalars().all()
            if len(matched_classes) > 1:
                raise HTTPException(
                    status_code=400,
                    detail=f"Duplicate class names found for '{class_name}' (count: {len(matched_classes)})"
                )
            if not matched_classes:
                raise HTTPException(
                    status_code=404,
                    detail=f"No class found with name '{class_name}'"
                )
            classes.append(matched_classes[0])

    return classes