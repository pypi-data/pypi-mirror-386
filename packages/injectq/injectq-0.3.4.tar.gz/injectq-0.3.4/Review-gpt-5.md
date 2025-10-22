# InjectQ — Senior engineer review

## Executive summary

InjectQ is a mature, thoughtfully designed Python dependency-injection library that targets modern async+sync Python applications. It implements a full DI stack: registry, resolver, container, multiple scopes (singleton/transient/thread-local/request/action), lifecycle/resource management (sync and async), diagnostics (profiler, validator, visualizer), testing helpers, and useful integrations (FastAPI and TaskIQ). The codebase shows practical engineering trade-offs: pragmatic API ergonomics (decorators like `@singleton` / `@inject`), careful async-awareness (contextvars and hybrid locks), and good test coverage across features.

Overall judgment: strong foundation with advanced features. The main risks are complexity in hybrid sync/async locking and scope handling, a few minor API/typing inconsistencies, and places where documentation and guarded tests could better explain subtle behavior (particularly around hybrid usage and threading). Addressing these would significantly reduce cognitive load for adopters and reduce the risk of subtle runtime bugs.

## What I inspected

- Core container and registry: `core/container.py`, `core/registry.py`
- Resolver and thread-safe variant: `core/resolver.py`, `core/thread_safe_resolver.py`
- Scopes and async scopes: `core/scopes.py`, `core/async_scopes.py`
- Thread/async safety primitives: `core/thread_safety.py`
- Decorators and resource management: `decorators/inject.py`, `decorators/resource.py`, `decorators/singleton.py`
- Diagnostics: `diagnostics/profiling.py`, `diagnostics/validation.py`, `diagnostics/visualization.py`
- Integrations: `integrations/fastapi.py`, `integrations/taskiq.py`
- Components & modules: `components/*`, `modules/base.py`
- Utilities and types: `utils/*`
- Tests across `tests/` to understand expected behavior and patterns.

I purposely focused on design, correctness-sensitive areas (locking, scopes, resolver), API ergonomics, and integration surface.

## Strengths

- Feature completeness: container, multiple scopes (including request/action), lifecycle-managed resources, decorator sugar, and diagnostics are all present and coherent.
- Async-aware design: uses contextvars for async scopes, provides both sync and async lifecycle hooks, and offers hybrid locks to handle mixed sync/async scenarios.
- Testing and ergonomics: `testing` utilities and override context managers make it easy to test code that depends on the container. Decorator-based registration reduces ceremony for most use-cases.
- Diagnostics: profiler, validator and visualizer are powerful for debugging dependency graphs, startup order, and cycles.
- Integration adapters: FastAPI and TaskIQ adapters are well aligned with framework idioms (FastAPI Depends compatibility, request middleware attaching contextvar container).

## Areas for improvement (high-level)

1. Complexity & subtle invariants in hybrid sync/async locking and scopes
	- The combination of `HybridLock`, thread-local storage and contextvars creates many valid execution paths. That surface is inherently tricky and can lead to deadlocks or unexpected behavior if used incorrectly (e.g., calling sync APIs inside an event loop that expects async locks or mixing thread-local and contextvar-scoped state without clear guidelines).

2. Documentation and guidance for hybrid usage
	- There are many valid ways to configure the container (sync-only, async scopes, hybrid). The README and API docs should include a short matrix describing recommended configurations for common hosting scenarios (pure-sync, pure-async, hybrid server + background threads, FastAPI worker model) and explicit guidance about which functions are safe to call from which context.

3. Typing and ergonomic rough edges
	- A few places reference aliases or types that are not perfectly consistent (e.g., the `Inject` proxy and mentions of `InjectType` surfaced during inspection). Strengthening type hints and small mypy/pyright CI runs would improve DX.

4. Validation & pre-start checks
	- The validation utilities are present and valuable. I recommend a stronger "pre-flight" mode that can be opt-in at container compile/install time to fail fast for production deployments (e.g., enforce no circular deps across installed modules and ensure resources with async `__aexit__` get the right lifecycle path).

5. Clearer failures and error messages
	- When resolution fails, the existing exceptions are helpful but could carry richer diagnostic metadata (call stack of resolution, requested binding chain, and suggestion hints). This makes production debugging much faster.

## Concrete, prioritized recommendations

