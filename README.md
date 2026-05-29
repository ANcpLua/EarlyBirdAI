# Gods

Dynamic God Team discovery for Claude Code workflow and review skills.

This repository is a Claude Code plugin named `gods`. The primary command is:

```text
/gods:review
```

The plugin does not hard-code a pantheon. It reads a skill or workflow prompt, extracts review axes, embeds those axes
with candidate deity profiles, searches team sizes `k=4..16`, and writes the smallest powerful team that covers the
workflow without wasteful overlap.

## Commands

- `/gods:review <task-or-skill-path>` - discover and use a God Team for review.
- `/gods:nihil <target-scope>` - run the evaluated k=10 Nihil transformation workflow.
- `/gods:forge` - refine workflow axes or candidate god profiles.
- `/gods:evolve` - improve a previous run from its rejected gods and rejected sizes.
- `/gods:rank <task-or-skill-path>` - inspect scoring and rejected alternatives.

## Local Usage

Install dependencies when needed:

```bash
python3 -m pip install -r requirements.txt
```

Run the default thermo-nuclear review example:

```bash
python3 main.py
```

Run against a specific skill markdown file or inline task:

```bash
python3 main.py --skill examples/thermo-nuclear-code-quality-review.md
python3 main.py --skill "Review a Python refactor for architecture, deletion, type boundaries, and approval bar."
```

Validate the plugin shape and generated artifacts:

```bash
python3 scripts/validate_gods_pipeline.py
```

Test the plugin in Claude Code:

```bash
claude --plugin-dir .
```

Then invoke:

```text
/gods:review examples/thermo-nuclear-code-quality-review.md
```

## Outputs

The discovery run writes:

```text
results/god_team_scores.csv
results/god_team.json
visualizations/god_team_tsne.png
```

`results/god_team.json` contains the selected team, rejected gods, rejected team sizes, assigned workflow axes, and
coverage/separation metrics.

The JSON includes the command, selected gods, role assignments, score breakdowns, evidence notes, and any blocked
validations. The local pipeline uses deterministic TF-IDF vectors as a dry-run embedding backend, so no external API or
Qdrant service is required for validation.

## Model

The scoring model balances:

- semantic fit
- workflow coverage
- non-overlap
- mythic power
- name usability
- evidence score

t-SNE is only a visualization layer. It is not used as the final ranking metric.

See `SEMANTIC_MODEL.md` for the full model.
