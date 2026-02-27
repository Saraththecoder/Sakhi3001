from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(settings.MONGO_URI)
db = client["sakhi_db"]

users_collection = db["users"]
analytics_collection = db["analytics"]