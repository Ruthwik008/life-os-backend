from datetime import datetime, timedelta
import pytz



WEEKDAY_MAP = {
    "MON": 0,
    "TUE": 1,
    "WED": 2,
    "THU": 3,
    "FRI": 4,
    "SAT": 5,
    "SUN": 6
}

def calculate_next_send_time(reminder):

    timezone = pytz.timezone(reminder["timezone"])
    now = datetime.now(timezone)

    reminder_time = reminder["reminder_time"]

    if reminder_time:
        reminder_time = datetime.strptime(str(reminder_time), "%H:%M:%S").time()

    reminder_type = reminder["reminder_type"]

    # ONCE reminder
    if reminder_type == "ONCE":

        reminder_date = reminder["reminder_date"]

        dt = datetime.combine(reminder_date, reminder_time)

        return timezone.localize(dt)

    # DAILY reminder
    if reminder_type == "DAILY":

        next_time = datetime.combine(now.date(), reminder_time)
        next_time = timezone.localize(next_time)

        if next_time <= now:
            next_time = next_time + timedelta(days=1)

        return next_time

    # WEEKLY reminder
    if reminder_type == "WEEKLY":

        days = reminder["reminder_days"].split(",")

        today = now.weekday()

        candidate_days = []

        for day in days:
            candidate_days.append(WEEKDAY_MAP[day])

        candidate_days.sort()

        for day in candidate_days:

            diff = day - today

            if diff < 0:
                diff += 7

            next_date = now.date() + timedelta(days=diff)

            next_dt = datetime.combine(next_date, reminder_time)
            next_dt = timezone.localize(next_dt)

            if next_dt > now:
                return next_dt

        # fallback next week
        next_date = now.date() + timedelta(days=7)

        return timezone.localize(
            datetime.combine(next_date, reminder_time)
        )

    return None

