# Thermo-Nuclear Code Quality Review

Review code with a strict approval bar and lead with concrete risks.

Core review axes:

- Structural simplification and fewer moving parts.
- Code-judo deletion: small deletions that redirect the problem instead of adding force.
- Spaghetti growth detection across tangled control flow and hidden coupling.
- File-size limits and module responsibility boundaries.
- Abstraction quality: reject indirection that hides rather than removes complexity.
- Type boundaries, API contracts, and schema cleanliness.
- Canonical-layer ownership and source-of-truth protection.
- Orchestration atomicity, routing clarity, and sequencing of workflow steps.
- Output expectations: findings first, ordered by severity, with concise evidence.
- Tone enforcement: direct, useful, non-performative review language.
- Approval bar: correctness, verification, and no unsupported claims.
- Maintainability regression blocking when a change makes future work harder.
- Unnecessary abstraction rejection for duplicate layers and speculative extension points.
- Generic linting rejection: do not substitute style nits for structural judgment.
- Evidence grounding with precise code facts and explicit uncertainty.
- Ambitious review scope when the root cause lives outside the local edit.
