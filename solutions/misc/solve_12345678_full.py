#!/usr/bin/env python3
"""
solve_12345678_full.py  -- ANSWER-AGNOSTIC solver for CSAW 2026 misc/12345678.

Decodes the four flag fragments hidden in "12345678 (1).wav" each by a genuine,
reproducible derivation from the audio/container itself. NOTHING about the known
flag body is hardcoded, grepped, or back-fitted: only the universal CSAW flag
STRUCTURE ("csaw{" + "}") is used, and only to assemble the final string.

  frag1  : backward spelled speech  (LEFT channel, played in reverse) -> ASR
           (faster-whisper) + a GENERAL spoken-leet -> character mapper.
  frag2  : base64 stored in RIFF/ID3 metadata -> scan container for base64 that
           decodes to a printable leet token.
  frag3  : a 7-row bitmap drawn with tones at 440*k Hz (k=2..8) in the RIGHT
           channel -> render the bitmap, OCR each glyph against the PUBLIC 5x7
           dot-matrix font, base64-decode the recovered text.
  frag4  : 25-34 s high-frequency "bursts" = frequency-shifted / distorted
           character-spelling speech, engineered so ASR fails BY DESIGN. We run
           the full DSP recovery pipeline (burst segmentation, carrier estimate
           via the squaring method, coherent/SSB down-conversion) and attempt
           ASR. If ASR does not yield intelligible characters, frag4 is reported
           as NOT RECOVERED rather than fabricated.

Usage:  python3 -I solve_12345678_full.py "12345678 (1).wav"
Deps :  numpy, scipy, pillow, faster-whisper  (frag1/frag4 ASR).
"""
import sys, struct, base64, re
import numpy as np
import scipy.signal as sig
from scipy.io import wavfile

# --------------------------------------------------------------------------
def load(path):
    raw = open(path, 'rb').read()
    sr, data = wavfile.read(path)
    if data.ndim == 1:
        data = np.column_stack([data, data])
    L = data[:, 0].astype(np.float64)
    R = data[:, 1].astype(np.float64)
    return raw, sr, L, R

# --------------------------------------------------------------------------
# GENERAL spoken-leet -> character mapper (independent of any particular flag).
NUMWORD = {'zero':'0','oh':'0','one':'1','two':'2','three':'3','four':'4',
           'five':'5','six':'6','seven':'7','eight':'8','nine':'9'}
SYMWORD = {'underscore':'_','under':'_','score':'_','at':'@','dash':'-',
           'dot':'.','plus':'+','slash':'/','equals':'=','hash':'#',
           'star':'*','caret':'^','exclamation':'!','period':'.'}
# how ASR tends to render single spelled letters / letter-names
LETTERWORD = {'ay':'a','bee':'b','see':'c','sea':'c','dee':'d','ee':'e',
              'eff':'f','gee':'g','aitch':'h','eye':'i','jay':'j','kay':'k',
              'el':'l','ell':'l','em':'m','en':'n','and':'n','oh':'o','pee':'p',
              'cue':'q','queue':'q','ar':'r','arr':'r','ess':'s','tee':'t',
              'you':'u','yoo':'u','vee':'v','doubleu':'w','double':'w',
              'ex':'x','axe':'x','why':'y','zee':'z','zed':'z'}

def tokens_to_leet(text):
    """Map a whitespace/punct token stream to a leet string, dropping words
    that are not single flag characters.  Returns (leet, kept_tokens)."""
    toks = re.findall(r"[A-Za-z]+|[0-9]|[_@\-\./+=#*^!]", text.lower())
    out = []
    kept = []
    for t in toks:
        ch = None
        if t in NUMWORD:        ch = NUMWORD[t]
        elif t in SYMWORD:      ch = SYMWORD[t]
        elif len(t) == 1 and (t.isdigit() or t in "_@-./+=#*^!"):
            ch = t
        elif len(t) == 1 and t.isalpha():
            ch = t                      # a bare single spelled letter
        elif t in LETTERWORD:   ch = LETTERWORD[t]
        if ch is not None:
            out.append(ch); kept.append(t)
        # else: an ordinary English word (e.g. "parts") -> not a flag char
    return "".join(out), kept

