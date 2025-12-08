from pydantic import BaseModel, Field

# Response schema
class MarkAttendanceResponse(BaseModel):
    message: str = Field(..., example="Attendance updated successfully")
    student_id: str = Field(..., description="UUID of the student")
    student_name: str = Field(..., description="Name of the student")
    present: bool = Field(..., description="Marked attendance status")
