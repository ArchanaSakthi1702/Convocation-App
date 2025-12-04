from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ProgramType,Class,ClassName
from app.auth.dependencies import is_admin  # your admin dependency

router = APIRouter(
    prefix="/admin/program-types",
    tags=["Admin Program Types Listing"],
    dependencies=[Depends(is_admin)]
)


@router.get("/list-program-types")
async def list_program_types(db: AsyncSession = Depends(get_db)):
    """
    List all Program Types (UG/PG/etc.)
    Accessible only by admin.
    """

    result = await db.execute(select(ProgramType))
    program_types = result.scalars().all()

    return {
        "count": len(program_types),
        "program_types": [
            {
                "id":  str(pt.id),
                "type_name": pt.type_name
            }
            for pt in program_types
        ]
    }




@router.get("/get-classes-by-program-type-name/{program_type_name}")
async def get_classes_by_program_type_name(
    program_type_name: str,
    db: AsyncSession = Depends(get_db)
):
    # Find ProgramType by name
    result = await db.execute(
        select(ProgramType).where(ProgramType.type_name == program_type_name)
    )
    program_type = result.scalars().first()

    if not program_type:
        raise HTTPException(
            status_code=404,
            detail=f"Program type '{program_type_name}' not found"
        )

    # Now fetch classes
    result = await db.execute(
        select(Class)
        .options(
            selectinload(Class.class_name_ref),
            selectinload(Class.program_type_ref),
        )
        .where(Class.program_type_id == program_type.id)
    )

    classes = result.scalars().all()

    return {
        "program_type": program_type.type_name,
        "count": len(classes),
        "classes": [
            {
                "id":str(c.id),
                "class_name": c.class_name_ref.name,
                "program_type": c.program_type_ref.type_name,
                "department": c.department,
                "section": c.section,
                "regular_or_self": c.regular_or_self,
            }
            for c in classes
        ],
    }


@router.get("/get-classes-by-program-type-id/{program_type_id}")
async def get_classes_by_program_type_id(
    program_type_id: str,
    db: AsyncSession = Depends(get_db)
):
    # Validate UUID
    try:
        program_type_uuid = UUID(program_type_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid program_type_id")

    # Check program type exists
    result = await db.execute(
        select(ProgramType).where(ProgramType.id == program_type_uuid)
    )
    program_type = result.scalars().first()

    if not program_type:
        raise HTTPException(status_code=404, detail="Program type not found")

    # Fetch all classes under this program type
    result = await db.execute(
        select(Class)
        .options(
            selectinload(Class.class_name_ref),
            selectinload(Class.program_type_ref),
        )
        .where(Class.program_type_id == program_type_uuid)
    )

    classes = result.scalars().all()

    return {
        "program_type": program_type.type_name,
        "count": len(classes),
        "classes": [
            {
                "id": str(c.id),
                "class_name": c.class_name_ref.name,
                "program_type": c.program_type_ref.type_name,
                "department": c.department,
                "section": c.section,
                "regular_or_self": c.regular_or_self,
            }
            for c in classes
        ],
    }