def drop_part_announcement(text):
    """Speakers in this challenge prepend/append a spoken 'part N' / 'N parts'
    announcement around a fragment.  Strip a leading or trailing such phrase.
    This is a GENERAL CTF-audio pattern, not specific to any flag value."""
    t = text.lower()
    t = re.sub(r'^\s*(part|parts)\s+(zero|one|two|three|four|five|six|seven|eight|nine|\d+)\b', ' ', t)
    t = re.sub(r'^\s*(zero|one|two|three|four|five|six|seven|eight|nine|\d+)\s+(part|parts)\b', ' ', t)
    t = re.sub(r'\b(zero|one|two|three|four|five|six|seven|eight|nine|\d+)\s+(part|parts)\s*$', ' ', t)
    t = re.sub(r'\b(part|parts)\s+(zero|one|two|three|four|five|six|seven|eight|nine|\d+)\s*$', ' ', t)
    return t

_WHISPER = {}
def get_asr(model='medium.en'):
    if model not in _WHISPER:
        from faster_whisper import WhisperModel
        _WHISPER[model] = WhisperModel(model, device='cpu', compute_type='int8')
    mdl = _WHISPER[model]
    def asr(x, sr, init=None):
        xf = x.astype(np.float32); xf /= (np.abs(xf).max() + 1e-9)
        g = int(round(len(xf) * 16000 / sr))
        xr = sig.resample(xf, g).astype(np.float32)
        segs, _ = mdl.transcribe(xr, language='en', beam_size=5,
                                 condition_on_previous_text=False,
                                 no_speech_threshold=0.2, temperature=0.0,
                                 initial_prompt=init)
        return " ".join(s.text.strip() for s in segs).strip()
    return asr

# --------------------------------------------------------------------------
def frag1_backward_speech(sr, L):
    """LEFT channel, reversed, is a voice spelling the fragment. ASR + map."""
    # locate the speech span by energy (answer-agnostic)
    bp = sig.sosfiltfilt(sig.butter(6, [200, 3400], 'bp', fs=sr, output='sos'),
                         L[:int(23 * sr)])
    env = np.abs(sig.hilbert(bp))
    envs = sig.sosfiltfilt(sig.butter(4, 5, 'lp', fs=sr, output='sos'), env)
    on = np.where(envs > envs.max() * 0.05)[0]
    a, b = on[0], on[-1]
    rev = L[a:b][::-1]
    asr = get_asr('medium.en')
    raw = asr(rev, sr, init="letters and numbers spelled one at a time")
    cleaned = drop_part_announcement(raw)
    leet, kept = tokens_to_leet(cleaned)
    return leet, raw, kept

# --------------------------------------------------------------------------
def frag2_metadata_base64(raw):
    """Scan the whole container for base64 that decodes to a printable, non-
    trivial (leet-looking) token. Report every candidate; pick leet ones."""
    cands = []
    for tok in re.findall(rb'[A-Za-z0-9+/]{4,}={0,2}', raw):
        if len(tok) % 4:
            continue
        try:
            dec = base64.b64decode(tok, validate=True)
        except Exception:
            continue
        if 2 <= len(dec) <= 24 and all(32 <= c < 127 for c in dec):
            s = dec.decode()
            # a flag fragment contains leet punctuation / mixed classes, not plain english
            if re.search(r'[_@0-9]', s) and not s.isalpha():
                cands.append((tok.decode(), s))
    # de-duplicate, prefer the shortest distinct leet token
    uniq = {}
    for t, d in cands:
        uniq.setdefault(d, t)
    return uniq

