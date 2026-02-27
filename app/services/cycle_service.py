from datetime import datetime, timedelta

def predict_next_period(last_date: str):
    date_obj = datetime.strptime(last_date, "%d-%m-%Y")
    next_date = date_obj + timedelta(days=28)
    return next_date.strftime("%d-%m-%Y")