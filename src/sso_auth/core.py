"""SSO Keycloak authentication helpers for sso.bps.go.id."""

from __future__ import annotations

import base64
import getpass
import json
import os
import re
import sys
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

# Konfigurasi default
SSO_BASE_URL = "https://sso.bps.go.id"
REALM = "pegawai-bps"

# Daftar client_id yang umum bersifat public di Keycloak
PUBLIC_CLIENTS = [
    "account-console",
    "security-admin-console",
    "admin-cli",
    "broker",
]

# Client yang membutuhkan secret (opsional via env var SSO_CLIENT_SECRET)
CONFIDENTIAL_CLIENT = "account"
CLIENT_SECRET = os.environ.get("SSO_CLIENT_SECRET", "")

AUTH_URL = f"{SSO_BASE_URL}/auth/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL = f"{SSO_BASE_URL}/auth/realms/{REALM}/protocol/openid-connect/token"
USERINFO_URL = f"{SSO_BASE_URL}/auth/realms/{REALM}/protocol/openid-connect/userinfo"


def create_session() -> requests.Session:
    """Create HTTP session with browser-like user-agent."""
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        }
    )
    return session


def try_direct_grant(session: requests.Session, username: str, password: str) -> dict:
    """Try Resource Owner Password Credentials (Direct Grant)."""
    print("[*] Metode 1: Direct Grant (ROPC)")
    print("    Mencoba beberapa public client...")
    print()

    for client_id in PUBLIC_CLIENTS:
        payload = {
            "grant_type": "password",
            "client_id": client_id,
            "username": username,
            "password": password,
            "scope": "openid",
        }

        resp = session.post(TOKEN_URL, data=payload)
        if resp.status_code == 200:
            tokens = resp.json()
            print(f"    [OK] Berhasil dengan client: {client_id}")
            tokens["_method"] = "direct_grant"
            tokens["_client_id"] = client_id
            return tokens

        try:
            err = resp.json()
            err_msg = err.get("error_description", err.get("error", ""))
        except ValueError:
            err_msg = resp.text[:100]
        print(f"    [--] {client_id}: {err_msg}")

    print()
    print("    Tidak ada public client yang berhasil untuk Direct Grant.")
    return {}


def get_redirect_uri(client_id: str) -> str:
    """Return matching redirect URI for each known client."""
    redirect_map = {
        "account": f"{SSO_BASE_URL}/auth/realms/{REALM}/account/login-redirect",
        "account-console": f"{SSO_BASE_URL}/auth/realms/{REALM}/account/",
        "security-admin-console": f"{SSO_BASE_URL}/auth/admin/{REALM}/console/",
        "admin-cli": f"{SSO_BASE_URL}/auth/realms/{REALM}/account/",
        "broker": f"{SSO_BASE_URL}/auth/realms/{REALM}/broker/",
    }
    return redirect_map.get(client_id, f"{SSO_BASE_URL}/auth/realms/{REALM}/account/")


def get_login_form(session: requests.Session, client_id: str) -> str:
    """Open authorization page and return login form action URL."""
    redirect_uri = get_redirect_uri(client_id)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid",
    }

    try:
        resp = session.get(AUTH_URL, params=params, allow_redirects=True)
        if resp.status_code != 200:
            return ""
    except requests.exceptions.RequestException:
        return ""

    soup = BeautifulSoup(resp.text, "html.parser")
    form = soup.find("form", id="kc-form-login") or soup.find("form")
    if not form or not form.get("action"):
        return ""
    return str(form["action"])


def submit_credentials(
    session: requests.Session, action_url: str, username: str, password: str
) -> str:
    """Submit login form and return authorization code if any."""
    payload = {"username": username, "password": password}
    resp = session.post(action_url, data=payload, allow_redirects=False)

    for _ in range(10):
        if resp.status_code not in (301, 302, 303, 307, 308):
            break

        location = resp.headers.get("Location", "")
        parsed = urlparse(location)
        query_params = parse_qs(parsed.query)

        if "code" in query_params:
            return query_params["code"][0]
        if "error" in query_params:
            return ""

        resp = session.get(location, allow_redirects=False)

    return ""


