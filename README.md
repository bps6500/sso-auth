# sso-auth

Python package untuk autentikasi SSO Keycloak (`sso.bps.go.id`) secara programatis.

## Install dari wheel/sdist

Build artifact:

```bash
python -m build
```

Hasil build ada di folder `dist/`:

- `dist/sso_auth-<version>-py3-none-any.whl`
- `dist/sso_auth-<version>.tar.gz`

Install di project lain:

```bash
pip install /path/ke/dist/sso_auth-<version>-py3-none-any.whl
```

## Penggunaan

Sebagai library:

```python
from sso_auth import authenticate

result = authenticate("username", "password")
print(result)
```

Sebagai CLI:

```bash
sso-auth
```
