import datetime as dt
import logging
from pathlib import Path

import azure.functions as func
from bluesky import update_bluesky_avatar
from config import load_settings
from icon import rotate_icon, select_icon_path
from zoneinfo import ZoneInfo


app = func.FunctionApp()
BASE_DIR = Path(__file__).resolve().parent
JAPAN_TIMEZONE = "Asia/Tokyo"


@app.timer_trigger(
    schedule="0 0 * * * *",
    arg_name="timer",
    run_on_startup=False,
    use_monitor=True,
)
def rotate_bluesky_icon(timer: func.TimerRequest) -> None:
    settings = load_settings()
    now = dt.datetime.now(ZoneInfo(JAPAN_TIMEZONE))

    if timer.past_due:
        logging.warning("Timer trigger is past due.")

    icon_path = select_icon_path(now, settings, BASE_DIR)
    rotated_icon = rotate_icon(icon_path, now)
    update_bluesky_avatar(rotated_icon, settings)

    logging.info(
        "Updated Bluesky icon from %s for %s.",
        icon_path,
        now.isoformat(),
    )
