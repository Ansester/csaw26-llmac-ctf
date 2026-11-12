# breach_zero_day

**Flag:** `csaw{RELAYSHELL_WINDEFEND_FORESTTIGER}`

Run: `python3 solve_breach_zero_day.py [dir-with-fenwick_*]` (artifacts bundled in `breach_zero_day_artifacts/`, stdlib only).

## 1. C2 indicator — pcap
- Two plaintext `POST /api/sync` requests (everything else is TLS noise / benign telemetry):
  - `backup-vault.fenwick.local` -> `{"id":"QkFDS1VQU1ZD"}` = `BACKUPSVC` at 23:58:10 UTC. Single connection, internal host, the same minute as the NightlyBackup task / "Fenwick Backup Agent" in the event log.
  - `docs-fenwick-portal.com` -> id split across two TCP segments (`UkVMQV` + `lTSEVMTA==`); reassembled by seq = `RELAYSHELL`, POST at 01:13:42 UTC.
- Disambiguation by time: internal monitor 10.14.0.9 checks in every ~5 min (348 packets) from 18:00:00, last at 01:09:47 UTC, then never again. docs-fenwick-portal.com's 73 connections start at 01:13:42 with a ~4 min beacon (regular from 01:14:25) through the end of the capture (05:58); the BACKUPSVC host never appears again. => **RELAYSHELL**.

## 2. Service — event log
- Service Control Manager "stopped" events for security services:
  - 20:12:07 WinDefend stopped, running again 37 s later (benign)
  - 23:58:48 SecurityHealthService stopped, 5 s after driver `BkupAgent64.sys` installed — ties to the backup agent/BACKUPSVC decoy, ~71 min *before* the gap
  - **01:14:20 WinDefend stopped, 5 s after kernel driver `Afd4Eop12` (Afd4Eop12_x64.dll, "AFD EoP") was installed (01:14:15)**, 273 s after the monitoring gap opens; no restart until a later separate stop/start pair
  - 03:41:52 WinDefend stopped, running 29 s later (benign)
- => **WinDefend**.

## 3. Backdoor — memdump
- Memory strings are stored reversed. Of ~45 random upper-case strings only four reverse into words: `ELUDOMDUF`->FUDMODULE, `EGDEHREPPOC`->COPPERHEDGE (complete names, decoys), and two fragments `TSEROF`->FOREST (addr 0x7ff60011a103) and `REGIT`->TIGER (0x7ff6000f02ed).
- Reading the dump back-to-front (consistent with strings being reversed) places FOREST before TIGER => **FORESTTIGER**.
- Honest caveat: the memdump has no timestamps, so unlike parts 1-2 this choice is not time-correlated; it rests on the structure (two complete names vs. deliberately fragmented/scattered pieces) and on fragment ordering. The word list in the solver (FOREST/TIGER/MODULE/COPPER/HEDGE/FUD) was assembled by eye from the reversed strings.

## Verification
Solver run in this session derives all three parts from the artifacts and prints the flag. `challenge.json` / README not used as the source; they agree as a post-hoc check.
