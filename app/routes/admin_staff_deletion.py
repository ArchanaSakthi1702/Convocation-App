from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete,select
from sqlalchemy.orm import selectinload
from uuid import UUID


from app.database import get_db
from app.models import User,staff_classes
from app.auth.dependencies import is_admin

router = APIRouter(
    prefix="/admin",
    tags=["Admin Staff deletion"],
    dependencies=[Depends(is_admin)]
)


@router.delete("/delete-all-staffs", response_model=dict)
async def delete_all_staffs(db: AsyncSession = Depends(get_db)):
    """
    Delete ALL staff records and clean up staff_classes table.
    Admin-only operation.
    """
    try:
        # Delete all entries from staff_classes table first
        await db.execute(delete(staff_classes))
        # Then delete all users
        await db.execute(delete(User))
        await db.commit()
        return {"message": "All staff records and their class assignments have been deleted successfully."}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to delete all staff: {str(e)}")

@router.delete("/delete-staff-by-id/{staff_id}", response_model=dict)
async def delete_staff(staff_id: str, db: AsyncSession = Depends(get_db)):
    try:
        staff_uuid = UUID(staff_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid staff ID format")

    # Fetch the staff to ensure it exists
    result = await db.execute(select(User).where(User.id == staff_uuid))
    staff = result.scalars().first()

    if not staff:
        raise HTTPException(status_code=404, detail="Staff not found")

    # Delete the staff
    await db.delete(staff)
    await db.commit()

    return {"message": f"Staff {staff.staff_name or staff_id} deleted successfully"}


@router.delete("/delete-staff/{roll_no}")
async def delete_staff_by_roll_no(
    roll_no: str,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(User).where(User.staff_roll_number == roll_no).options(selectinload(User.assigned_classes))
    )
    teacher = result.scalar_one_or_none()

    if not teacher:
        raise HTTPException(
            status_code=404,
            detail=f"Staff not found for roll no {roll_no}"
        )

    # Clear class assignments (important for M2M)
    teacher.assigned_classes.clear()

    await db.delete(teacher)
    await db.commit()

    return {
        "message": "Staff deleted successfully",
        "staff_roll_number": roll_no,
        "staff_id": str(teacher.id)
    }
