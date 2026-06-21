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

def test_me_no_auth():
    r = request("GET", "/users/me")
    assert r.status_code == 401

def test_user_can_me():
    token = login_user()

    r = request(
        "GET",
        "/users/me",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


# =========================================================
# TESTS
# =========================================================

def test_list_users_no_auth():
    r = request("GET", "/users/")
    assert r.status_code == 401


def test_get_user_no_auth():
    r = request("GET", "/users/1")
    assert r.status_code == 401


def test_create_user_no_auth():
    r = request(
        "POST",
        "/users/",
        json_body={
            "username": "x",
            "password": "test",
            "name": "X"
        }
    )
    assert r.status_code == 401


def test_delete_user_no_auth():
    r = request("DELETE", "/users/1")
    assert r.status_code == 401


def test_login_admin():
    token = login_admin()
    assert token


def test_login_user():
    token = login_user()
    assert token


def test_user_can_list_users():
    token = login_user()

    r = request(
        "GET",
        "/users/",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

def test_user_can_list_user():
    token = login_user()

    r = request(
        "GET",
        "/users/1",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

def test_user_cannot_create_user():
    token = login_user()

    r = request(
        "POST",
        "/users/",
        headers=auth_headers(token),
        json_body={
            "username": "hack",
            "password": "test",
            "name": "Hack"
        }
    )

    assert r.status_code == 403


def test_user_cannot_delete_user():
    token = login_user()

    r = request(
        "DELETE",
        "/users/2",
        headers=auth_headers(token)
    )

    assert r.status_code == 403


def test_admin_can_list_users():
    token = login_admin()

    r = request(
        "GET",
        "/users/",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

def test_admin_can_list_user():
    token = login_admin()

    r = request(
        "GET",
        "/users/1",
        headers=auth_headers(token)
    )

    assert r.status_code == 200

def test_admin_can_create_user():
    token = login_admin()

    r = request(
        "POST",
        "/users/",
        headers=auth_headers(token),
        json_body={
            "username": "dummy",
            "password": "test",
            "name": "Dummy"
        }
    )

    assert r.status_code in (200, 201)


def test_admin_can_delete_user():
    token = login_admin()

    r = request(
        "DELETE",
        "/users/2",
        headers=auth_headers(token)
    )

    assert r.status_code in (200, 204)



# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    tests = [
        ("list_users_no_auth", test_list_users_no_auth),
        ("get_user_no_auth", test_get_user_no_auth),
        ("create_user_no_auth", test_create_user_no_auth),
        ("delete_user_no_auth", test_delete_user_no_auth),

        ("login_admin", test_login_admin),
        ("login_user", test_login_user),
        
        ("me_no_auth", test_me_no_auth),
        ("user_can_me", test_user_can_me),

        ("user_can_list_users", test_user_can_list_users),
        ("user_can_list_user", test_user_can_list_user),
        ("user_cannot_create_user", test_user_cannot_create_user),
        ("user_cannot_delete_user", test_user_cannot_delete_user),

        ("admin_can_list_users", test_admin_can_list_users),
        ("admin_can_list_user", test_admin_can_list_user),
        ("admin_can_create_user", test_admin_can_create_user),
        ("admin_can_delete_user", test_admin_can_delete_user),
    ]

    print("\nSTARTING E2E TEST RUN\n")

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