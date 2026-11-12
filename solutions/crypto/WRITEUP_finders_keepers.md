# finders_keepers (crypto)

**Answer to submit (plaintext, no wrapper):** `cantfindit`
**Status: confirmed correct.** Submit `cantfindit`.
**Secondary (metadata layer, not the answer):** `csaw{y0u_@lw@ys_kn0w_wh3r3_t0_l00k}`

challenge.json says "Submit the decoded plaintext without a flag wrapper", so the intended answer is the decoded video message.


## Findings
1. `finderskeepers.mp4` is a 10 s / 300 frame / 1080p video with no audio: dark background with drifting pastel rectangles.
2. Starting around t~6-7 s a faint, low-contrast, rotated string drifts across the upper-middle of the frame and is fully revealed in the last
   second: `Y2FudGZpbmRpdA==` (seen in frames ~211-300, crop x700-1500,y60-260). Base64 -> `cantfindit`.
3. The MP4 `uuid` box contains an XMP packet (ExifTool/Canva) whose `dc:subject` bag holds a second base64 blob:
   `ZXNucHtkMGNfQHl6QGdsX21uMGpfcG0zejNfZzBfbzAwc30=` -> `esnp{d0c_@yz@gl_mn0j_pm3z3_g0_o00s}` (flag-shaped but wrong).
4. `esnp` vs `csaw` gives per-letter shifts 2,0,13,19 = c,a,n,t -> the video text is the Vigenere key. Decrypting the letters only
   (key index advances on letters, symbols pass through) with `cantfindit` yields `csaw{y0u_@lw@ys_kn0w_wh3r3_t0_l00k}` -
   readable leetspeak ("you always know where to look"), which confirms the key and the chain.

## Run
```
python solve_finders_keepers.py                      # dumps XMP blob + frame crop strip (finders_keepers_out/strip.png)
python solve_finders_keepers.py Y2FudGZpbmRpdA==     # base64 read from the frames -> plaintext + Vigenere of XMP blob
```
Reading the drifting text off the image was done by eye (OCR not attempted), so the solver takes that string as an argument.

## Caveats
- `cantfindit` was derived from the video before being compared with challenge.json's `flag` field, and has since been confirmed as the correct answer.
