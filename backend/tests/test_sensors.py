from test_runner import print_response, print_request, pretty, request, ok, fail, run_test
import time

SENSOR_CACHE = {}

# =========================================================
# AUTH
# =========================================================

def login_user():
    r = request(
        "POST",
        "/auth/login",
        json_body={"username": "test", "password": "test"}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# =========================================================
# SYSTEM + API KEY (IMPORTANTE)
# =========================================================

def get_system_and_api_key():
    token = login_user()

    r = request(
        "GET",
        "/irrigation-systems/",
        headers=auth_headers(token)
    )

    assert r.status_code == 200
    systems = r.json()

    if not systems:
        raise Exception("No systems found. Seed not loaded.")

    system = systems[0]

    api_key = system.get("api_key") or "seed-huerto-principal"

    return system["id"], api_key


# =========================================================
# SENSOR DISCOVERY SAFE
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

    systems_data = systems.json()
    if not systems_data:
        raise Exception("No systems available")

    system_id = systems_data[0]["id"]

    sensors = request(
        "GET",
        f"/irrigation-systems/{system_id}/sensors",
        headers=auth_headers(token)
    )

    assert sensors.status_code == 200

    sensors_data = sensors.json()
    if not sensors_data:
        raise Exception("No sensors found in system")

    sensor_id = sensors_data[0]["id"]

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
        json_body={"name": "Unauthorized"}
    )

    assert r.status_code == 401


def test_user_can_update_sensor():
    token = login_user()
    sensor_id = get_sensor_id()

    r = request(
        "PUT",
        f"/sensors/{sensor_id}",
        headers=auth_headers(token),
        json_body={"name": "Updated Sensor"}
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
# HISTORY
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
    assert "data" in r.json()


# =========================================================
# INGEST (ESP32 API KEY)
# =========================================================

def test_ingest_batch():
    system_id, api_key = get_system_and_api_key()

    r = request(
        "POST",
        "/sensors/ingest",
        headers={"X-API-KEY": api_key},
        json_body={
            "data": [
                {"sensor_key": "temp1", "value": 21.5},
                {"sensor_key": "soil1", "value": 55.2}
            ]
        }
    )

    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ingest_single():
    system_id, api_key = get_system_and_api_key()

    token = login_user()

    sensors = request(
        "GET",
        f"/irrigation-systems/{system_id}/sensors",
        headers=auth_headers(token)
    )

    assert sensors.status_code == 200

    sensor_id = sensors.json()[0]["id"]

    r = request(
        "POST",
        f"/sensors/ingest/{sensor_id}",
        headers={"X-API-KEY": api_key},
        params={"value": 33.3}
    )

    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    tests = [
        ("update_sensor_no_auth", test_update_sensor_no_auth),
        ("user_can_update_sensor", test_user_can_update_sensor),

        ("latest_value_no_auth", test_latest_value_no_auth),
        ("user_can_get_latest_value", test_user_can_get_latest_value),

        ("history_no_auth", test_history_no_auth),
        ("user_can_get_sensor_history", test_user_can_get_sensor_history),

        ("multi_sensor_history_no_auth", test_multi_sensor_history_no_auth),
        ("user_can_get_multi_sensor_history", test_user_can_get_multi_sensor_history),

        ("ingest_batch", test_ingest_batch),
        ("ingest_single", test_ingest_single),
    ]

    print("\n" + "=" * 80)
    print("STARTING SENSORS TEST SUITE")
    print("=" * 80)
    print(f"TOTAL TESTS: {len(tests)}")
    print("=" * 80)

    passed = 0
    failed = 0

    for name, fn in tests:
        time.sleep(0.2)
        try:
            run_test(name, fn)

            passed += 1
        except:
            failed += 1

    print("\n" + "=" * 80)
    print("FINAL RESULT")
    print("=" * 80)
    print(f"PASSED: {passed} / {len(tests)}")
    print(f"FAILED: {failed} / {len(tests)}")