def try_auth_code_flow(session: requests.Session, username: str, password: str) -> dict:
    """Try browser-simulated authorization code flow with known clients."""
    print("[*] Metode 2: Authorization Code Flow")
    print("    Mencoba login via form + token exchange...")
    print()

    clients_to_try = PUBLIC_CLIENTS + ([CONFIDENTIAL_CLIENT] if CLIENT_SECRET else [])
    for client_id in clients_to_try:
        print(f"    Mencoba client: {client_id}...", end=" ")
        trial_session = create_session()

        action_url = get_login_form(trial_session, client_id)
        if not action_url:
            print("form tidak ditemukan")
            continue

        auth_code = submit_credentials(trial_session, action_url, username, password)
        if not auth_code:
            print("login gagal atau code tidak diperoleh")
            continue

        payload = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "redirect_uri": get_redirect_uri(client_id),
            "code": auth_code,
        }
        if client_id == CONFIDENTIAL_CLIENT and CLIENT_SECRET:
            payload["client_secret"] = CLIENT_SECRET

        resp = trial_session.post(TOKEN_URL, data=payload)
        if resp.status_code == 200:
            tokens = resp.json()
            print("BERHASIL!")
            tokens["_method"] = "auth_code"
            tokens["_client_id"] = client_id
            session.cookies.update(trial_session.cookies)
            return tokens

        try:
            err = resp.json()
            print(f"{err.get('error', 'gagal')}")
        except ValueError:
            print("gagal")

    print()
    print("    Tidak ada client yang berhasil untuk Auth Code flow.")
    return {}


def try_session_based(session: requests.Session, username: str, password: str) -> dict:
    """Try session-cookie based login as fallback."""
    print("[*] Metode 3: Session-Based Authentication")
    print("    Login untuk mendapatkan session cookies...")
    print()

    try:
        action_url = get_login_form(session, CONFIDENTIAL_CLIENT)
        if not action_url:
            print("    [!] Tidak dapat menemukan form login.")
            return {}

        payload = {"username": username, "password": password}
        session.post(action_url, data=payload, allow_redirects=True)
    except requests.exceptions.RequestException as exc:
        print(f"    [!] Error saat login: {exc}")
        return {}

    kc_cookies = {
        k: v
        for k, v in session.cookies.items()
        if "KEYCLOAK" in k.upper() or "AUTH_SESSION" in k.upper() or "KC_" in k.upper()
    }
    all_cookies = dict(session.cookies)
    if not all_cookies:
        print("    [!] Tidak ada cookies yang diperoleh.")
        return {}

    print(f"    [OK] Login berhasil! {len(all_cookies)} cookies diperoleh.")
    print()

    userinfo = {}
    try:
        ui_resp = session.get(USERINFO_URL)
        if ui_resp.status_code == 200:
            userinfo = ui_resp.json()
            print("    [OK] User info berhasil diambil via session.")
    except Exception:
        pass

    if not userinfo:
        try:
            account_url = f"{SSO_BASE_URL}/auth/realms/{REALM}/account"
            acc_resp = session.get(account_url)
            if acc_resp.status_code == 200:
                try:
                    userinfo = acc_resp.json()
                    print("    [OK] User info diambil dari Account API.")
                except ValueError:
                    soup = BeautifulSoup(acc_resp.text, "html.parser")
                    scripts = soup.find_all("script")
                    for script in scripts:
                        if script.string and "userName" in script.string:
                            match = re.search(
                                r'"userName"\s*:\s*"([^"]+)"',
                                script.string,
                            )
                            if match:
                                userinfo["preferred_username"] = match.group(1)
                                print("    [OK] Username diekstrak dari Account page.")
                                break
        except Exception:
            pass

    return {
        "_method": "session_cookies",
        "_cookies": all_cookies,
        "_keycloak_cookies": kc_cookies,
        "user_info": userinfo,
    }


def get_user_info(session: requests.Session, access_token: str) -> dict:
    """Fetch user profile using access token."""
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = session.get(USERINFO_URL, headers=headers)
    if resp.status_code == 200:
        return resp.json()
    return {}


