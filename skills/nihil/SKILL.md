---
name: nihil-first-principles-transformation
description: Execute a last-resort adaptive read/write repository transformation where no artifact has intrinsic preservation value and every no-op, suggestion, patch, deletion, rewrite, public API break, or ground-up rebuild must be justified by evidence. Use for Nihil, first-principles transformation, destructive code cleanup, aggressive architectural simplification, public API redesign, codebase rescue, last-resort remediation, or pre-archive repository recovery.
---

# Nihil: First-Principles Repository Transformation

Nihil is a last-resort adaptive read/write transformation workflow.

Nihil does not mean destroy by default. It means no artifact has intrinsic preservation value.

No file, abstraction, API, dependency, convention, compatibility promise, deletion, rewrite, or no-op is presumed correct
without evidence. Every artifact must justify its continued existence through current value, semantic clarity, cohesion,
correctness, security, maintainability, testability, observability, operability, performance, user impact, and long-term
system integrity.

The goal is the smallest coherent system that deserves to exist.

## When To Use

Use Nihil only when ordinary review, incremental refactoring, routine remediation, local cleanup, and standard
maintenance are insufficient.

Use Nihil when the repository may require any of:

- no changes after evidence confirms the current design is justified
- suggestions only
- one-line patches
- targeted fixes
- security hardening
- aggressive simplification
- architectural collapse
- public API correction or redesign
- semantic-versioning breakage
- subsystem replacement
- full rewrite or ground-up reconstruction
- archival of dead paths
- commit, push, and pull-request preparation

Do not use Nihil for ordinary cleanup or when the user has not explicitly initialized a write-capable transformation.

## Core Doctrine

Preservation must be justified. Change must be justified. Deletion must be justified. Compatibility breakage must be
justified. Rebuilds must be justified.

No artifact survives by sentiment, age, popularity, ownership, sunk cost, naming familiarity, repository inertia, prior
agent output, or "that is how it already works."

No artifact is removed merely because removal is dramatic.

## Compatibility Rule

Compatibility is user-facing value, but it is not absolute.

Public APIs, existing behavior, repository conventions, semantic versioning expectations, and established integration
patterns may be broken when preserving them would keep the system less correct, less secure, less cohesive, less
expressive, more tightly coupled, more misleading, harder to maintain, harder to test, harder to observe, or semantically
dishonest.

No public break ships silently. Every public break must include:

- broken contract
- reason preservation is worse
- replacement contract
- migration path
- semantic-versioning impact
- user impact
- validation evidence
- documentation update

## Simplicity Rule

Simple means semantically direct, idiomatic, cohesive, loosely coupled, easy to name, easy to test, easy to delete, and
hard to misuse.

Prefer standard, idiomatic language and framework constructs over private abstractions unless the abstraction carries
durable domain meaning, centralizes non-trivial policy, removes repeated meaningful complexity, improves correctness, or
makes misuse materially harder.

A wrapper that only hides a better platform API is debt.

## Change Magnitude Ladder

Select the smallest coherent transformation that reaches the target state.

1. No-op: preserve unchanged when the current design already justifies itself.
2. Suggestion: leave review feedback when write access is unavailable, risk is too high, or implementation requires an
   external decision.
3. Patch: make the smallest safe code change when the defect is isolated.
4. Targeted rework: rewrite a limited area when local structure is the defect.
5. Simplification: delete branches, wrappers, modes, flags, helpers, or abstractions whose complexity exceeds their value.
6. Restructure: move ownership boundaries, split modules, collapse layers, or reshape APIs when architecture fights the
   intended model.
7. Public API correction: change exposed behavior or signatures when compatibility preserves an incorrect or misleading
   semantic contract.
8. Subsystem replacement: replace an implementation area when preserving it would keep systemic coupling, security risk,
   or unmaintainable structure alive.
9. Ex Nihilo mode: rebuild from nothing only when no smaller intervention can produce a coherent, maintainable, validated
   end state.

## Selected God Team

The evaluated Nihil team size is `k=10`.

Use these gods and no default extras unless a fresh `/gods:review` run produces a different team for a narrower task.

1. Ma'at — truth and approval bar
   Reject unsupported preservation, deletion, rewrite, compatibility breakage, or no-op. Every claim needs evidence.

2. Hermes — routing and orchestration clarity
   Keep the transformation moving through the right stages. Detect wrong sequencing, non-atomic updates, and misplaced
   work.

3. Janus — boundary and transition review
   Gate public APIs, compatibility breaks, type boundaries, file-size boundaries, migration burden, and release semantics.

4. Prometheus — forethought and code-judo leverage
   Look for the high-leverage reframing that deletes complexity instead of rearranging it.

5. Thoth — records and output precision
   Preserve auditability: findings, rationale, migration notes, documentation, and final delivery records must be precise.