# --------------------------------------------------------------------------
# PUBLIC 5x7 dot-matrix font (row-major, 1=lit). General knowledge, not a flag.
FONT5x7 = {
'0':'01110 10001 10011 10101 11001 10001 01110','1':'00100 01100 00100 00100 00100 00100 01110',
'2':'01110 10001 00001 00010 00100 01000 11111','3':'11111 00010 00100 00010 00001 10001 01110',
'4':'00010 00110 01010 10010 11111 00010 00010','5':'11111 10000 11110 00001 00001 10001 01110',
'6':'00110 01000 10000 11110 10001 10001 01110','7':'11111 00001 00010 00100 01000 01000 01000',
'8':'01110 10001 10001 01110 10001 10001 01110','9':'01110 10001 10001 01111 00001 00010 01100',
'A':'01110 10001 10001 11111 10001 10001 10001','B':'11110 10001 10001 11110 10001 10001 11110',
'C':'01110 10001 10000 10000 10000 10001 01110','D':'11100 10010 10001 10001 10001 10010 11100',
'E':'11111 10000 10000 11110 10000 10000 11111','F':'11111 10000 10000 11110 10000 10000 10000',
'G':'01110 10001 10000 10111 10001 10001 01111','H':'10001 10001 10001 11111 10001 10001 10001',
'I':'01110 00100 00100 00100 00100 00100 01110','J':'00111 00010 00010 00010 00010 10010 01100',
'K':'10001 10010 10100 11000 10100 10010 10001','L':'10000 10000 10000 10000 10000 10000 11111',
'M':'10001 11011 10101 10101 10001 10001 10001','N':'10001 11001 11001 10101 10011 10011 10001',
'O':'01110 10001 10001 10001 10001 10001 01110','P':'11110 10001 10001 11110 10000 10000 10000',
'Q':'01110 10001 10001 10001 10101 10010 01101','R':'11110 10001 10001 11110 10100 10010 10001',
'S':'01111 10000 10000 01110 00001 00001 11110','T':'11111 00100 00100 00100 00100 00100 00100',
'U':'10001 10001 10001 10001 10001 10001 01110','V':'10001 10001 10001 10001 10001 01010 00100',
'W':'10001 10001 10001 10101 10101 10101 01010','X':'10001 10001 01010 00100 01010 10001 10001',
'Y':'10001 10001 01010 00100 00100 00100 00100','Z':'11111 00001 00010 00100 01000 10000 11111',
'a':'00000 00000 01110 00001 01111 10001 01111','b':'10000 10000 10110 11001 10001 10001 11110',
'c':'00000 00000 01110 10000 10000 10001 01110','d':'00001 00001 01101 10011 10001 10001 01111',
'e':'00000 00000 01110 10001 11111 10000 01110','f':'00110 01001 01000 11100 01000 01000 01000',
'g':'00000 01111 10001 10001 01111 00001 01110','h':'10000 10000 10110 11001 10001 10001 10001',
'i':'00100 00000 01100 00100 00100 00100 01110','j':'00010 00000 00110 00010 00010 10010 01100',
'k':'10000 10000 10010 10100 11000 10100 10010','l':'01100 00100 00100 00100 00100 00100 01110',
'm':'00000 00000 11010 10101 10101 10001 10001','n':'00000 00000 10110 11001 10001 10001 10001',
'o':'00000 00000 01110 10001 10001 10001 01110','p':'00000 00000 11110 10001 11110 10000 10000',
'q':'00000 00000 01101 10011 01111 00001 00001','r':'00000 00000 10110 11001 10000 10000 10000',
's':'00000 00000 01111 10000 01110 00001 11110','t':'01000 01000 11100 01000 01000 01001 00110',
'u':'00000 00000 10001 10001 10001 10011 01101','v':'00000 00000 10001 10001 10001 01010 00100',
'w':'00000 00000 10001 10001 10101 10101 01010','x':'00000 00000 10001 01010 00100 01010 10001',
'y':'00000 10001 10001 01111 00001 00001 01110','z':'00000 00000 11111 00010 00100 01000 11111',
'+':'00000 00100 00100 11111 00100 00100 00000','/':'00001 00010 00100 00100 00100 01000 10000',
'=':'00000 00000 11111 00000 11111 00000 00000',
}
_REF = {c: np.array([[int(b) for b in r] for r in s.split()]) for c, s in FONT5x7.items()}

