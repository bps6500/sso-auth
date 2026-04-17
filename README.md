# sso-auth

Python SDK + CLI untuk autentikasi SSO Keycloak (`sso.bps.go.id`) yang siap diintegrasikan ke aplikasi automation/monitoring internal.

## Install

```bash
pip install -e .
```

Untuk development:

```bash
pip install -e ".[dev]"
```

## CLI

```bash
sso-auth login <username>
sso-auth status <username>
sso-auth whoami <username>
sso-auth token <username>
sso-auth refresh <username>
sso-auth logout <username>
```

## Penggunaan SDK

```python
from sso_auth import SsoClient

client = SsoClient.from_keyring("your_username")
client.ensure_valid()

token = client.access_token
session = client.session
resp = session.get("https://internal-app.example/api")
```

## Integrasi ke aplikasi lain

- Gunakan `SsoClient` sebagai dependency tunggal untuk auth state
- Pakai `client.ensure_valid()` sebelum request agar auto-refresh
- Reuse `client.session` untuk HTTP client aplikasi adapter Anda
- Gunakan `client.on_token_refresh(callback)` jika perlu sinkronisasi token/cookie

## Browser Automation (opsional)

Install extras dan browser binary terlebih dahulu:

```bash
pip install -e ".[browser]"
playwright install chromium
```

Contoh pemakaian:

```python
from sso_auth import SsoClient
from sso_auth.browser import BrowserSession

client = SsoClient.from_keyring("username")

with BrowserSession.launch(client, app_url="https://app.bps.go.id/") as b:
    b.page.goto("https://app.bps.go.id/laporan")
    b.download_to("/tmp/laporan.xlsx", trigger_selector="#btn-export")
    rows = b.page.evaluate("() => [...]")  # atau gunakan extract_table
```

- Login dilakukan otomatis via halaman SSO kalau sesi belum aktif
- Sesi tersimpan di `~/.config/sso-auth/storage_state.json` dan di-reuse run berikutnya
- Browser berjalan headless secara default; gunakan `headless=False` untuk debug

CLI browser:

```bash
sso-auth browser open <app-url> --username <u> [--headful]
sso-auth browser clear <username>
```

## Keamanan

- Password + refresh token disimpan di OS keyring
- Metadata non-rahasia disimpan di `~/.config/sso-auth/state.json`
- Jangan commit token file ke repository

