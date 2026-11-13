# Proof transcripts (autonomous solver + orchestration sessions)

Gzipped Claude Code session transcripts (`.jsonl.gz`), one per session. The six
category sessions ran autonomously in parallel tmux panes; orchestration/HITL
sessions drove setup, verification, and packaging. Category is assigned by the
dominant challenge-name frequency in each log (`gunzip -c <f> | less` to read).

| transcript | primary category | size(MB) | challenges referenced |
|---|---|---|---|
| `misc__0e07121a.jsonl.gz` | misc | 3.0 | 12345678, breach_zero_day, house_of_hollow_houses, keep_walking_forward, music_sec_dept |
| `web__113c6bc7.jsonl.gz` | web | 8.8 | 12345678, autobahn, breach_zero_day, copper_choir, csale, diamond_dogs, finders_keepers, flagchecker, ghost_in_the_machine, golf_heist, hells_bells, hemispheres, house_of_hollow_houses, juggler, keep_walking_forward, low_tide, machine_head, music_sec_dept, polly, saint_vespers, schrodingers_backup, secret_treaties, taking_on_the_temple, trustdinoidc |
| `forensics__174d8778.jsonl.gz` | forensics | 1.3 | breach_zero_day, ghost_in_the_machine, hemispheres, house_of_hollow_houses, keep_walking_forward, music_sec_dept, schrodingers_backup, secret_treaties |
| `crypto__2235af97.jsonl.gz` | crypto | 3.1 | breach_zero_day, finders_keepers, ghost_in_the_machine, hemispheres, keep_walking_forward, music_sec_dept, polly, schrodingers_backup, secret_treaties, taking_on_the_temple |
| `rev__3a73e524.jsonl.gz` | rev | 1.8 | 12345678, autobahn, breach_zero_day, keep_walking_forward, machine_head, music_sec_dept |
| `misc__408d5b67.jsonl.gz` | misc | 5.2 | 12345678, breach_zero_day, house_of_hollow_houses, keep_walking_forward, music_sec_dept |
| `pwn__8500a4c9.jsonl.gz` | pwn | 1.9 | breach_zero_day, copper_choir, diamond_dogs, flagchecker, golf_heist, hells_bells, keep_walking_forward, music_sec_dept, saint_vespers |
| `web__a23658e3.jsonl.gz` | web | 1.9 | 12345678, breach_zero_day, csale, flagchecker, golf_heist, juggler, keep_walking_forward, low_tide, music_sec_dept, trustdinoidc |
| `misc__e8319214.jsonl.gz` | misc | 10.9 | 12345678, breach_zero_day, golf_heist, house_of_hollow_houses, keep_walking_forward, music_sec_dept |
| `rev__4ab23db4.jsonl.gz` | rev | 6.3 | 12345678, autobahn, breach_zero_day, copper_choir, csale, diamond_dogs, finders_keepers, flagchecker, ghost_in_the_machine, golf_heist, hells_bells, hemispheres, house_of_hollow_houses, juggler, keep_walking_forward, low_tide, machine_head, music_sec_dept, polly, saint_vespers, schrodingers_backup, secret_treaties, taking_on_the_temple, trustdinoidc |
| `orchestration-mixed__8bd4de6c.jsonl.gz` | orchestration-mixed | 0.5 | — |
| `orchestration-mixed__a9a173db.jsonl.gz` | orchestration-mixed | 0.8 | — |
| `web__4ce97508.jsonl.gz` | web | 6.7 | 12345678, breach_zero_day, csale, finders_keepers, flagchecker, golf_heist, house_of_hollow_houses, juggler, keep_walking_forward, low_tide, music_sec_dept, secret_treaties, trustdinoidc |
