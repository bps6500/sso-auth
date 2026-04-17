# Arsitektur Teknis — sso-auth 0.2.0

## Ringkasan

Mulai versi 0.2.0, `sso-auth` diposisikan sebagai **SDK + CLI** dengan `SsoClient` sebagai facade utama untuk:

- login (auth code flow + fallback session cookies)
- penyimpanan kredensial aman via OS keyring
- persistence state non-rahasia
- token refresh terstruktur
- integrasi reusable ke aplikasi internal lain

## Struktur Utama

```
src/sso_auth/
├── client.py            # Facade utama SsoClient
├── models.py            # Pydantic models (TokenBundle, UserInfo, AuthResult)
├── exceptions.py        # Error hierarchy
├── config.py            # Settings (env driven)
├── logging.py           # Logging helpers
├── cli.py               # Typer CLI
├── auth/
│   ├── code_flow.py     # Authorization code flow
│   ├── session_flow.py  # Session-cookie fallback
│   └── refresh.py       # Refresh token flow
├── storage/
│   ├── keyring_backend.py
│   ├── state.py
│   └── cookies.py
└── core.py              # Backward-compatible wrappers (deprecated)
```

## Alur Login

1. `SsoClient.login()` mencoba `auth.code_flow.try_auth_code_flow()`
2. Jika gagal, fallback ke `auth.session_flow.try_session_based()`
3. Hasil dipetakan ke `AuthResult`
4. Token/cookies/state disimpan via storage layer

## Persistensi Data

- Secret: password + refresh token di OS keyring (`sso.bps.go.id`)
- Non-secret: `~/.config/sso-auth/state.json`
- Cookies: `~/.config/sso-auth/cookies.pickle`

## Kontrak API

```python
from sso_auth import SsoClient

client = SsoClient.from_keyring("username")
client.ensure_valid()     # login/refresh otomatis
session = client.session  # reusable untuk app adapter lain
```

## CLI Commands

- `sso-auth login <username>`
- `sso-auth logout <username>`
- `sso-auth whoami <username>`
- `sso-auth token <username>`
- `sso-auth refresh <username>`
- `sso-auth status <username>`

## Integrasi Lanjutan

Arsitektur ini disiapkan untuk fase berikutnya:

- `sso_auth.vpn` untuk handoff SAML FortiClient
- `sso_auth.browser` untuk injeksi session ke Playwright
- `sso_auth.apps.*` untuk adapter per aplikasi internal

## Catatan Keamanan

- `sso_tokens.json` tidak lagi disimpan default
- file token lama harus dianggap compromise dan wajib rotasi sesi/password