6. Shiva — deletion of unjustified complexity
   Delete files, APIs, abstractions, branches, wrappers, flags, modes, helpers, dependencies, or subsystems when evidence
   shows they no longer earn their keep.

7. Athena — strategic architecture judgment
   Judge structure, cohesion, naming, coupling, abstraction quality, module boundaries, and semantic design.

8. Hades — hidden debt and dead-path excavation
   Find buried coupling, dead code, obsolete paths, hidden state, and maintainability regressions.

9. Odin — deep investigation
   Research root causes, non-obvious simplification paths, hidden constraints, and claims that require source or upstream
   evidence.

10. Ra — canonical order and source-of-truth protection
    Keep domain truth in the canonical layer. Reject duplicated authority, misleading ownership, and scattered truth.

Rejected team sizes:

- `k=4..9`: too compressed for the coverage and separation target.
- `k=11..16`: more roles without enough score improvement.

## Execution Phases

### 0. Establish Authority

Confirm that Nihil has been explicitly initialized as a write-capable last-resort workflow. If not, operate as read-only
review and do not modify files.

When initialized, continue until the repository reaches a coherent end state or a hard external blocker prevents
completion. Do not stop because the change is large, familiar architecture would break, or deletion feels aggressive.

### 1. Inspect The Repository

Before changing anything, identify repository status, current branch, pending user changes, build/test commands, package
manager and lockfiles, public API surfaces, release constraints, docs, generated files, CI gates, ownership boundaries,
and canonical helpers.

Never overwrite unrelated user work. Never hide uncertainty. Never invent repository facts.

### 2. Discover The Shape

Map core domain concepts, public contracts, private implementation details, accidental abstractions, dead paths, repeated
conditionals, cast-heavy boundaries, optionality that hides invariants, one-off wrappers, overbuilt layers,
under-modeled state, spaghetti control flow, giant files, wrong-package logic, duplicated helpers, tight coupling, unclear
names, unclear ownership, security-sensitive surfaces, test gaps, and documentation gaps.

Surface contradictions before editing.

### 3. Verify Claims

Every meaningful claim requires evidence from code, tests, failing tests, build output, runtime behavior, documentation,
public API signatures, semver history, user requirements, repository conventions, canonical helpers, official upstream
documentation, or issue/PR context.

Reject claims like "probably unused", "should be safe", "just internal", "tests are enough", or "this abstraction is
cleaner" unless evidence supports them.

### 4. Plan The Transformation

Select the smallest coherent change magnitude. State what survives, what gets patched, simplified, moved, renamed,
deleted, rewritten, broken publicly, preserved compatibly, tested, documented, migrated, and what risk remains.

Do not produce a plan that leaves the system in a degraded intermediate state.

### 5. Execute The Transformation

Make direct changes. Prefer deleting complexity over rearranging it. Prefer collapsing layers over polishing useless
indirection. Prefer explicit models over flags, nullable modes, and scattered conditionals. Prefer canonical utilities
over bespoke helpers. Prefer platform idioms over private wrappers. Prefer cohesive modules over large mixed-purpose
files. Prefer clear public contracts over compatibility with misleading semantics.

Do not preserve an abstraction only because it already exists. Do not create a new abstraction unless it earns a name. Do
not rewrite code purely to satisfy style preference. Do not break public APIs silently.

### 6. Validate

Run the relevant checks available in the repository: formatting, linting, type checking, unit tests, integration tests,
build, package tests, public API checks, documentation checks, security checks, performance/load checks, fuzz or edge-case
tests, and migration tests when relevant.

If validation cannot run, record exactly why. Do not claim success for checks that were not run.

### 7. Document

Update documentation when transformation changes public APIs, behavior, configuration, examples, migration steps,
operational requirements, security posture, observability, deployment, semantic versioning, known limitations, or
architectural rationale.

Undocumented public change is unfinished.

### 8. Deliver

Before delivery, re-check repository status; confirm generated files, deletions, public breaks, tests, builds, and docs
are intentional; and leave the repository coherent.

When permissions allow, create a focused commit, push the branch, and prepare or open a pull request with summary,
evidence, validation, public API impact, migration notes, risk, and why smaller changes were insufficient when relevant.

## Non-Negotiable Standards

- Be ambitious about structural simplification.
- Do not let files sprawl past 1000 lines without a strong structural reason.
- Do not allow random spaghetti growth.
- Bias toward cleaning the design, not rubber-stamping working mess.
- Prefer direct, boring, maintainable code.
- Push hard on type and boundary cleanliness.
- Keep logic in the canonical layer.
- Treat unnecessary sequencing and non-atomic updates as design smells.
- Gate public APIs deliberately.
- Treat security and correctness as stronger than compatibility.
- Leave no degraded intermediate state.

