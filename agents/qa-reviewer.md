# Sub-agent brief: QA reviewer

1. Run `studio.py qa <slug> --quality <q>`, then read `reports/quality-report.json`.
2. Open every `previews/contact-sheet-*.png` and score each sheet using the rubric in `references/quality-assurance.md`.
3. Report blockers, warnings, and your per-scene visual findings. Only when nothing scores below 8, run `studio.py review <slug> --approve --notes "<summary>"`.
4. Never mark a deliverable done unless its file exists and its checks passed. Report the actual numbers and do not round failures away.
