# web/juggler

**Flag:** `csaw{tw0_f0r_0n3_2gc9w2hz}`

No reference solve shipped for this one — solved from scratch by reading
`src/*.php`.

## Vulnerability

Two bugs chain together, both in `src/profile_update.php` and
`public/admin.php`:

**1. Blind mass assignment** (`src/profile_update.php`, reachable via
`POST /dashboard.php` with `Content-Type: application/json`):

```php
foreach ($jsonData as $jsonKey => $jsonValue) {
    if (array_key_exists($jsonKey, $_SESSION))
        $_SESSION[$jsonKey] = $jsonValue;
    if (in_array($jsonKey, $dbColumns, true)) {
        $stmt = $pdo->prepare("UPDATE users SET `$jsonKey` = ? WHERE id = ?");
        ...
        $stmt->execute([$jsonValue, $_SESSION["user_id"]]);
    }
}
```

Any JSON key the client sends gets written straight into `$_SESSION` (and
the `users` table) as long as the key name matches an existing session
key / DB column — no allowlist, and critically **no type check** on
`$jsonValue`. `role` is both a session key (set at login from the DB) and
a `users` column, so a logged-in low-privilege user can send
`{"role": <anything>}` and have `$_SESSION["role"]` become that exact
value — including a PHP `bool`, which a web form could never submit.

**2. Loose (`==`) type comparison in the admin gate**
(`public/admin.php`):

```php
$adminRoles = $config["Roles"]["admin_roles"];   // 2 random 32-char strings
if (!isset($_SESSION["role"]) || !in_array($_SESSION["role"], $adminRoles))
    header("Location: index.php");
```

`in_array()` without its optional `strict` (3rd) argument defaults to
loose `==` comparisons. The admin role strings are randomized at
container build time (`Dockerfile`: `sed -i
"s/placeholder_admin_role.../$random32chars/g"`), so they're
unguessable by design — but PHP's loose-comparison rule for
`bool == string` doesn't care what the string's *contents* are: both
sides get cast to `bool`, and any non-empty, non-`"0"` string is `true`.
So `in_array(true, [<any two non-empty strings>])` is `true` **regardless
of what those strings actually are**.

This is the "juggling" of the challenge description: "at least one is
assigned an airborne trajectory" — `role` gets *assigned* a value that
isn't the expected type (a string) but a bool, literally "in the air"
between true/false rather than grounded as one of the real role strings,
and that's exactly what slips past the loose check.

## Exploit

1. `POST /register.php` → create an unprivileged account.
2. `POST /login.php` → `$_SESSION["role"] = "user"`.
3. `POST /dashboard.php`, `Content-Type: application/json`, body
   `{"csrf_token": "<current>", "username": "<own username>", "role": true}`
   — the `username` field is required only to pass
   `profile_update.php`'s own empty-check (set it to the account's own
   current name, which the `username != own id` uniqueness query happily
   allows); `role: true` is what actually matters.
4. `$_SESSION["role"]` is now the PHP boolean `true`.
5. `GET /admin.php` → `in_array(true, $adminRoles)` is `true` → flag
   rendered from `flag.txt`.

(Note: the client must POST to `/register.php` / `/login.php` themselves,
not `/register_handler.php` / `/login_handler.php` directly — those
handler files live in `src/`, outside the Apache/PHP document root
[`public/`], and are only ever `require_once`'d from inside the
corresponding public page when the request method is POST.)

## How I verified it

No Docker available in this sandbox (socket permission denied, no
passwordless sudo), and no system PHP installed either (no root for
`apt install php`). Used `micromamba` (a self-contained, no-root package
manager, fetched as a single static binary) to install `php` with
`pdo_sqlite` from conda-forge into an isolated env, then reproduced the
Dockerfile's own setup steps exactly: `php src/init.php` to create the
SQLite schema, then randomized `config/config.ini`'s two admin-role
placeholders with fresh random 32-character strings (same `sed` command
the Dockerfile runs) so the admin roles are genuinely unguessable, not
left at the literal `placeholder_admin_role1/2` strings from source.
Served the app with PHP's built-in server (`php -S`, document root
`public/`).

Ran `solve_juggler.py` against that live instance. It performs the whole
chain above purely over HTTP (register → login → the type-juggling POST
→ GET admin.php) with no knowledge of the randomized role strings, and
the service itself returned the flag in `admin.php`'s rendered HTML:
`csaw{tw0_f0r_0n3_2gc9w2hz}` — matching the repo's own `flag.txt` /
`challenge.json` (used only as a final sanity cross-check, not as the
source of the flag; the point of re-randomizing the admin roles before
testing was specifically to confirm the exploit doesn't depend on
knowing them in advance).

## Run it

```bash
python3 solve_juggler.py <base_url>   # defaults to http://127.0.0.1:8099
```
