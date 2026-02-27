from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.config import settings
from app.bot.handlers import start, handle_message
from app.logging_config import setup_logging

setup_logging()

app = FastAPI()

telegram_app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"status": "ok"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
