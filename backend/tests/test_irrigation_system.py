import requests
import json
import traceback
import time

BASE_URL = "http://localhost:8000"

# =========================================================
# ANSI COLORS
# =========================================================

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


# =========================================================
# HELPERS
# =========================================================

def pretty(obj):
    try:
        return json.dumps(obj, indent=2, ensure_ascii=False)
    except Exception:
        return str(obj)


def print_request(method, url, headers=None, body=None):
    print(f"{CYAN}{BOLD}\n--- REQUEST ---{RESET}")
    print(f"{BLUE}{method} {url}{RESET}")

    if headers:
        print(f"{YELLOW}\nHEADERS:{RESET}")
        print(pretty(headers))

    if body is not None:
        print(f"{YELLOW}\nBODY:{RESET}")
        print(pretty(body))


def print_response(resp):
    print(f"{CYAN}{BOLD}\n--- RESPONSE ---{RESET}")
    print(f"{BLUE}STATUS: {resp.status_code}{RESET}")

    try:
        print(f"{YELLOW}\nBODY:{RESET}")
        print(pretty(resp.json()))
    except Exception:
        print(resp.text)


def ok(msg):
    print(f"{GREEN}OK: {msg}{RESET}")


def fail(msg):
    print(f"{RED}FAIL: {msg}{RESET}")


# =========================================================
# HTTP WRAPPER
# =========================================================

def request(method, path, headers=None, json_body=None):
    url = f"{BASE_URL}{path}"

    print_request(method, url, headers, json_body)

    resp = requests.request(
        method,
        url,
        headers=headers,
        json=json_body
    )

    print_response(resp)
    return resp


# =========================================================
# AUTH HELPERS
# =========================================================

def login_admin():
    r = request(
        "POST",
        "/auth/login",
        json_body={"email": "admin@admin.com", "password": "admin"}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def login_user():
    r = request(
        "POST",
        "/auth/login",
        json_body={"email": "test@test.com", "password": "secret123"}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# =========================================================
# RUNNER
# =========================================================

def run_test(name, fn):
    print(f"\n{BOLD}{CYAN}{'=' * 80}{RESET}")
    print(f"{BOLD}TEST: {name}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 80}{RESET}")

    try:
        fn()
        ok(name)
    except Exception as e:
        fail(name)
        print(f"{RED}\nERROR:{RESET}")
        print(str(e))
        traceback.print_exc()


# =========================================================
# TESTS
# =========================================================

SYSTEM_CACHE = {}


# ---------------------------------------------------------
# CREATE
# ---------------------------------------------------------

def test_create_system_no_auth():
    r = request(
        "POST",
        "/irrigation-systems/",
        json_body={
            "alias": "My Farm",
            "description": "Test system"
        }
    )
    assert r.status_code == 401


def test_user_create_system():
    token = login_user()

    r = request(
        "POST",
        "/irrigation-systems/",
        headers=auth_headers(token),
        json_body={
            "alias": "Farm 1",
            "description": "Main irrigation system"
        }
    )

    assert r.status_code in (200, 201)

    data = r.json()
    SYSTEM_CACHE["system_id"] = data["id"]

    return data["id"]


# ---------------------------------------------------------
# LIST
# ---------------------------------------------------------

def test_user_list_systems():
    token = login_user()

    r = request(
        "GET",
        "/irrigation-systems/",
        headers=auth_headers(token)
    )

    assert r.status_code == 200


# ---------------------------------------------------------
# GET
# ---------------------------------------------------------

def test_user_get_system():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}",
        headers=auth_headers(token)
    )

    assert r.status_code == 200


# ---------------------------------------------------------
# UPDATE
# ---------------------------------------------------------

def test_owner_update_system():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "PUT",
        f"/irrigation-systems/{system_id}",
        headers=auth_headers(token),
        json_body={
            "alias": "Updated Farm"
        }
    )

    assert r.status_code == 200


def test_update_no_auth():
    system_id = SYSTEM_CACHE.get("system_id", 1)

    r = request(
        "PUT",
        f"/irrigation-systems/{system_id}",
        json_body={"alias": "Hack"}
    )

    assert r.status_code == 401


# ---------------------------------------------------------
# SHARE
# ---------------------------------------------------------

def test_owner_share_system():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "POST",
        f"/irrigation-systems/{system_id}/share",
        headers=auth_headers(token),
        json_body={
            "user_id": 1,
            "role": "viewer"
        }
    )

    assert r.status_code in (200, 201)


def test_non_owner_cannot_share():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    token2 = login_admin()

    r = request(
        "POST",
        f"/irrigation-systems/{system_id}/share",
        headers=auth_headers(token2),
        json_body={
            "user_id": 3,
            "role": "viewer"
        }
    )

    assert r.status_code == 403


# ---------------------------------------------------------
# DELETE
# ---------------------------------------------------------

def test_delete_no_auth():
    r = request(
        "DELETE",
        "/irrigation-systems/1"
    )

    assert r.status_code == 401


def test_owner_delete_system():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "DELETE",
        f"/irrigation-systems/{system_id}",
        headers=auth_headers(token)
    )

    assert r.status_code in (200, 204)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    tests = [
        ("create_system_no_auth", test_create_system_no_auth),
        ("user_create_system", test_user_create_system),
        ("user_list_systems", test_user_list_systems),
        ("user_get_system", test_user_get_system),
        ("owner_update_system", test_owner_update_system),
        ("update_no_auth", test_update_no_auth),
        ("owner_share_system", test_owner_share_system),
        ("non_owner_cannot_share", test_non_owner_cannot_share),
        ("delete_no_auth", test_delete_no_auth),
        ("owner_delete_system", test_owner_delete_system),
    ]

    print("\nSTARTING IRRIGATION SYSTEMS TEST SUITE\n")

    passed = 0
    failed = 0

    for name, fn in tests:
        run_test(name, fn)
        time.sleep(1)

        try:
            passed += 1
        except:
            failed += 1

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(f"PASSED: {passed} / {len(tests)}")
    print(f"FAILED: {failed} / {len(tests)}")