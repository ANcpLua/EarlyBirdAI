---
description: Rank candidate gods and rejected pantheon sizes for a skill without treating any team as preselected.
---

# Gods Rank

Use this command to inspect why a team won and why other gods or team sizes lost.

Run:

```bash
python3 main.py --skill "$ARGUMENTS"
```

Then summarize `results/god_team_scores.csv` and `results/god_team.json`: selected gods, rejected gods, rejected team
sizes, coverage gaps, and overlap penalties.
