---
description: Discover the smallest powerful God Team for a review task or skill markdown, then use that team to guide a strict code-quality review.
---

# Gods Review

Use this command for dynamic review-team discovery. `$ARGUMENTS` may be a skill path, markdown file, or free-form review
task.

Run the local discovery pipeline first:

```bash
python3 main.py --skill "$ARGUMENTS"
```

Then read `results/god_team.json` and use the selected team as workflow forces for the review. Do not treat the gods as
static subagents. If the selected team looks redundant, rerun with a clearer skill/task input before reviewing.

Review output should lead with blocking findings, then important findings, then the selected God Team summary.
