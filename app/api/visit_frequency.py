from fastapi import APIRouter, Depends, HTTPException
from app.db import con, get_site_by_id
from app.auth_utils import verify_token
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login")

def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload

@router.get("/sites/{site_id}/visit-frequency")
async def get_site_visit_frequency(site_id: str, current_user: dict = Depends(get_current_user)):
    site = get_site_by_id(site_id)
    if not site or site.owner_user_id != current_user["sub"]:
        raise HTTPException(status_code=404, detail="Site not found")

    # Get the last 30 days of pageview events
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=30)
    rows = con.execute('''
        SELECT ts FROM raw_events WHERE site_id = ? AND event_type = 'pageview' AND DATE(ts) BETWEEN ? AND ?
        ORDER BY ts ASC
    ''', [site_id, str(start_date), str(end_date)]).fetchall()
    if not rows:
        return {"buckets": [], "granularity": "none", "message": "No visits in the last 30 days"}

    timestamps = [row[0] for row in rows]
    total_views = len(timestamps)
    days = (end_date - start_date).days + 1
    avg_per_day = total_views / days

    # Decide granularity
    if avg_per_day < 1.5:
        # Very infrequent: bucket by week
        granularity = "weekly"
        buckets = {}
        for ts in timestamps:
            dt = datetime.fromisoformat(str(ts))
            week = dt.strftime("%Y-W%U")
            buckets[week] = buckets.get(week, 0) + 1
        bucket_list = [{"period": k, "views": v} for k, v in sorted(buckets.items())]
    elif avg_per_day < 10:
        # Moderate: bucket by day
        granularity = "daily"
        buckets = {}
        for ts in timestamps:
            dt = datetime.fromisoformat(str(ts))
            day = dt.strftime("%Y-%m-%d")
            buckets[day] = buckets.get(day, 0) + 1
        bucket_list = [{"period": k, "views": v} for k, v in sorted(buckets.items())]
    else:
        # Frequent: bucket by hour
        granularity = "hourly"
        buckets = {}
        for ts in timestamps:
            dt = datetime.fromisoformat(str(ts))
            hour = dt.strftime("%Y-%m-%d %H:00")
            buckets[hour] = buckets.get(hour, 0) + 1
        bucket_list = [{"period": k, "views": v} for k, v in sorted(buckets.items())]

    return {"buckets": bucket_list, "granularity": granularity, "total_views": total_views}
