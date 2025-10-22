# InjectQ Code Review

This document contains a high-level review of the `injectq` library, focusing on architecture, design patterns, and potential areas for improvement. The review is based on the state of the codebase as of the analysis date.

## Overall Impression

`injectq` is a powerful and feature-rich dependency injection library for Python. It successfully combines concepts from several established DI frameworks, offering a flexible and modern tool for managing dependencies in both synchronous and asynchronous applications.

The inclusion of a component system, advanced diagnostics (profiling, validation, visualization), and thoughtful integrations (FastAPI, Taskiq) makes it a very compelling choice. The API is generally well-designed, providing multiple interaction styles (decorators, direct binding, modules) to suit different developer preferences.

The following sections highlight specific observations and provide recommendations for improvement.

---

## Key Observations and Recommendations

### 1. Architecture and Design

#### Observation: Duplicated Dependency Resolver Logic
The library currently contains two separate dependency resolver classes: `core/resolver.py:DependencyResolver` and `core/thread_safe_resolver.py:ThreadSafeDependencyResolver`. The logic within these two classes is almost identical, with the primary difference being the addition of locking for thread safety in the latter. This duplication violates the DRY (Don't Repeat Yourself) principle, making the core resolution logic harder to maintain and reason about.

**Recommendation:**
Refactor the two resolvers into a single `DependencyResolver` class. Thread safety can be achieved by having the resolver accept a lock object (e.g., `HybridLock`) during its initialization. If thread safety is disabled, a "dummy" lock that does nothing can be passed instead. This consolidates the critical resolution logic into one place, improving maintainability and reducing the chance of bugs.

---

#### Observation: Complex Thread and Async Safety Model
The `HybridLock` in `core/thread_safety.py` is an intelligent solution for handling mixed sync/async environments. However, its implementation, particularly the fallback to `asyncio.to_thread` for acquiring a thread lock from an async context, can introduce non-obvious performance overhead. While this correctly avoids blocking the event loop, it adds complexity. Similarly, the separate `AsyncScopeManager` and `ScopeManager` classes, each with fallbacks, contribute to the overall complexity.

**Recommendation:**
The current implementation is functional, but it would be beneficial to:
1.  **Document the `HybridLock` behavior:** Clearly document the performance implications of using the lock in mixed sync/async scenarios, especially the `asyncio.to_thread` fallback.
2.  **Simplify Scope Management:** Investigate if `ScopeManager` and `AsyncScopeManager` can be merged into a single, unified manager that transparently handles both contexts, similar to the `HybridScope` approach. This would reduce the number of core classes and simplify the internal architecture.

---

#### Observation: Encapsulation Breaking in Component System
In `components/__init__.py`, the `ComponentContainer` class directly accesses private attributes of the `ComponentRegistry` (e.g., `self.component_registry._bindings`, `self.component_registry._instances`). This breaks encapsulation and makes the `ComponentContainer` tightly coupled to the internal implementation of the `ComponentRegistry`.

**Recommendation:**
Enhance the public API of `ComponentRegistry` to provide the necessary functionality. For example, add methods like `get_all_bindings()` or `get_component_names()` to the registry. The `ComponentContainer` should then be updated to use these public methods exclusively, respecting encapsulation and improving code modularity.

---

### 2. API and Usability

#### Observation: Large Public API Surface
The main `injectq/__init__.py` file exports a very large number of symbols in its `__all__` list. This can be overwhelming for new users and makes it unclear what constitutes the stable, public-facing API versus internal implementation details.

**Recommendation:**
Conduct a review of the symbols listed in `__all__`. Consider moving lower-level classes (e.g., `ServiceBinding`, `ComponentBinding`, `ThreadSafeDict`) to an internal `_internal` module or simply not exporting them. The public API should be focused and consist of the primary entry points a user needs: the `InjectQ` container, core decorators (`@inject`, `@singleton`, etc.), modules, and high-level exceptions.

---

#### Observation: Brittle Dependency Name Resolution in Components
The component startup logic in `ComponentRegistry.get_startup_order` appears to resolve dependencies based on the `__name__` attribute of the dependency type. This approach is brittle and can lead to conflicts if two different interface types in different modules share the same class name.

**Recommendation:**
Modify the dependency graph to use the actual type objects as keys or identifiers, rather than their string names. This ensures that dependencies are tracked precisely, avoiding any ambiguity or potential for name collisions.

---

### 3. Code Quality and Style

#### Observation: Local Imports to Avoid Circular Dependencies
There are several instances of `noqa: PLC0415` comments to suppress warnings about imports not being at the top level. While sometimes necessary, they can also be a symptom of a sub-optimal dependency structure between modules.

**Recommendation:**
Review the modules involved in these circular dependencies. It may be possible to refactor the code, perhaps by moving a class or function to a different file or introducing a new module, to break the cycle. This would improve the overall structure and readability of the codebase.

---

## Positive Highlights

- **Excellent Diagnostics:** The `diagnostics` package is a standout feature. The `DependencyProfiler`, `DependencyValidator`, and `DependencyVisualizer` are invaluable tools for understanding, debugging, and optimizing complex applications.
- **Flexible API Design:** The library provides multiple, intuitive ways to register dependencies (decorators, dict-style access, modules), catering to various use cases and developer preferences.
- **Elegant Lazy Injection:** The `Inject[T]` proxy object is a very clean and user-friendly mechanism for lazy dependency resolution.
- **Modern Async/Context Handling:** The use of `contextvars` for framework integrations (FastAPI) is the correct, modern approach for handling request-scoped or task-scoped context in async applications, ensuring performance and safety.
- **Comprehensive Feature Set:** The library is well-rounded, covering not just basic DI but also component lifecycles, resource management, and advanced configuration patterns.
