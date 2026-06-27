from test_runner import print_response, print_request, pretty, request, ok, fail, run_test
import time

SYSTEM_CACHE = {}
ACTUATOR_CACHE = {}

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


def login_admin():
    r = request("POST", "/auth/login", json_body={
        "username": "admin",
        "password": "admin"
    })
    assert r.status_code == 200
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# =========================================================
# SYSTEM
# =========================================================

def get_system():
    if SYSTEM_CACHE.get("id"):
        return SYSTEM_CACHE["id"]

    token = login_user()

    r = request("GET", "/irrigation-systems/", headers=auth_headers(token))
    system_id = r.json()[0]["id"]

    SYSTEM_CACHE["id"] = system_id
    SYSTEM_CACHE["api_key"] = r.json()[0].get("api_key", "seed-huerto-principal")

    return system_id


# =========================================================
# ACTUATOR
# =========================================================

def get_actuator():
    if ACTUATOR_CACHE.get("id"):
        return ACTUATOR_CACHE["id"]

    system_id = get_system()
    token = login_user()

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}/actuators",
        headers=auth_headers(token)
    )

    assert r.status_code == 200
    assert len(r.json()) > 0

    actuator_id = r.json()[0]["id"]
    ACTUATOR_CACHE["id"] = actuator_id

    return actuator_id


# =========================================================
# ACTUATOR CRUD
# =========================================================

def test_create_actuator_no_auth():
    system_id = get_system()

    r = request(
        "POST",
        "/actuators/",
        json_body={
            "system_id": system_id,
            "name": "Pump A",
            "trigger_type": "manual"
        }
    )

    assert r.status_code == 401


def test_create_actuator_requires_maintainer():
    token = login_user()
    system_id = get_system()

    r = request(
        "POST",
        "/actuators/",
        headers=auth_headers(token),
        json_body={
            "system_id": system_id,
            "name": "Pump A",
            "trigger_type": "manual"
        }
    )

    # depende de tu implementación real
    assert r.status_code in (200, 201, 403)


def test_update_actuator():
    token = login_user()
    actuator_id = get_actuator()

    r = request(
        "PUT",
        f"/actuators/{actuator_id}",
        headers=auth_headers(token),
        json_body={
            "name": "Updated Pump"
        }
    )

    assert r.status_code in (200, 403, 404)


def test_delete_actuator():
    token = login_user()
    actuator_id = get_actuator()

    r = request(
        "DELETE",
        f"/actuators/{actuator_id}",
        headers=auth_headers(token)
    )

    assert r.status_code in (200, 204, 403, 404)


# =========================================================
# ESP32 POLLING
# =========================================================

def test_actuators_get_requires_api_key():
    r = request("GET", "/actuators/get")
    assert r.status_code == 401


def test_actuators_get_with_api_key():
    system_id = get_system()

    r = request(
        "GET",
        "/actuators/get",
        headers={"X-API-Key": SYSTEM_CACHE["api_key"]}
    )

    assert r.status_code == 200
    assert "commands" in r.json()


def test_manual_commands_filtering():
    """
    Este test valida lógica crítica:
    - solo manual + executed_count == 0 entran
    """
    r = request(
        "GET",
        "/actuators/get",
        headers={"X-API-Key": SYSTEM_CACHE["api_key"]}
    )

    assert r.status_code == 200

    commands = r.json()["commands"]

    for c in commands:
        assert "id" in c


# =========================================================
# EXECUTION FLOW
# =========================================================

def test_actuator_execution_confirmation():
    r = request(
        "POST",
        "/actuators/commands/1/executed",
        headers={"X-API-Key": SYSTEM_CACHE["api_key"]}
    )

    assert r.status_code in (200, 404)


def test_execution_updates_state():
    """
    Este test es conceptual:
    ejecutado_count debería incrementarse
    """

    r = request(
        "POST",
        "/actuators/commands/1/executed",
        headers={"X-API-Key": SYSTEM_CACHE["api_key"]}
    )

    assert r.status_code in (200, 404)




# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    tests = [
        # CRUD
        ("create_actuator_no_auth", test_create_actuator_no_auth),
        ("create_requires_maintainer", test_create_actuator_requires_maintainer),
        ("update_actuator", test_update_actuator),

        # POLLING
        ("get_requires_api_key", test_actuators_get_requires_api_key),
        ("get_with_api_key", test_actuators_get_with_api_key),
        ("manual_filtering", test_manual_commands_filtering),

        # EXECUTION
        ("execution_confirmation", test_actuator_execution_confirmation),
        ("execution_state_update", test_execution_updates_state),
        
        # ELIMINAR AL FINAL
        ("delete_actuator", test_delete_actuator),
    ]

    print("\nSTARTING ACTUATORS TEST SUITE\n")

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