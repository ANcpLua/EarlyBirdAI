# Semantic Model: Dynamic God Team Discovery

## Purpose

This project does not define a fixed subagent team.

It defines a dynamic God Team discovery system. Given a skill, workflow, or review prompt, the system finds the
smallest powerful pantheon that semantically covers the work without redundant roles.

The goal is to evolve a skill into a Claude Code plugin called `gods`, where each invocation can derive or reuse the
best-fitting god team for the task.

## Core Idea

The God Team is not hard-coded.

The system must:

1. Read the skill markdown.
2. Extract its core workflow axes.
3. Build candidate deity profiles.
4. Embed both workflow axes and deity profiles.
5. Evaluate candidate pantheon sizes.
6. Score each god by semantic fit, mythic power, role coverage, non-overlap, and name usability.
7. Select the smallest team that covers the skill well.
8. Produce a machine-readable God Team plan.
9. Use t-SNE only as a visualization and sanity-check layer.

## Plugin Name

```text
Plugin: gods
Primary command: /gods:review
Evolution command: /gods:evolve
Ranking command: /gods:rank
Forge command: /gods:forge
```

## Definitions

A `god` is not a static subagent.

A god is a named dynamic workflow force with:

* a mythological identity
* a semantic domain
* a power score
* a practical workflow responsibility
* assigned skill axes
* overlap penalties against other gods
* evidence for why the name fits

A `God Team` is the selected pantheon for one skill or task.

A `pantheon size` is the number of gods selected for the workflow.

## Dynamic Discovery Pipeline

```text
skill markdown
  -> workflow-axis extraction
  -> candidate deity corpus
  -> embeddings
  -> role-fit scoring
  -> pantheon-size search
  -> cluster validation
  -> t-SNE visualization
  -> God Team selection
  -> plugin command output
```

## Workflow Axis Extraction

For each skill, extract core axes such as:

```text
structural_simplification
code_judo_deletion
spaghetti_detection
file_size_boundary
abstraction_quality
type_boundary_cleanliness
canonical_layer_ownership
orchestration_atomicity
output_prioritization
tone_enforcement
approval_bar
maintainability_regression_blocking
unnecessary_abstraction_rejection
generic_linting_rejection
evidence_grounding
ambitious_review_scope
```

The extracted axes become the semantic target space.

The local validation path uses deterministic TF-IDF vectors as the embedding backend so the plugin can be tested without
external API credentials or a vector database. A production embedding backend can replace that layer without changing the
God Team output schema.

## Candidate God Profile

Each candidate god must be represented as structured text before embedding.

Example:

```json
{
  "name": "Shiva",
  "pantheon": "Hindu",
  "domains": ["destruction", "transformation", "renewal", "cosmic dissolution"],
  "workflow_affinity": ["delete complexity", "remove obsolete structure", "break false stability"],
  "mythic_power_score": 0.98,
  "name_usability_score": 0.90,
  "role_hint": "complexity deletion",
  "evidence_notes": "Hindu deity associated with destruction and transformation, fitting renewal through deletion."
}
```

## Scoring Model

Each candidate god receives:

```text
semantic_fit_score
mythic_power_score
workflow_coverage_score
non_overlap_score
name_usability_score
evidence_score
```

Final score:

```text
final_score =
  0.40 * semantic_fit_score
+ 0.20 * workflow_coverage_score
+ 0.15 * non_overlap_score
+ 0.15 * mythic_power_score
+ 0.05 * name_usability_score
+ 0.05 * evidence_score
```

## Pantheon Size Search

Test team sizes:

```text
k = 4..16
```

For each `k`, compute:

```text
team_coverage
team_separation
team_power
team_overlap_penalty
team_name_quality
team_complexity_penalty
```

Select the smallest `k` whose score is within an acceptable margin of the best score.

Rule:

```text
Prefer the smallest team that covers the workflow.
Do not add gods for style if they do not reduce ambiguity or improve coverage.
```

## t-SNE Role

t-SNE is visualization only.

Use it to inspect whether gods, workflow axes, and selected teams form intuitive neighborhoods.

Do not use t-SNE coordinates as final proof of power, rank, or correctness.

