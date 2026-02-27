from fastapi import FastAPI, Request
import httpx
import os
from app.config import settings
from app.logging_config import setup_logging
from app.services.user_service import get_or_create_user, update_user
from app.services.cycle_service import predict_next_period
from app.services.tip_service import get_daily_tip
from app.analytics import track_event

setup_logging()

app = FastAPI()

TELEGRAM_API = f"https://api.telegram.org/bot{settings.TELEGRAM_TOKEN}"

async def send_message(chat_id: int, text: str, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup

    async with httpx.AsyncClient() as client:
        await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    if "message" not in data:
        return {"status": "ignored"}

    message = data["message"]
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    user = await get_or_create_user(chat_id)

    # START command
    if text == "/start":
        await track_event(chat_id, "start")
        keyboard = {
            "keyboard": [["English", "Telugu"]],
            "resize_keyboard": True
        }
        await send_message(chat_id, "Welcome to Sakhi 🌸\nSelect language:", keyboard)
        return {"status": "ok"}

    # Language selection
    if text in ["English", "Telugu"]:
        await update_user(chat_id, {"language": text})
        await track_event(chat_id, "language_selected")
        await send_message(chat_id, "Enter last period date (DD-MM-YYYY):")
        return {"status": "ok"}

    # Period prediction
    if user.get("language") and not user.get("last_period_date"):
        await update_user(chat_id, {"last_period_date": text})
        next_date = predict_next_period(text)
        await track_event(chat_id, "prediction_generated")

        await send_message(chat_id, f"Your next expected period: {next_date}")
        await send_message(chat_id, get_daily_tip())
        return {"status": "ok"}

    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

from app.database import analytics_collection, users_collection

@app.get("/admin/stats")
async def get_stats():
    total_users = await users_collection.count_documents({})
    total_events = await analytics_collection.count_documents({})
    predictions = await analytics_collection.count_documents({"event": "prediction_generated"})
    
    return {
        "total_users": total_users,
        "total_events": total_events,
        "predictions_generated": predictions
    }
