from datetime import datetime, date, timedelta, timezone
from abs_exception_core.exceptions import BadRequestError


def get_day_range(value: str|datetime):
    if isinstance(value, str):
        # Parse the ISO string to datetime (UTC-aware)
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    elif isinstance(value, datetime):
        dt = value
    else :
        raise BadRequestError("Invalid date value")
        
    start = dt
    end = start + timedelta(days=1)
    return start, end