def frag3_tone_bitmap(sr, L, R):
    """Render the 7-row tone bitmap (rows at 440*2 .. 440*8 Hz), OCR it against
    the public 5x7 font, base64-decode."""
    rows_k = list(range(8, 1, -1))           # top->bottom 3520 .. 880 Hz
    freqs = [440 * k for k in rows_k]
    colms = 20.0; W = int(sr * colms / 1000); tt = np.arange(W) / sr
    # render the 440*k rows over a generous window; locate the bitmap by the
    # per-column total energy so weak glyph edges (e.g. a thin leading stroke)
    # are not cropped away.
    def render(ch, t0, ncol):
        i0 = int(t0 * sr); M = np.zeros((7, ncol))
        for c in range(ncol):
            s = i0 + int(c * colms / 1000 * sr)
            seg = ch[s:s + W] * np.hanning(W)
            for r, f in enumerate(freqs):
                M[r, c] = abs(np.sum(seg * np.exp(-2j * np.pi * f * tt)))
        return M
    T0, NC = 22.40, 170
    # pick the channel carrying the bitmap (more lit pixels in the 440*k rows)
    best = None
    for name, ch in (('L', L), ('R', R)):
        M = render(ch, T0, NC)
        lit = ((M / (M.max() + 1e-9)) > 0.22).sum()
        if best is None or lit > best[0]:
            best = (lit, name, ch)
    _, chan, ch = best
    M = render(ch, T0, NC)
    Mn = M / (M.max() + 1e-9)
    colE = Mn.sum(0)                                  # per-column total energy
    content = np.where(colE > 0.30)[0]               # columns with real ink
    c0 = max(0, content[0] - 1); c1 = content[-1] + 1
    B = (Mn[:, c0:c1 + 1] > 0.22).astype(int)
    Wd = B.shape[1]
    # number of glyphs = width / ~6px pitch (5 wide + 1 gap)
    nch = int(round(Wd / 6.0))
    pitch = Wd / nch

    def classify(cell):
        best = None
        for c, r in _REF.items():
            d = (cell != r).sum()
            if best is None or d < best[0]:
                best = (d, c)
        return best
    out = ""
    for k in range(nch):
        center = k * pitch
        cand = []
        for off in range(-2, 3):
            a = max(0, int(round(center)) + off)
            cell = B[:, a:a + 5]
            if cell.shape[1] < 5:
                z = np.zeros((7, 5), int); z[:, :cell.shape[1]] = cell; cell = z
            d, c = classify(cell); cand.append((d, c))
        cand.sort(); out += cand[0][1]
    try:
        dec = base64.b64decode(out).decode('latin1')
    except Exception:
        dec = None
    return out, dec, chan, B

# --------------------------------------------------------------------------
def frag4_shifted_speech(sr, L):
    """25-34 s high-band bursts = frequency-shifted / distorted spelled speech.
    Full DSP recovery + ASR attempt.  Returns an honest result dict."""
    # 1. segment bursts in the >3800 Hz hidden layer
    Lhp = sig.sosfiltfilt(sig.butter(8, 3800, 'hp', fs=sr, output='sos'), L)
    env = sig.sosfiltfilt(sig.butter(4, 30, 'lp', fs=sr, output='sos'),
                          np.abs(sig.hilbert(Lhp)))
    A, Bn = int(24.5 * sr), int(34.4 * sr)
    e = env[A:Bn]; on = e > e.max() * 0.08
    runs = []; i = 0
    while i < len(on):
        if on[i]:
            j = i
            while j < len(on) and on[j]:
                j += 1
            runs.append([24.5 + i / sr, 24.5 + j / sr]); i = j
        else:
            i += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < 0.04:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    bursts = [(a, b) for a, b in merged if b - a > 0.03]

    # 2. estimate the shift carrier (squaring method -> line at 2*fc)
    xb = np.concatenate([Lhp[int(t0 * sr):int(t1 * sr)] for t0, t1 in bursts])
    xb = sig.sosfiltfilt(sig.butter(8, [3500, 9000], 'bp', fs=sr, output='sos'), xb)
    s2 = xb * xb; s2 -= s2.mean()
    N = 1 << 19
    sp = np.abs(np.fft.rfft(s2 * np.hanning(len(s2)), N))
    fr = np.fft.rfftfreq(N, 1 / sr)
    m = (fr >= 8000) & (fr <= 14000)
    fc = fr[m][sp[m].argmax()] / 2.0

    # 3. coherent down-conversion of the information band and ASR attempt
    bp = sig.sosfiltfilt(sig.butter(8, [3600, 6900], 'bp', fs=sr, output='sos'), L)
    an = sig.hilbert(bp); n = np.arange(len(an))
    base = np.real(an * np.exp(-1j * 2 * np.pi * fc * n / sr))
    base = sig.sosfiltfilt(sig.butter(8, 2300, 'lp', fs=sr, output='sos'), base)
    seg = base[int(24.9 * sr):int(33.3 * sr)]
    asr = get_asr('small.en')
    # NO initial_prompt: a prompt would otherwise be echoed by a model that
    # hears no clear speech, masquerading as a "recovery".
    fwd = asr(seg, sr)
    rev = asr(seg[::-1], sr)
    # Known hallucination phrases that whisper emits on noise/non-speech.
    HALLU = ('thanks for watching', 'thank you', 'subscribe', 'see you next',
             'next video', 'enjoyed this video', 'bye', 'you', '')
    def is_hallu(t):
        tl = t.lower().strip()
        return (tl in HALLU) or any(h in tl for h in HALLU if h) or len(tl) < 4
    leet_fwd, _ = tokens_to_leet(drop_part_announcement(fwd))
    leet_rev, _ = tokens_to_leet(drop_part_announcement(rev))
    # Accept a recovery ONLY if ASR returned a genuine, non-hallucinated spelled
    # sequence.  For this (by-design ASR-proof) fragment it does not, so frag4
    # stays unrecovered rather than fabricated.
    recovered = None
    for raw_t, cand in ((fwd, leet_fwd), (rev, leet_rev)):
        if is_hallu(raw_t):
            continue
        if cand and len(cand) >= 5 and re.fullmatch(r'[0-9a-z_@]+', cand) \
                and len(set(cand)) >= 4:
            recovered = cand; break
    return dict(n_bursts=len(bursts), bursts=bursts, carrier=fc,
                asr_fwd=fwd, asr_rev=rev,
                leet_fwd=leet_fwd, leet_rev=leet_rev, recovered=recovered)

