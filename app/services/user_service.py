from app.database import users_collection

async def get_or_create_user(user_id: int):
    user = await users_collection.find_one({"telegram_id": user_id})
    if not user:
        user = {
            "telegram_id": user_id,
            "language": None,
            "last_period_date": None,
            "cycle_lengths": []
        }
        await users_collection.insert_one(user)
    return user

async def update_user(user_id: int, data: dict):
    await users_collection.update_one(
        {"telegram_id": user_id},
        {"$set": data}
    )
