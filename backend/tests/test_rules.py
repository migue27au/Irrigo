from test_runner import request, run_test
import time

SYSTEM_CACHE = {}
COMMAND_CACHE = {}
GROUP_CACHE = {}
CONDITION_CACHE = {}


# =========================================================
# AUTH HELPERS
# =========================================================

def login_user():
    r = request("POST", "/auth/login", json_body={
        "username": "test",
        "password": "test"
    })
    assert r.status_code == 200
    return r.json()["access_token"]


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# =========================================================
# SYSTEM HELPERS
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


def get_command_id():
    if COMMAND_CACHE.get("command_id"):
        return COMMAND_CACHE["command_id"]

    system_id, api_key = get_system_and_api_key()

    r = request("GET", "/actuators/get", headers={
        "X-API-Key": api_key
    })

    assert r.status_code == 200

    commands = r.json()["commands"]
    assert len(commands) > 0

    auto = next((c for c in commands if c["trigger_type"] == "automatic"), None)
    manual = next((c for c in commands if c["trigger_type"] == "manual"), None)

    chosen = auto or manual
    COMMAND_CACHE["command_id"] = chosen["id"]

    return COMMAND_CACHE["command_id"]


# =========================================================
# ACTUATORS / COMMANDS FLOW TEST
# =========================================================

def test_actuator_get_commands():
    system_id, api_key = get_system_and_api_key()

    r = request(
        "GET",
        "/actuators/get",
        headers={"X-API-Key": api_key}
    )

    assert r.status_code == 200
    data = r.json()

    assert "commands" in data
    assert isinstance(data["commands"], list)
    assert len(data["commands"]) > 0


def test_manual_command_rules_should_fail():
    system_id, api_key = get_system_and_api_key()

    r = request(
        "GET",
        "/actuators/get",
        headers={"X-API-Key": api_key}
    )

    commands = r.json()["commands"]
    manual = next((c for c in commands if c["trigger_type"] == "manual"), None)

    if manual:
        r2 = request(
            "GET",
            f"/rules/{manual['id']}",
            headers={"X-API-Key": api_key}
        )
        assert r2.status_code == 404


# =========================================================
# RULE GROUP CRUD
# =========================================================

def test_create_rule_group():
    token = login_user()
    command_id = get_command_id()

    r = request(
        "POST",
        f"/rules/group/{command_id}",
        headers=auth_headers(token),
        json_body={
            "name": "Moisture group",
            "description": "auto irrigation rule",
            "conditions": [
                {
                    "type": "sensor",
                    "sensor_id": 1,
                    "operator": "<",
                    "value": 40
                }
            ]
        }
    )

    assert r.status_code in (200, 201)

    data = r.json()
    GROUP_CACHE["group_id"] = data["group_id"]


def test_add_condition():
    token = login_user()
    group_id = GROUP_CACHE.get("group_id")

    assert group_id is not None, "group_id missing (create_rule_group failed)"

    r = request(
        "POST",
        f"/rules/group/{group_id}/condition",
        headers=auth_headers(token),
        json_body={
            "type": "sensor",
            "sensor_id": 1,
            "operator": "<",
            "value": 40
        }
    )

    assert r.status_code in (200, 201)

    CONDITION_CACHE["condition_id"] = r.json()["condition_id"]


# =========================================================
# RULE FETCH (ESP32)
# =========================================================

def test_rules_requires_api_key():
    command_id = get_command_id()

    r = request("GET", f"/rules/{command_id}")
    assert r.status_code == 401


def test_rules_only_automatic():
    system_id, api_key = get_system_and_api_key()

    r = request(
        "GET",
        "/actuators/get",
        headers={"X-API-Key": api_key}
    )

    commands = r.json()["commands"]
    auto = next((c for c in commands if c["trigger_type"] == "automatic"), None)

    if not auto:
        return

    r2 = request(
        "GET",
        f"/rules/{auto['id']}",
        headers={"X-API-Key": api_key}
    )

    assert r2.status_code == 200

    data = r2.json()
    assert "groups" in data
    assert isinstance(data["groups"], list)


def test_rules_structure_validation():
    system_id, api_key = get_system_and_api_key()

    r = request(
        "GET",
        "/actuators/get",
        headers={"X-API-Key": api_key}
    )

    auto = next((c for c in r.json()["commands"] if c["trigger_type"] == "automatic"), None)

    if not auto:
        return

    r2 = request(
        "GET",
        f"/rules/{auto['id']}",
        headers={"X-API-Key": api_key}
    )

    data = r2.json()

    for group in data["groups"]:
        assert "group_id" in group or "id" in group
        assert "conditions" in group
        assert isinstance(group["conditions"], list)

        for cond in group["conditions"]:
            assert "id" in cond
            assert "type" in cond


# =========================================================
# EDGE CASES
# =========================================================

def test_invalid_command():
    system_id, api_key = get_system_and_api_key()

    r = request(
        "GET",
        "/rules/999999",
        headers={"X-API-Key": api_key}
    )

    assert r.status_code == 404


def test_wrong_api_key():
    command_id = get_command_id()

    r = request(
        "GET",
        f"/rules/{command_id}",
        headers={"X-API-Key": "invalid-key"}
    )

    assert r.status_code in (401, 403, 404)


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":

    tests = [
        ("actuator_get_commands", test_actuator_get_commands),

        ("create_rule_group", test_create_rule_group),
        ("add_condition", test_add_condition),

        ("rules_requires_api_key", test_rules_requires_api_key),
        ("rules_only_automatic", test_rules_only_automatic),
        ("rules_structure_validation", test_rules_structure_validation),

        ("invalid_command", test_invalid_command),
        ("wrong_api_key", test_wrong_api_key),

        ("manual_command_rules_should_fail", test_manual_command_rules_should_fail),
    ]

    print("\nSTARTING RULES TEST SUITE\n")

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