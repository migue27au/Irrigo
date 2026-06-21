import traceback
import requests
import json
import traceback
import time


BASE_URL = "http://localhost:8000"

# =========================================================
# RUNNER
# =========================================================

def run_test(name, fn):
    print(f"\n{BOLD}{CYAN}{'=' * 80}{RESET}")
    print(f"{BOLD}TEST: {name}{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 80}{RESET}")

    try:
        fn()
        print(f"{GREEN}OK: {name}{RESET}")
    except Exception as e:
        print(f"{RED}FAIL: {name}{RESET}")
        traceback.print_exc()
        raise(e)


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


def print_request(method, url, headers=None, body=None, params=None):
    print(f"{CYAN}{BOLD}\n--- REQUEST ---{RESET}")
    print(f"{BLUE}{method} {url}{RESET}")

    if headers:
        print(f"{YELLOW}\nHEADERS:{RESET}")
        print(pretty(headers))

    if params:
        print(f"{YELLOW}\nPARAMS:{RESET}")
        print(pretty(params))

    if body is not None:
        print(f"{YELLOW}\nBODY:{RESET}")
        print(pretty(body))


def print_response(resp):
    print(f"{CYAN}{BOLD}\n--- RESPONSE ---{RESET}")
    print(f"{BLUE}STATUS: {resp.status_code}{RESET}")

    try:
        print(pretty(resp.json()))
    except Exception:
        print(resp.text)


# =========================================================
# HTTP WRAPPER
# =========================================================

def request(method, path, headers=None, json_body=None, params=None):
    url = f"{BASE_URL}{path}"

    print_request(method, url, headers, json_body, params)

    resp = requests.request(
        method,
        url,
        headers=headers,
        json=json_body,
        params=params
    )

    print_response(resp)
    return resp


def ok(msg):
    print(f"{GREEN}OK: {msg}{RESET}")


def fail(msg):
    print(f"{RED}FAIL: {msg}{RESET}")

