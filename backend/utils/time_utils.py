from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import current_app


def get_app_timezone() -> ZoneInfo:
    timezone_name = current_app.config["APP_TIMEZONE"]

    try:
        return ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        return timezone.utc


def local_now() -> datetime:
    return datetime.now(get_app_timezone())


def current_date_string() -> str:
    return local_now().strftime("%Y-%m-%d")


def current_time_string() -> str:
    return local_now().strftime("%H:%M:%S")


def current_timestamp_string() -> str:
    return local_now().strftime("%Y-%m-%d %H:%M:%S")
