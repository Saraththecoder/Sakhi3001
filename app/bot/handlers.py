from telegram import Update
from telegram.ext import ContextTypes
from app.services.user_service import get_or_create_user, update_user
from app.services.cycle_service import predict_next_period
from app.services.tip_service import get_daily_tip
from app.analytics import track_event
from app.bot.keyboards import language_keyboard

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await get_or_create_user(user_id)
    await track_event(user_id, "start")
    await update.message.reply_text(
        "Welcome to Sakhi 🌸\nSelect language:",
        reply_markup=language_keyboard()
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    user = await get_or_create_user(user_id)

    if text in ["English", "Telugu"]:
        await update_user(user_id, {"language": text})
        await track_event(user_id, "language_selected")
        await update.message.reply_text("Enter last period date (DD-MM-YYYY):")
        return

    if user["language"] and not user["last_period_date"]:
        await update_user(user_id, {"last_period_date": text})
        next_date = predict_next_period(text)
        await track_event(user_id, "prediction_generated")
        await update.message.reply_text(
            f"Your next expected period: {next_date}"
        )
        await update.message.reply_text(get_daily_tip())
        return