def display_results(result: dict) -> None:
    """Print authentication result to stdout."""
    print()
    print("=" * 60)
    print("  HASIL OTENTIKASI")
    print("=" * 60)

    method = result.get("_method", "unknown")
    client_id = result.get("_client_id", "-")
    print(f"\n  Metode     : {method}")
    print(f"  Client ID  : {client_id}")

    user_info = result.get("user_info", {})
    if user_info:
        print(f"\n  Nama       : {user_info.get('name', user_info.get('firstName', 'N/A'))}")
        print(f"  Email      : {user_info.get('email', 'N/A')}")
        print(
            f"  Username   : "
            f"{user_info.get('preferred_username', user_info.get('username', 'N/A'))}"
        )

    if "access_token" in result:
        print(f"\n  Access Token  : {result['access_token'][:50]}...")
        print(f"  Refresh Token : {result.get('refresh_token', 'N/A')[:50]}...")
        print(f"  Token Type    : {result.get('token_type', 'N/A')}")
        print(f"  Expires In    : {result.get('expires_in', 'N/A')} detik")

        try:
            payload_b64 = result["access_token"].split(".")[1]
            payload_b64 += "=" * (4 - len(payload_b64) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_b64))
            print("\n  --- Info dari JWT ---")
            print(f"  Subject    : {payload.get('sub', 'N/A')}")
            print(f"  Name       : {payload.get('name', 'N/A')}")
            print(f"  Email      : {payload.get('email', 'N/A')}")
            print(f"  Realm      : {payload.get('azp', 'N/A')}")
            if "realm_access" in payload:
                roles = payload["realm_access"].get("roles", [])
                print(f"  Roles      : {', '.join(roles)}")
        except Exception:
            pass

    if "_cookies" in result:
        cookies = result["_cookies"]
        print(f"\n  Session Cookies ({len(cookies)} total):")
        for name, value in cookies.items():
            display_val = value[:40] + "..." if len(value) > 40 else value
            print(f"    {name} = {display_val}")

    print()


def save_results(result: dict, filename: str = "sso_tokens.json") -> None:
    """Save auth output as JSON file."""
    output = {}
    for key, value in result.items():
        if not key.startswith("_") or key in ("_method", "_client_id"):
            output[key] = value

    if "_cookies" in result:
        output["cookies"] = result["_cookies"]

    with open(filename, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print(f"  Hasil disimpan ke: {filename}")


def authenticate(username: str, password: str, session: requests.Session | None = None) -> dict:
    """Run auth flow and return result dictionary."""
    working_session = session or create_session()
    result = try_direct_grant(working_session, username, password)
    if not result:
        print()
        result = try_auth_code_flow(working_session, username, password)
    if not result:
        print()
        result = try_session_based(working_session, username, password)
    if result and "access_token" in result and "user_info" not in result:
        user_info = get_user_info(working_session, result["access_token"])
        if user_info:
            result["user_info"] = user_info
    return result


def cli_main() -> None:
    """CLI entrypoint."""
    print("=" * 60)
    print("  SSO Authentication - sso.bps.go.id")
    print("  Realm: pegawai-bps")
    print("=" * 60)
    print()

    username = input("Username : ").strip()
    password = getpass.getpass("Password : ")

    if not username or not password:
        print("[!] Username dan password tidak boleh kosong.")
        sys.exit(1)

    print()
    result = authenticate(username, password)
    if result:
        display_results(result)
        save_results(result)
        return

    print()
    print("=" * 60)
    print("  [!] SEMUA METODE GAGAL")
    print("=" * 60)
    print()
    print("  Kemungkinan penyebab:")
    print("  1. Username atau password salah")
    print("  2. Semua client di server bersifat confidential")
    print("  3. Direct Access Grants dinonaktifkan untuk semua client")
    print("  4. IP/jaringan Anda diblokir oleh server")
    print()
    print("  Solusi:")
    print("  - Pastikan kredensial benar")
    print("  - Minta client_secret ke admin, lalu set env var:")
    print("    export SSO_CLIENT_SECRET='secret_anda'")
    print()
    sys.exit(1)
