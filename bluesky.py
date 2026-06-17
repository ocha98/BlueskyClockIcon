import logging
from typing import Any

from atproto import Client, SessionEvent
from atproto.exceptions import BadRequestError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

from config import Settings


def update_bluesky_avatar(icon_png: bytes, settings: Settings) -> None:
    client = init_bluesky_client(settings)
    did = client.me.did
    avatar_blob = to_plain_value(client.upload_blob(icon_png).blob)

    profile, profile_cid = load_profile_record(client, did)
    profile["avatar"] = avatar_blob
    profile.setdefault("$type", "app.bsky.actor.profile")

    record_data = {
        "repo": did,
        "collection": "app.bsky.actor.profile",
        "rkey": "self",
        "record": profile,
    }
    if profile_cid:
        record_data["swap_record"] = profile_cid

    client.com.atproto.repo.put_record(record_data)


def init_bluesky_client(settings: Settings) -> Client:
    logging.info("bluesky clientの初期化を開始します")
    client = Client()

    @client.on_session_change
    def on_session_change(event: SessionEvent, session: Any) -> None:
        logging.info("bluesky session change eventを受信")
        if event in (SessionEvent.CREATE, SessionEvent.REFRESH):
            try:
                logging.info("Bluesky sessionを保存します。 event=%s", event)
                save_bluesky_session(export_session(session), settings)
                logging.info("Bluesky sessionの保存に成功しました: event=%s", event)
            except Exception:
                logging.exception("Bluesky sessionの保存に失敗しました event = %s", event)
                raise

    bluesky_session = load_bluesky_session(settings)

    if bluesky_session:
        try:
            logging.info("既存の session を利用してログインします")
            client.login(session_string=bluesky_session)
            verify_bluesky_login(client, login_method="session")
            return client
        except Exception:
            logging.warning("既存セッションが使えなかったため app password でログインします")

    if not settings.bsky_handle or not settings.bsky_app_pass:
        raise RuntimeError(
            "BLUESKY_SESSION が無効、かつ BSKY_HANDLE / BSKY_APP_PASS が設定されていません。"
        )

    logging.info("Bluesky に app password でログインします")
    client.login(settings.bsky_handle, settings.bsky_app_pass)
    verify_bluesky_login(client, login_method="app pass")
    save_bluesky_session(client.export_session_string(), settings)

    return client


def get_secret_client(settings: Settings) -> SecretClient:
    if not settings.key_vault_url:
        raise RuntimeError("KEY_VAULT_URL must be set.")

    credential = DefaultAzureCredential()
    return SecretClient(vault_url=settings.key_vault_url, credential=credential)


def load_bluesky_session(settings: Settings) -> str | None:
    if not settings.bluesky_session_keyvault_name:
        logging.warning("BLUESKY_SESSION_KEYVAULT_NAME is not set.")
        return None

    try:
        secret_client = get_secret_client(settings)
        return secret_client.get_secret(settings.bluesky_session_keyvault_name).value
    except Exception:
        logging.exception("Key vaultからBLUESKY_SESSIONを取得できませんでした。")
        return None


def save_bluesky_session(session: str, settings: Settings) -> None:
    if not settings.bluesky_session_keyvault_name:
        raise RuntimeError("BLUESKY_SESSION_KEYVAULT_NAME must be set.")

    secret_client = get_secret_client(settings)
    secret_client.set_secret(settings.bluesky_session_keyvault_name, session)


def verify_bluesky_login(client: Client, login_method: str) -> None:
    logging.info("Bluesky ログイン確認を開始します: method=%s", login_method)

    try:
        me = client.me
        logging.info(
            "Bluesky ログイン確認に成功しました: method=%s handle=%s did=%s",
            login_method,
            getattr(me, "handle", None),
            getattr(me, "did", None),
        )
    except Exception:
        logging.exception("Bluesky ログイン確認に失敗しました: method=%s", login_method)
        raise


def export_session(session: Any) -> str:
    if hasattr(session, "export"):
        return session.export()
    return str(session)


def load_profile_record(client: Client, did: str) -> tuple[dict[str, Any], str | None]:
    try:
        response = client.com.atproto.repo.get_record(
            {
                "repo": did,
                "collection": "app.bsky.actor.profile",
                "rkey": "self",
            }
        )
    except BadRequestError as e:
        if is_record_not_found(e):
            return {"$type": "app.bsky.actor.profile"}, None
        raise

    return to_dict(response.value), response.cid


def is_record_not_found(error: BadRequestError) -> bool:
    content = getattr(getattr(error, "response", None), "content", None)
    if isinstance(content, dict):
        return content.get("error") == "RecordNotFound"

    return getattr(content, "error", None) == "RecordNotFound"


def to_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value

    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True, exclude_none=True)

    return {"$type": "app.bsky.actor.profile"}


def to_plain_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(by_alias=True, exclude_none=True)

    return value
