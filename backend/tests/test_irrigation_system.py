from test_runner import print_response, print_request, pretty, request, ok, fail, run_test
import time

# =========================================================
# AUTH HELPERS
# =========================================================

def login_admin():
    r = request(
        "POST",
        "/auth/login",
        json_body={"username": "admin", "password": "admin"}
    )
    assert r.status_code == 200
    return r.json()["access_token"]


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
            "username": "admin",
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
            "username": "test",
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
# SHARED USERS
# =========================================================

def test_get_shared_users_as_owner():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}/shared-users",
        headers=auth_headers(token)
    )

    assert r.status_code == 200


def test_get_shared_users_forbidden_for_viewer():
    owner_token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    # Share system to admin first
    request(
        "POST",
        f"/irrigation-systems/{system_id}/share",
        headers=auth_headers(owner_token),
        json_body={
            "username": "admin",
            "role": "viewer"
        }
    )

    admin_token = login_admin()

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}/shared-users",
        headers=auth_headers(admin_token)
    )

    assert r.status_code == 403


# =========================================================
# UNSHARE
# =========================================================

def test_unshare_user_from_system():
    owner_token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    # 1. Share admin user
    request(
        "POST",
        f"/irrigation-systems/{system_id}/share",
        headers=auth_headers(owner_token),
        json_body={
            "username": "admin",
            "role": "viewer"
        }
    )

    # 2. Get shared users to obtain user_id
    r = request(
        "GET",
        f"/irrigation-systems/{system_id}/shared-users",
        headers=auth_headers(owner_token)
    )

    assert r.status_code == 200

    shared_users = r.json()
    admin_user = next((u for u in shared_users if u["username"] == "admin"), None)

    assert admin_user is not None
    admin_user_id = admin_user["user_id"]

    # 3. Remove user
    r2 = request(
        "DELETE",
        f"/irrigation-systems/{system_id}/share/{admin_user_id}",
        headers=auth_headers(owner_token)
    )

    assert r2.status_code in (200, 204)


def test_cannot_unshare_owner():
    owner_token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    # Try to remove owner himself
    r = request(
        "DELETE",
        f"/irrigation-systems/{system_id}/share/999999",
        headers=auth_headers(owner_token)
    )

    # Either 404 or 400 depending on DB state
    assert r.status_code in (400, 404)


# =========================================================
# OWNER FIELD CHECK
# =========================================================

def test_system_has_owner_username():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

    data = r.json()

    # owner_username must exist (even if null in edge cases)
    assert "owner_username" in data

# =========================================================
# API KEY
# =========================================================
def test_owner_can_get_apikey():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}/apikey",
        headers=auth_headers(token)
    )

    assert r.status_code == 200
    assert "api_key" in r.json()

def test_viewer_cannot_get_apikey():
    owner_token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    request(
        "POST",
        f"/irrigation-systems/{system_id}/share",
        headers=auth_headers(owner_token),
        json_body={
            "username": "admin",
            "role": "viewer"
        }
    )

    admin_token = login_admin()

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}/apikey",
        headers=auth_headers(admin_token)
    )

    assert r.status_code == 403

def test_owner_can_regenerate_apikey():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    r = request(
        "POST",
        f"/irrigation-systems/{system_id}/apikey/regenerate",
        headers=auth_headers(token)
    )

    assert r.status_code == 200
    assert "api_key" in r.json()

def test_viewer_cannot_regenerate_apikey():
    owner_token = login_user()
    system_id = SYSTEM_CACHE.get("system_id") or test_user_create_system()

    request(
        "POST",
        f"/irrigation-systems/{system_id}/share",
        headers=auth_headers(owner_token),
        json_body={
            "username": "admin",
            "role": "viewer"
        }
    )

    admin_token = login_admin()

    r = request(
        "POST",
        f"/irrigation-systems/{system_id}/apikey/regenerate",
        headers=auth_headers(admin_token)
    )

    assert r.status_code == 403

# =========================================================
# SYSTEM SENSORS
# =========================================================
def test_user_can_list_system_sensors():
    token = login_user()
    system_id = SYSTEM_CACHE.get("system_id")

    r = request(
        "GET",
        f"/irrigation-systems/{system_id}/sensors",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

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

        # SHARE
        ("owner_share_system", test_owner_share_system),
        ("non_owner_cannot_share", test_non_owner_cannot_share),

        # SHARED USERS
        ("get_shared_users_as_owner", test_get_shared_users_as_owner),
        ("get_shared_users_forbidden_for_viewer", test_get_shared_users_forbidden_for_viewer),

        # UNSHARE
        ("unshare_user_from_system", test_unshare_user_from_system),
        ("cannot_unshare_owner", test_cannot_unshare_owner),

        # OWNER FIELD
        ("system_has_owner_username", test_system_has_owner_username),

        # API KEY
        ("owner_can_get_apikey", test_owner_can_get_apikey),
        ("viewer_cannot_get_apikey", test_viewer_cannot_get_apikey),
        ("owner_can_regenerate_apikey", test_owner_can_regenerate_apikey),
        ("viewer_cannot_regenerate_apikey", test_viewer_cannot_regenerate_apikey),

        # SYSTEM SENSORS
        ("user_can_list_system_sensors", test_user_can_list_system_sensors),

        # DELETE
        ("delete_no_auth", test_delete_no_auth),
        ("owner_delete_system", test_owner_delete_system),
    ]

    print("\nSTARTING IRRIGATION SYSTEMS TEST SUITE\n")

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