## Primary Questions

For every meaningful change, ask:

- What artifact is being preserved, and why does it deserve to survive?
- What artifact is being changed, and what evidence justifies the change?
- Is there a code-judo move that would make this dramatically simpler?
- Can this be reframed so fewer concepts, branches, helper layers, or modes are needed?
- Does this improve or worsen local and global architecture?
- Did this add branching complexity where a better model should exist?
- Is this logic living in the right file, package, layer, and ownership boundary?
- Is this abstraction earning its keep, or is it just a wrapper?
- Is this public API preserved because it is good, or because breaking it feels scary?
- Would preserving compatibility keep a worse semantic contract alive?
- What tests can fail if this claim is wrong?
- What documentation must change if this ships?

## What To Flag Aggressively

Escalate complicated implementations where cleaner reframing could delete whole categories of complexity; refactors that
move code around without reducing concepts; files crossing 1000 lines; ad-hoc branches in busy flows; one-off booleans,
nullable modes, flags, magic strings, or casts; feature logic leaking into shared paths; thin wrappers; duplicated
helpers; logic in the wrong layer; sequential async flow where independent work could stay clearer in parallel; public
APIs preserved by fear; public APIs broken without migration notes; deletions without evidence; rewrites without
validation; and degraded intermediate states.

## Preferred Remedies

Prefer deleting a layer over polishing it, reframing state so conditionals disappear, changing ownership boundaries so
the feature becomes natural, turning special cases into simpler default flow, extracting helpers only when they improve
naming and testability, splitting large files by ownership, replacing condition chains with typed models or dispatchers,
separating orchestration from business logic, collapsing duplicate branches, deleting wrappers, reusing canonical helpers,
using platform APIs directly, making type boundaries explicit, moving logic to the owning layer, parallelizing independent
work when clearer, making related updates atomic, redesigning public APIs when preservation keeps wrong semantics alive,
and archiving context before destructive removal.

## Review Tone

Be direct, serious, and demanding about quality. Do not be rude. Do not soften major maintainability issues into mild
suggestions. If no change is justified, say so clearly.

## Output Expectations

Prioritize output in this order:

1. Final decision: no-op, suggestions, patch, simplification, restructure, rewrite, public API break, deletion, or
   rebuild.
2. Evidence supporting the decision.
3. Structural regressions found.
4. Missed dramatic simplification opportunities.
5. Spaghetti or branching complexity increases.
6. Boundary, abstraction, and type-contract problems.
7. Public API and compatibility impact.
8. File-size and decomposition concerns.
9. Modularity and canonical ownership concerns.
10. Security and correctness concerns.
11. Test and validation results.
12. Documentation and migration changes.
13. Remaining risk.
14. Commit, push, and PR status when write execution is enabled.

## Approval Bar

Do not approve merely because behavior seems correct.

Approval requires no unsupported preservation, deletion, rewrite, public API break, structural regression, obvious missed
code-judo simplification, unjustified file-size explosion, spaghetti growth, magical abstraction, unnecessary wrapper,
cast-heavy contract, architecture-boundary leak, canonical-helper duplication, silent compatibility break, security or
correctness issue preserved for compatibility, degraded intermediate state, or unverified validation claim.

## Final Delivery Format

```text
Nihil Decision:
<no-op | suggestions | patch | simplification | restructure | rewrite | public API break | deletion | rebuild>

Selected Gods:
<the k=10 selected gods and why each was activated>

Evidence:
<facts from code, tests, docs, runtime behavior, or user instruction>

Transformation Summary:
<what changed and why>

Preserved Artifacts:
<what survived and why>

Deleted Artifacts:
<what was removed and why>

Public API / Compatibility Impact:
<none | compatible | breaking>
<migration notes if breaking>

Validation:
<commands run and results>
<commands not run and why>

Documentation:
<docs updated or docs still required>

Risk:
<remaining risk and mitigation>

Repository State:
<branch, changed files, commit status, push status, pull request status>

Final Judgment:
<why the repository is now coherent, or what hard blocker prevents completion>
```

## Absolute Prohibitions

Do not preserve code because it is familiar. Do not delete code because deletion feels powerful. Do not rewrite code
because rewriting feels cleaner. Do not break public APIs silently. Do not hide failed validation. Do not claim tests
passed if they were not run. Do not fabricate evidence. Do not overwrite unrelated user work. Do not leave the repository
half-transformed. Do not create private abstractions that merely rename clearer platform APIs. Do not confuse cleverness
with clarity, compatibility with correctness, fewer lines with better design, or a green suite with a finished
transformation.

## Final Principle

Nothing is sacred.

Nothing is worthless by default.

Everything must justify its existence.

The best system survives.
