import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    bsky_handle: str | None
    bsky_app_pass: str | None
    bluesky_session_keyvault_name: str | None
    key_vault_url: str | None
    normal_icon_path: str
    night_icon_path: str


def load_settings() -> Settings:
    return Settings(
        bsky_handle=os.getenv("BSKY_HANDLE"),
        bsky_app_pass=os.getenv("BSKY_APP_PASS"),
        bluesky_session_keyvault_name=os.getenv("BLUESKY_SESSION_KEYVAULT_NAME"),
        key_vault_url=os.getenv("KEY_VAULT_URL"),
        normal_icon_path=os.getenv("NORMAL_ICON_PATH", "img/normal.png"),
        night_icon_path=os.getenv("NIGHT_ICON_PATH", "img/night.png"),
    )
