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

## Keamanan

- Password + refresh token disimpan di OS keyring
- Metadata non-rahasia disimpan di `~/.config/sso-auth/state.json`
- Jangan commit token file ke repository
