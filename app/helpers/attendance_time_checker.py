from fastapi import HTTPException
from datetime import datetime, time
import pytz

# -------------------------
# Helper: Check IST Time Limit (Before 10:00 AM)
# -------------------------
def check_attendance_time_limit():
    ist = pytz.timezone("Asia/Kolkata")
    now_ist = datetime.now(ist).time()

    cutoff = time(10, 0, 0)  # 10:00 AM IST

    if now_ist > cutoff:
        raise HTTPException(
            status_code=403,
            detail="Attendance marking is allowed only until 10:00 AM IST"
        )
