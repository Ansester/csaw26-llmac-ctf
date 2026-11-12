# misc/house_of_hollow_houses

Flag: `csaw{w4nd3r3r_0f_th3_h0ll0w_h0us3}`

Static site (python http.server). 100+ rooms, but only a 5-step golden path matters; the rest are decoys.
1. `/robots.txt` -> `Disallow: /atrium/`
2. atrium: first letters of the `<span class="h">` paragraphs (hidden by CSS colour) spell OSSUARY.
3. ossuary: `<code class="rite">` is base64 for "what the mirror sees, the mirror keeps" -> `mirror`.
4. mirror: all text is `scaleX(-1)` flipped; it names the `wellspring`.
5. wellspring: morse hidden in the width of word gaps in the elegy (1 space = dot, 3 = dash, newline = letter, blank line = word) -> "THE FLAG LIES WAITING IN THE SANCTUM".
6. `/sanctum/` contains the flag.

Run: `python3 solve_house_of_hollow_houses.py HOST PORT`

Verification: ran the handout's `chal/` dir under `python3 -m http.server` (the Dockerfile's exact CMD; Docker was not usable in my sandbox) and the script derived the flag from live pages; it matches challenge.json (checked only after).