Priority: P0 (high)
- Add a short compatibility & usage doc page named "Sync vs Async usage" that describes recommended container setup for three common cases (sync app, async app, hybrid app with background threads). Include a summary table of which container methods are safe in sync/async contexts and examples.
- Add stronger runtime assertions in critical paths to prevent incorrect hybrid usage (e.g., detect calling async-scope-only APIs from a plain sync context and produce a clear exception explaining the mismatch).

Priority: P1 (medium)
- Improve resolution error payloads: attach the resolution path (service keys visited) and show nearest cycles or missing binding hints.
- Tighten typing across public API surfaces. Run mypy/pyright in CI, or add a typed-check GitHub Action. Fix the small inconsistencies found in `utils` and decorator helpers.
- Add a `container.compile()` or `container.validate_all()` step that fails early for common misconfigurations; expose a flag for strict mode in production.

Priority: P2 (low)
- Expand the diagnostics to include a runtime health check endpoint (or a CLI script) that can produce an easily consumable JSON report for running systems.
- Consider small ergonomics: `ContainerBuilder` fluent helper for programmatic configuration; optional lightweight DSL to declare modules.

## Safety, concurrency and correctness notes

- The hybrid locking approach is pragmatic and reasonable, but it's a brittle area. A few suggestions:
  - Add more unit tests that simulate mixed threading + asyncio usage and stress test common operations (bind/get/clear scope) under concurrency.
  - Document that lock acquisition order must be preserved (if there are multiple internal locks) or centralize locks to avoid double-lock deadlocks.
  - Consider exposing a runtime mode that enforces single execution model (sync-only or async-only) to get safety when hybrid behavior isn't needed.

## Tests, CI and quality gates

- The repository already contains many tests. Ensure CI runs the test matrix with:
  - Python versions you support (3.8+ or 3.9+ depending on target)
  - Mypy/pyright type checks
  - Linting (flake8/ruff) with explicit rules for public API naming and docstring coverage for exported symbols

## Documentation and examples

- Add a small page with migration/advanced-pattern examples: mixing container with frameworks (FastAPI), background workers, and using `override` in tests. Show a real-world integration example that uses request-scoped dependencies.
- Show explicit lifecycle examples for async-managed resources (setup/teardown) in both application and test contexts.

## Code-style and maintainability

- Keep API stability for public symbols in `__all__`. Consider adding a deprecation policy in docs for future changes.
- Consider splitting very large files (if any) into smaller focused modules if you see cognitive complexity increasing (the current breakup looks reasonable but watch for growth in `container.py`/`resolver.py`).

## Quick wins (small PRs to improve DX)

- Add a short FAQ section in README for common errors (e.g., "Why do I get a CircularDependencyError?").
- Add examples that demonstrate: testing with `override`, using `Inject[...]` proxy, registering providers that return async generators, and integrating with FastAPI request lifecycle.
- Add a CI job for type checking and a targeted concurrency test suite (small runner that spawns threads + event loop to exercise hybrid code paths).

## Suggested roadmap / next steps

1. Publish a short "Sync vs Async" doc and add a runtime check for common misuse (P0).
2. Add richer resolution diagnostics and near-term type fixes (P1).
3. Harden concurrency tests and add CI typed checks (P1).
4. Expand docs and examples; add a health-check diagnostic output (P2).

## Files and areas I inspected (non-exhaustive)

- injectq/__init__.py
- injectq/core/container.py
- injectq/core/registry.py
- injectq/core/resolver.py
- injectq/core/thread_safe_resolver.py
- injectq/core/scopes.py
- injectq/core/async_scopes.py
- injectq/core/thread_safety.py
- injectq/decorators/inject.py
- injectq/decorators/resource.py
- injectq/diagnostics/*.py
- injectq/integrations/fastapi.py
- injectq/components/*
- tests/

## Closing notes

This library is well-architected for teams that need a flexible DI system in Python with async-first thinking. The main work to reach "bulletproof" status is improving clarity around hybrid sync/async modes, enhancing diagnostics for fast failure in production, and tightening type coverage. Those investments will pay off proportionally because the library already exposes a rich feature set and good composability.

If you'd like, I can:

- Open a follow-up PR with small, low-risk changes: add the "Sync vs Async" doc and a runtime check (P0 quick-win).
- Create targeted unit tests that exercise hybrid threading+async interactions and add them to tests/ to avoid regressions.

---
End of review.
