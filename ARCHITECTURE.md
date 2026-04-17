# Arsitektur Teknis — sso-auth 0.3.0

## Ringkasan

`sso-auth` adalah Python SDK + CLI untuk autentikasi SSO Keycloak (`sso.bps.go.id`).
Mulai versi 0.3.0, paket memiliki dua layer utama:

1. **Core SDK** (`SsoClient`) — autentikasi, token refresh, persistensi aman
2. **Browser module** (`sso_auth.browser`, optional) — headless Playwright automation dengan smart hybrid login

## Struktur Utama

```
src/sso_auth/
├── client.py            # Facade utama SsoClient
├── models.py            # Pydantic models (TokenBundle, UserInfo, AuthResult)
├── exceptions.py        # Error hierarchy
├── config.py            # Settings (env driven)
├── logging.py           # Logging helpers
├── cli.py               # Typer CLI (auth + browser subcommands)
├── auth/
│   ├── code_flow.py     # Authorization code flow
│   ├── session_flow.py  # Session-cookie fallback
│   └── refresh.py       # Refresh token flow
├── storage/
│   ├── keyring_backend.py
│   ├── state.py
│   └── cookies.py
├── browser/             # Optional — requires sso-auth[browser]
│   ├── session.py       # BrowserSession context manager
│   ├── login.py         # smart_login + _auto_ui_login
│   ├── stealth.py       # JS init patches (fingerprint)
│   ├── human.py         # HumanBehavior timing helpers
│   ├── storage.py       # storage_state.json load/save
│   └── scraping.py      # download_to, extract_table, wait_any
└── core.py              # Backward-compatible wrappers (deprecated)
```

## Alur Login (Core SDK)

1. `SsoClient.login()` mencoba `auth.code_flow.try_auth_code_flow()`
2. Jika gagal, fallback ke `auth.session_flow.try_session_based()`
3. Hasil dipetakan ke `AuthResult`
4. Token/cookies/state disimpan via storage layer

## Alur Login (Browser Module)

```
BrowserSession.launch(client, app_url)
        │
        ▼
  Load storage_state.json jika ada
        │
        ▼
  page.goto(app_url)
        │
        ▼
  URL mengandung sso.bps.go.id?
   Tidak ──► Sesi masih valid, lanjut
   Ya   ──► Auto-fill form Keycloak (username/password dari SsoClient)
             └─► Submit ──► Tunggu redirect balik ke app
                              └─► Save storage_state.json
```

## Persistensi Data

| Data | Lokasi | Sensitivitas |
|------|--------|--------------|
| Password | OS keyring (`sso.bps.go.id`) | Secret |
| Refresh token | OS keyring (`sso.bps.go.id`) | Secret |
| Token metadata + user_info | `~/.config/sso-auth/state.json` | Non-secret |
| HTTP cookies | `~/.config/sso-auth/cookies.pickle` | Semi-secret |
| Browser session | `~/.config/sso-auth/storage_state.json` | Semi-secret |

## Kontrak API (Core)

```python
from sso_auth import SsoClient

client = SsoClient.from_keyring("username")
client.ensure_valid()     # login/refresh otomatis
session = client.session  # reusable requests.Session untuk app adapter
```

## Kontrak API (Browser)

```python
from sso_auth import SsoClient
from sso_auth.browser import BrowserSession

client = SsoClient.from_keyring("username")
with BrowserSession.launch(client, app_url="https://app.bps.go.id/") as b:
    b.download_to("/tmp/out.xlsx", trigger_selector="#btn-export")
    rows = b.page.evaluate("() => ...")
```

## CLI Commands

**Auth:**
- `sso-auth login <username>`
- `sso-auth logout <username>`
- `sso-auth whoami <username>`
- `sso-auth token <username>`
- `sso-auth refresh <username>`
- `sso-auth status <username>`

**Browser (requires `[browser]` extras):**
- `sso-auth browser open <app-url> --username <u> [--headful]`
- `sso-auth browser clear <username>`

## Integrasi Lanjutan

Arsitektur ini disiapkan untuk fase berikutnya:

- `sso_auth.vpn` — handoff SAML FortiClient
- `sso_auth.apps.*` — adapter per aplikasi internal (reuse `SsoClient.session`)

## Catatan Keamanan

- `sso_tokens.json` tidak lagi disimpan default
- File token lama harus dianggap compromise dan wajib rotasi sesi/password
- `storage_state.json` mengandung session cookies aktif — jangan commit ke repo