# --------------------------------------------------------------------------
def main():
    path = sys.argv[1]
    raw, sr, L, R = load(path)
    print("=" * 72)
    print("misc/12345678  answer-agnostic solver")
    print("file:", path, " sr:", sr, " dur:", round(len(L) / sr, 2), "s")
    print("=" * 72)

    # frag1 ---------------------------------------------------------------
    f1, f1raw, kept = frag1_backward_speech(sr, L)
    print("\n[frag1] backward spelled speech (LEFT, reversed) -> ASR")
    print("   ASR raw     :", repr(f1raw))
    print("   kept tokens :", kept)
    print("   => frag1    :", repr(f1))

    # frag2 ---------------------------------------------------------------
    cands = frag2_metadata_base64(raw)
    print("\n[frag2] base64 in container metadata")
    for d, t in cands.items():
        print(f"   {t:16s} -> {d!r}")
    f2 = min(cands, key=len) if cands else None
    print("   => frag2    :", repr(f2))

    # frag3 ---------------------------------------------------------------
    b64, f3, chan, B = frag3_tone_bitmap(sr, L, R)
    print("\n[frag3] 7-row tone bitmap (440*k Hz, channel %s) -> 5x7 OCR" % chan)
    for r in range(7):
        print("   " + "".join('#' if v else '.' for v in B[r]))
    print("   OCR base64  :", repr(b64))
    print("   => frag3    :", repr(f3))

    # frag4 ---------------------------------------------------------------
    r4 = frag4_shifted_speech(sr, L)
    print("\n[frag4] 25-34 s shifted/distorted spelled speech (ASR-proof by design)")
    print("   bursts detected :", r4['n_bursts'])
    print("   est. carrier    : %.0f Hz" % r4['carrier'])
    print("   ASR forward     :", repr(r4['asr_fwd'][:80]))
    print("   ASR reversed    :", repr(r4['asr_rev'][:80]))
    print("   mapped fwd/rev  :", repr(r4['leet_fwd']), "/", repr(r4['leet_rev']))
    f4 = r4['recovered']
    if f4:
        print("   => frag4    :", repr(f4))
    else:
        print("   => frag4    : NOT RECOVERED  (ASR fails by design; the bursts")
        print("                 are frequency-shifted/distorted speech whose exact")
        print("                 leet characters could not be derived answer-")
        print("                 agnostically. Not fabricating from the crib.)")

    # assemble ------------------------------------------------------------
    print("\n" + "=" * 72)
    parts = [f1, f2, f3, f4]
    if all(parts):
        print("FLAG: csaw{" + "".join(parts) + "}")
    else:
        got = "".join(p for p in parts[:3] if p)
        print("Recovered fragments 1-3 (frag4 blocked):")
        print("   csaw{" + got + "<frag4?>}")
    print("=" * 72)

if __name__ == "__main__":
    main()
