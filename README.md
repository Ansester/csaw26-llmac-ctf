# CSAW 2026 LLM CTF Attack Competition

**SegfaultObservers · First place, MENA region**

Our team was [Ashmit Mukherjee](https://github.com/Ansester), [Akshith Karthik](https://github.com/Ak1016-stack), Maryam Emaan Fiyaz, and [Aadil Chasmawala](https://github.com/Aarz1401).

This repository contains our work for the [November finals](https://csaw.io/competition/llm-ctf-attack-competition) at NYU Abu Dhabi. The organizers gave finalists the 2026 challenge set after a separate qualifying submission using challenges from the 2025 database.

We assigned one Claude Code agent to each of six challenge categories. For the hardest problems we tried competing approaches and asked a separate agent to check the proposed solution. In one audio challenge, the check showed that the decoder could reproduce a known part of the flag without deriving it from the recording. We left that challenge unsolved.

## Flag recoveries

We recovered flags for 22 of 23 challenges. The organizers clarified that we could use the reference files supplied with the challenges. Web search was prohibited. Twelve recoveries used a challenge author’s solver, generator, or walkthrough.

Our [challenge manifest](MANIFEST.md) also identifies two challenges where a solving prompt contained the answer, including one of those twelve. On `music_sec_dept`, a second model found a solution method through web search during the attempt. We disclosed that case in our submission. The table gives our recovery count by category.

| Category | Flags recovered | Code and write-ups |
| --- | --- | --- |
| Cryptography | 4 of 4 | [Crypto](solutions/crypto/) |
| Forensics | 4 of 4 | [Forensics](solutions/forensics/) |
| Miscellaneous | 2 of 3 | [Miscellaneous](solutions/misc/) |
| Binary exploitation | 3 of 3 | [Pwn](solutions/pwn/) |
| Reverse engineering | 3 of 3 | [Reverse engineering](solutions/rev/) |
| Web security | 6 of 6 | [Web](solutions/web/) |

## Submission materials

- [Competition submission](SUBMISSION.md) and [our approach](submission/APPROACH.md)
- [Per-challenge disclosures](submission/DISCLOSURE.md) and [corrections to the original write-ups](submission/ERRATA.md)
- [Flag index](solutions/FLAGS.md)
- [Agent session transcripts](submission/transcripts/) and [category prompts](prompts/)
- [Run time and token use](submission/EFFICIENCY.md)
