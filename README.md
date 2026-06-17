# Bluesky Clock Icon
Codexの練習がてら作成。

Azure Functions の Timer Trigger で 1 時間ごとに Bluesky のアイコンを更新します。

- `img/normal.png`: 日本時間 6:00 から 20:59 まで使用
- `img/night.png`: 日本時間 21:00 から 5:59 まで使用
- 画像は 12 時向きとして扱い、日本時間の短針位置へ時計回りに回転

## 必要な設定

Azure Functions のアプリ設定に以下を追加してください。

| Name | Value |
| --- | --- |
| `BSKY_HANDLE` | Bluesky のハンドル |
| `BSKY_APP_PASS` | Bluesky の App Password |
| `BLUESKY_SESSION_KEYVAULT_NAME` | Bluesky セッション保存用 Key Vault secret 名 |
| `KEY_VAULT_URL` | Azure Key Vault URL |
| `NORMAL_ICON_PATH` | 例: `img/normal.png` |
| `NIGHT_ICON_PATH` | 例: `img/night.png` |

`normal.png` と `night.png` は `img` フォルダーに配置します。時計の時刻判定と回転は常に日本時間で行います。

Bluesky のセッションは Azure Key Vault に保存し、次回以降はそのセッションを使ってログインします。セッションが無効な場合は `BSKY_HANDLE` / `BSKY_APP_PASS` でログインし直します。

## ファイル構成

| File | Role |
| --- | --- |
| `function_app.py` | Azure Functions の Timer Trigger |
| `config.py` | 環境変数から設定を読み込む |
| `icon.py` | アイコン画像の選択と回転 |
| `bluesky.py` | Bluesky 認証、セッション保存、アイコン更新 |

## ローカル実行

`local.settings.json.example` を参考に `local.settings.json` を作成し、値を設定します。

```bash
export UV_CACHE_DIR=.uv-cache
uv sync
uv export --format requirements.txt --no-hashes --output-file requirements.txt
uv pip install -r requirements.txt --target .python_packages/lib/site-packages
func start --port 7080
```

Azure Functions の remote build は `requirements.txt` を使うため、依存を変更したら `uv export --format requirements.txt --no-hashes --output-file requirements.txt` で更新します。

`AzureWebJobsStorage` が `UseDevelopmentStorage=true` の場合は、別途 Azurite を起動してください。Azurite を使わない場合は、`local.settings.json` の `AzureWebJobsStorage` に実際の Azure Storage 接続文字列を設定します。
