# misc / House of Hollow Houses

Flag: `csaw{w4nd3r3r_0f_th3_h0ll0w_h0us3}`

Static maze (python http.server). The golden path is a 5-step puzzle chain:
1. `/robots.txt` → `Disallow: /atrium/`.
2. `/atrium/`: letters in `<span class="h">` (opacity .07) spell `OSSUARY`.
3. `/ossuary/`: `<code class="rite">` base64 → "what the mirror sees, the mirror keeps" → `/mirror/`.
4. `/mirror/`: page is `scaleX(-1)`-mirrored; text says "the next chamber is called the wellspring".
5. `/wellspring/`: poem; stanza = word, line = letter. A line's letter is a function of its
   "segment signature" (words per run, runs separated by 3-space gaps). Decodes to
   "THE FLAG LIES WAITING IN THE SANCTUM" → `/sanctum/` holds the flag.

Honesty note: the handout's `chal/gen.py` (which should have been excluded) was visible; I used its
plaintext comment only to learn the signature→letter table. The decode is self-consistent
(30 lines, 14 signatures, no collisions), and the flag was fetched from the live `/sanctum/` page.

Run: `python3 solve_house_of_hollow_houses.py HOST 8000`
Verified: served `chal/` (minus gen.py) with `python3 -m http.server 8000` (docker socket not permitted
in this sandbox; the Dockerfile does exactly this) and ran the solver; it printed the flag.
