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
    text = message.get("text", "").lower()

    user = await get_or_create_user(chat_id)
    state = user.get("state", "NEW")

    # START
    if text == "/start":
        await update_user(chat_id, {"state": "ASK_LANGUAGE"})
        await send_message(chat_id, "Hi 🌸 I’m Sakhi.\nLet’s get started.\nWhich language do you prefer?\nEnglish or Telugu?")
        return {"status": "ok"}

    # LANGUAGE SELECTION
    if state == "ASK_LANGUAGE":
        if text in ["english", "telugu"]:
            await update_user(chat_id, {
                "language": text,
                "state": "ASK_DATE"
            })
            await send_message(chat_id, "Please tell me your last period date (DD-MM-YYYY).")
        else:
            await send_message(chat_id, "Please choose either English or Telugu.")
        return {"status": "ok"}

    # DATE INPUT
    if state == "ASK_DATE":
        try:
            next_date = predict_next_period(text)
            await update_user(chat_id, {
                "last_period_date": text,
                "state": "ACTIVE"
            })

            await send_message(chat_id, f"Got it 🌸\nYour next expected period is around {next_date}.")
            await send_message(chat_id, "You can now ask me things like:\n- When is my next period?\n- Give me a health tip\n- I have cramps")
        except:
            await send_message(chat_id, "That date format looks incorrect. Please enter like DD-MM-YYYY.")
        return {"status": "ok"}

    # ACTIVE CHAT MODE
    if state == "ACTIVE":

        if "next period" in text:
            next_date = predict_next_period(user["last_period_date"])
            await send_message(chat_id, f"Your next expected period is around {next_date}.")

        elif "tip" in text:
            tip = get_daily_tip()
            await send_message(chat_id, tip)

        elif "cramp" in text:
            await send_message(chat_id, "Mild cramps are common. Try light stretching, warm compress, and hydration.")

        elif "headache" in text:
            await send_message(chat_id, "Hormonal headaches can occur. Rest and hydration usually help.")

        else:
            await send_message(chat_id, "I didn’t fully understand. You can ask about your next period, tips, or symptoms.")

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
