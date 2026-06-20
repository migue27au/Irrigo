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

SENSOR_CACHE = {}


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

    print(f"{YELLOW}\nHEADERS:{RESET}")
    print(pretty(dict(resp.headers)))

    try:
        print(f"{YELLOW}\nBODY (JSON):{RESET}")
        print(pretty(resp.json()))
    except Exception:
        print(f"{YELLOW}\nBODY (TEXT):{RESET}")
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
        json_body={
            "username": "admin",
            "password": "admin"
        }
    )

    assert r.status_code == 200

    return r.json()["access_token"]


def login_user():
    r = request(
        "POST",
        "/auth/login",
        json_body={
            "username": "test",
            "password": "test"
        }
    )

    assert r.status_code == 200

    return r.json()["access_token"]


def auth_headers(token):
    return {
        "Authorization": f"Bearer {token}"
    }


# =========================================================
# SENSOR DISCOVERY
# =========================================================

def get_sensor_id():
    if SENSOR_CACHE.get("sensor_id"):
        return SENSOR_CACHE["sensor_id"]

    token = login_user()

    systems = request(
        "GET",
        "/irrigation-systems/",
        headers=auth_headers(token)
    )

    assert systems.status_code == 200
    system_id = systems.json()[0]["id"]

    sensors = request(
        "GET",
        f"/irrigation-systems/{system_id}/sensors",
        headers=auth_headers(token)
    )

    assert sensors.status_code == 200
    assert len(sensors.json()) > 0

    sensor_id = sensors.json()[0]["id"]

    SENSOR_CACHE["sensor_id"] = sensor_id

    return sensor_id


# =========================================================
# UPDATE SENSOR
# =========================================================

def test_update_sensor_no_auth():
    sensor_id = get_sensor_id()

    r = request(
        "PUT",
        f"/sensors/{sensor_id}",
        json_body={
            "name": "Unauthorized"
        }
    )

    assert r.status_code == 401


def test_user_can_update_sensor():
    token = login_user()
    sensor_id = get_sensor_id()

    r = request(
        "PUT",
        f"/sensors/{sensor_id}",
        headers={
            **auth_headers(token),
            "Content-Type": "application/json"
        },
        json_body={
            "name": "Updated Sensor"
        }
    )

    assert r.status_code == 200
    assert r.json()["name"] == "Updated Sensor"


# =========================================================
# LATEST VALUE
# =========================================================

def test_latest_value_no_auth():
    sensor_id = get_sensor_id()

    r = request(
        "GET",
        f"/sensors/{sensor_id}/latest"
    )

    assert r.status_code == 401


def test_user_can_get_latest_value():
    token = login_user()
    sensor_id = get_sensor_id()

    r = request(
        "GET",
        f"/sensors/{sensor_id}/latest",
        headers=auth_headers(token)
    )

    assert r.status_code == 200


# =========================================================
# SENSOR HISTORY
# =========================================================

def test_history_no_auth():
    sensor_id = get_sensor_id()

    r = request(
        "GET",
        f"/sensors/{sensor_id}/history"
    )

    assert r.status_code == 401


def test_user_can_get_sensor_history():
    token = login_user()
    sensor_id = get_sensor_id()

    r = request(
        "GET",
        f"/sensors/{sensor_id}/history",
        headers=auth_headers(token)
    )

    assert r.status_code == 200
    assert isinstance(r.json(), list)


# =========================================================
# MULTI SENSOR HISTORY
# =========================================================

def test_multi_sensor_history_no_auth():
    sensor_id = get_sensor_id()

    r = request(
        "GET",
        f"/sensors/history?sensor_ids={sensor_id}"
    )

    assert r.status_code == 401


def test_user_can_get_multi_sensor_history():
    token = login_user()
    sensor_id = get_sensor_id()

    r = request(
        "GET",
        f"/sensors/history?sensor_ids={sensor_id}",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

    data = r.json()

    assert "data" in data


# =========================================================
# RUNNER CORE
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
# MAIN
# =========================================================

if __name__ == "__main__":

    tests = [

        # UPDATE SENSOR
        ("update_sensor_no_auth", test_update_sensor_no_auth),
        ("user_can_update_sensor", test_user_can_update_sensor),

        # LATEST VALUE
        ("latest_value_no_auth", test_latest_value_no_auth),
        ("user_can_get_latest_value", test_user_can_get_latest_value),

        # SENSOR HISTORY
        ("history_no_auth", test_history_no_auth),
        ("user_can_get_sensor_history", test_user_can_get_sensor_history),

        # MULTI SENSOR HISTORY
        ("multi_sensor_history_no_auth", test_multi_sensor_history_no_auth),
        ("user_can_get_multi_sensor_history", test_user_can_get_multi_sensor_history),
    ]

    print("\nSTARTING SENSORS TEST SUITE\n")

    passed = 0
    failed = 0

    for name, fn in tests:

        run_test(name, fn)

        time.sleep(0.2)

        try:
            passed += 1
        except:
            failed += 1

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(f"PASSED: {passed} / {len(tests)}")
    print(f"FAILED: {failed} / {len(tests)}")