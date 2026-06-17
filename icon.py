import datetime as dt
import io
from pathlib import Path

from PIL import Image

from config import Settings


def select_icon_path(now: dt.datetime, settings: Settings, base_dir: Path) -> Path:
    icon_path = (
        settings.night_icon_path
        if now.hour >= 21 or now.hour < 6
        else settings.normal_icon_path
    )
    return base_dir / icon_path


def rotate_icon(icon_path: Path, now: dt.datetime) -> bytes:
    if not icon_path.exists():
        raise FileNotFoundError(f"Icon file not found: {icon_path}")

    hour_position = (now.hour % 12) + (now.minute / 60)
    clockwise_degrees = hour_position * 30

    with Image.open(icon_path) as image:
        rotated = image.convert("RGBA").rotate(
            -clockwise_degrees,
            resample=Image.Resampling.BICUBIC,
            expand=False,
        )

        output = io.BytesIO()
        rotated.save(output, format="PNG")
        return output.getvalue()
