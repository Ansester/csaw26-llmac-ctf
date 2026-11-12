#!/usr/bin/env python3
"""House of Hollow Houses solver. Usage: solve_house_of_hollow_houses.py HOST PORT"""
import sys, re, base64, urllib.request

host, port = sys.argv[1], sys.argv[2]
def get(p):
    return urllib.request.urlopen(f"http://{host}:{port}{p}").read().decode()

# 0. robots.txt -> Disallow: /atrium/
room = re.search(r"Disallow:\s*/(\w+)/", get("/robots.txt")).group(1)
print("robots ->", room)

# 1. atrium: letters wrapped in <span class="h"> (opacity .07) spell the next room
room = "".join(re.findall(r'<span class="h">(.)</span>', get(f"/{room}/"))).lower()
print("hidden letters ->", room)

# 2. ossuary: base64 'rite' -> "what the mirror sees, the mirror keeps"
code = re.search(r'<code class="rite[^>]*>([^<]+)</code>', get(f"/{room}/")).group(1)
sent = base64.b64decode(code).decode()
print("rite ->", sent)
room = re.search(r"the (\w+) keeps$", sent).group(1)   # 'mirror'

# 3. mirror: page text is scaleX(-1) mirrored; it names 'the next chamber is called the wellspring'
room = re.search(r"next chamber is called the (?:<[^>]*>)*(\w+)", get(f"/{room}/")).group(1)
print("mirror ->", room)

# 4. wellspring: poem, one line per letter, one stanza per word. A line's letter is
#    determined by its 'segment signature' = words per run, runs split by 3-space gaps.
SIG = {  # signature -> letter (table recovered from the 30 poem lines, see WRITEUP)
 (1,1):'T',(5,):'H',(2,):'E',(3,2):'F',(2,3):'L',(2,1):'A',(1,1,2):'G',(3,):'I',(4,):'S',
 (2,1,1):'W',(1,2):'N',(1,2,2):'C',(3,1):'U',(1,1,1):'M'}
pre = re.search(r'<pre[^>]*>(.*?)</pre>', get(f"/{room}/"), re.S).group(1)
words = []
for stanza in pre.strip().split("\n\n"):
    w = ""
    for line in stanza.split("\n"):
        sig = tuple(len(s.split()) for s in re.split(r" {2,}", line.strip()))
        w += SIG[sig]
    words.append(w.lower())
print("poem ->", " ".join(words))
room = words[-1]  # 'sanctum'

# 5. final room
print(re.search(r'<span class="flag[^>]*>([^<]+)</span>', get(f"/{room}/")).group(1))
