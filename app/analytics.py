from app.database import analytics_collection
from datetime import datetime

async def track_event(user_id: int, event_type: str):
    await analytics_collection.insert_one({
        "user_id": user_id,
        "event": event_type,
        "timestamp": datetime.utcnow()
    })