## Cluster Validation

Use silhouette score and bootstrap stability to estimate whether a team size is semantically clean.

High silhouette means the selected roles are more separated.

Near-zero silhouette means the team has overlapping or blurry responsibilities.

Negative silhouette means the team assignment is likely wrong.

## Expected Outputs

The system should write:

```text
results/god_team_scores.csv
results/god_team.json
visualizations/god_team_tsne.png
```

## `results/god_team.json`

```json
{
  "plugin": "gods",
  "skill": "thermo-nuclear-code-quality-review",
  "skill_name": "thermo-nuclear-code-quality-review",
  "command": "/gods:review",
  "optimal_team_size": 7,
  "selected_gods": ["Athena"],
  "selection_reason": "Smallest team with strong coverage, high role separation, and low overlap.",
  "team": [
    {
      "god": "Athena",
      "role": "strategic architecture judgment",
      "semantic_fit_score": 0.0,
      "workflow_coverage_score": 0.0,
      "non_overlap_score": 0.0,
      "mythic_power_score": 0.0,
      "name_usability_score": 0.0,
      "evidence_score": 0.0,
      "final_score": 0.0,
      "assigned_axes": [],
      "evidence_notes": []
    }
  ],
  "role_assignments": {},
  "score_breakdowns": {},
  "rejected_team_sizes": [],
  "blocked_validations": [],
  "notes": []
}
```

## Example God Team for Thermo-Nuclear Code Quality Review

This is an initial hypothesis only. The final team must be selected by scoring.

```text
Athena      -> strategic architecture judgment
Shiva       -> deletion of accidental complexity
Hephaestus  -> implementation structure and craft
Ma'at       -> truth, evidence, approval bar
Hermes      -> routing and orchestration clarity
Janus       -> boundary and compatibility review
Odin        -> deep investigation of hidden causes
```

Possible optional gods:

```text
Apollo      -> clarity, diagnostic light, readable expression
Thoth       -> documentation, records, precise language
Ares        -> aggressive blocker enforcement
Hades       -> dead-code and hidden-debt excavation
Vishvakarma -> system craftsmanship and construction
```

## Acceptance Criteria

A valid run must answer:

1. What is the optimal team size?
2. Which gods were selected?
3. Which skill axes does each god cover?
4. Which gods were rejected and why?
5. Which team sizes were rejected and why?
6. Did t-SNE visually support the separation?
7. Did silhouette/stability support the selected size?
8. Is the selected team smaller than an equally powerful but redundant team?

## Hard Rules

* Do not preselect the final pantheon manually.
* Do not confuse gods with static subagents.
* Do not use t-SNE as the final ranking metric.
* Do not optimize only for mythological power.
* Do not optimize only for semantic role fit.
* Always balance semantic fit, workflow coverage, mythic power, role separation, and practical name usability.

## Current Best Hypothesis For The Thermo-Nuclear Review Skill

For the thermo-nuclear review skill, test `k=4..16`; the initial expected winner is probably 7 gods, not 5 or 9.

Why 7?

```text
3 gods = too compressed; loses review specificity
5 gods = workable, but likely merges architecture/type/orchestration too much
7 gods = probably best balance
9 gods = expressive, but likely redundant
16 gods = too much overhead for one skill unless every role reduces ambiguity
```

Initial 7-god hypothesis:

| God        | Workflow force          | Why it fits this skill                             |
|------------|-------------------------|----------------------------------------------------|
| Athena     | Architecture judgment   | Strategy, design quality, clean structure          |
| Shiva      | Complexity deletion     | Delete accidental complexity and dead abstractions |
| Hephaestus | Craft implementation    | Build maintainable structure, concrete fixes       |
| Ma'at      | Approval bar / truth    | Evidence, correctness, strict judgment             |
| Hermes     | Routing / orchestration | Detect wrong layer, wrong flow, sequencing issues  |
| Janus      | Boundaries              | API, compatibility, type and module boundaries     |
| Odin       | Deep investigation      | Hidden causes, non-obvious simplification paths    |

This is a hypothesis, not a fixed team. The final team must be selected by the scoring run.
