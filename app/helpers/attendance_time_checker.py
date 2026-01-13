from fastapi import HTTPException
from datetime import datetime, time
import pytz

# -------------------------
# Helper: Check IST Time Limit (Before 10:00 AM)
# -------------------------
def check_attendance_time_limit():
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist).time()

    start_time = time(12, 5, 0)   # 12:05 PM IST
    end_time = time(13, 15, 0)    # 1:15 PM IST

    if not (start_time <= now_ist <= end_time):
        raise HTTPException(
            status_code=403,
            detail="Attendance marking is allowed only from 12:05 PM to 1:15 PM IST"
        )