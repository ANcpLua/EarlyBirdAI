---
description: Forge or refresh candidate god profiles and workflow axes before running God Team discovery.
---

# Gods Forge

Use this command to refine the candidate deity corpus or the workflow-axis vocabulary before discovery.

Read `SEMANTIC_MODEL.md`, `data/candidate_gods.json`, and `data/workflow_axes.json`. Keep profiles structured and
evidence-backed. Do not add a god only because the name is stylish; add it only when it covers a workflow force that the
existing corpus handles poorly.

After changes, run:

```bash
python3 scripts/validate_gods_pipeline.py
```
