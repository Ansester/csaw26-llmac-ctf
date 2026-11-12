#!/usr/bin/env python3
"""Usage: solve_house_of_hollow_houses.py HOST PORT   (walks the maze by decoding each room's hint)"""
import re, sys, base64, html, urllib.request

host, port = sys.argv[1], sys.argv[2]
def get(path):
    return urllib.request.urlopen(f"http://{host}:{port}{path}", timeout=10).read().decode()

MORSE = {'.-':'A','-...':'B','-.-.':'C','-..':'D','.':'E','..-.':'F','--.':'G','....':'H','..':'I',
         '.---':'J','-.-':'K','.-..':'L','--':'M','-.':'N','---':'O','.--.':'P','--.-':'Q','.-.':'R',
         '...':'S','-':'T','..-':'U','...-':'V','.--':'W','-..-':'X','-.--':'Y','--..':'Z'}

# 1. robots.txt -> disallowed room
room = re.search(r"Disallow:\s*/(\w+)/", get("/robots.txt")).group(1)
print("robots ->", room)

# 2. atrium: first letters of the CSS-hidden <span class="h"> spell the next room
page = get(f"/{room}/")
room = "".join(re.findall(r'<span class="h">(.)</span>', page)).lower()
print("hidden letters ->", room)

# 3. ossuary: base64 rite -> sentence; the noun in it that is a linked room is next
page = get(f"/{room}/")
rite = base64.b64decode(re.search(r'<code class="rite[^>]*>([^<]+)</code>', page).group(1)).decode()
linked = set(re.findall(r'href="/(\w+)/"', page))
room = next(w for w in re.findall(r"[a-z]+", rite) if w in linked)
print("rite:", rite, "->", room)

# 4. mirror: text is scaleX(-1) flipped (visual only); the "next chamber is called the <a>" names it
page = get(f"/{room}/")
room = re.search(r"next chamber is called the <a href=\"/(\w+)/\"", page).group(1)
print("mirror ->", room)

# 5. wellspring: morse in word-gap widths (1 space=dot, 3=dash; line=letter; blank line=word)
page = get(f"/{room}/")
elegy = html.unescape(re.search(r'<pre class="elegy">(.*?)</pre>', page, re.S).group(1))
msg = []
for word in elegy.split("\n\n"):
    letters = ""
    for line in word.split("\n"):
        gaps = re.findall(r" +", line.strip())
        letters += MORSE["".join("-" if len(g) >= 3 else "." for g in gaps) or "."] if gaps or line.strip() else ""
    msg.append(letters)
text = " ".join(msg)
print("morse:", text)
room = text.split()[-1].lower()

# 6. sanctum
flag = re.search(r"csaw\{[^}]*\}", get(f"/{room}/")).group(0)
print(flag)
