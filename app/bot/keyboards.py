from telegram import ReplyKeyboardMarkup

def language_keyboard():
    return ReplyKeyboardMarkup(
        [["English", "Telugu"]],
        resize_keyboard=True
    )
