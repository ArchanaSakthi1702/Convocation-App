from fastapi import HTTPException
from datetime import datetime, time
import pytz

# -------------------------
# Helper: Check IST Time Limit (Before 10:00 AM)
# -------------------------
def check_attendance_time_limit():
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist).time()

    start_time = time(9, 00, 0)   
    end_time = time(10, 30, 0) 

    if not (start_time <= now_ist <= end_time):
        raise HTTPException(
            status_code=403,
            detail="Attendance marking is allowed only from 12:05 PM to 1:15 PM IST"
        )
