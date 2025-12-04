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

    # If UUIDs provided
    if ids:
        for class_id in ids:
            class_bytes = uuid.UUID(class_id)
            result = await db.execute(select(Class).where(Class.id == class_bytes))
            cls = result.scalars().first()
            if not cls:
                raise HTTPException(status_code=404, detail=f"Class with id {class_id} not found")
            classes.append(cls)

    # If class names provided
    if names:
        for class_name in names:
            result = await db.execute(select(Class).join(Class.class_name_ref).where(ClassName.name == class_name))
            matched_classes = result.scalars().all()
            if len(matched_classes) > 1:
                raise HTTPException(status_code=400, detail=f"Duplicate class names found for '{class_name}' Count is '{len(matched_classes)}")
            if not matched_classes:
                raise HTTPException(status_code=404, detail=f"No class found with name '{class_name}'")
            classes.append(matched_classes[0])

    return classes
