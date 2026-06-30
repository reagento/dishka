# Phase II – Contribution Plan

## Issue

Repository: reagento/dishka
Issue: #402 – Migration from dependency-injector doc

## Reproduction Steps

1. Forked the Dishka repository.
2. Created a new branch named `docs/dependency-injector-migration`.
3. Reviewed Issue #402 and the maintainer's request.
4. Reviewed the documentation structure in the repository.
5. Confirmed that the project needs a separate migration page for users coming from `dependency-injector`.
6. Identified that the guide should focus on common dependency-injector usage patterns and translate them into Dishka's approach.

## Branch

https://github.com/zeynabbbhuseynli/dishka/tree/docs/dependency-injector-migration

## Solution Plan

I will create a documentation page that helps developers migrate from `dependency-injector` to Dishka.

The guide will explain how common dependency-injector concepts map to Dishka concepts, including containers, providers, factories, singleton-style dependencies, scoped dependencies, and dependency wiring.

I will include side-by-side Python examples showing the same use case in both libraries. The examples will be framework-independent and not Django-specific, following the maintainer's request.

Before opening a pull request, I will verify that the documentation builds correctly and that the new page fits the existing documentation structure.
## Implementation Notes

### Phase III Progress
**What I built:**
- Created `docs/migration_from_di.rst` - a new migration guide translating common `dependency-injector` patterns into their Dishka equivalents, with side-by-side Python code examples for each.
- Covered six patterns total:
  - Containers and factories (`providers.Factory` to `Provider` + `@provide`)
  - Singletons (`providers.Singleton` to `Scope.APP`)
  - Configuration (`providers.Configuration` to plain Python config object provided like any other dependency)
  - Resources and finalization (`providers.Resource` to generator-based `@provide` using `yield`)
  - Wiring (`@inject` + `Provide[Container.x]` to Dishka's `@inject` + `FromDishka[X]`)
  - Overriding dependencies for tests (`Container.x.override(...)` to building a container with a test-specific provider)
- Linked the new page into the docs navigation by adding `migration_from_di` to the `Contents:` toctree in `docs/index.rst`, right after `alternatives`.

**Commits this phase:**
- 70fbe70: docs: add containers/factories and singleton sections
- a91fe31: docs: add configuration section
- d818f68: docs: add resources and finalization section
- 26acc3e: docs: add wiring and test override sections; clean up formatting
- 4dadb05: docs: add migration guide to docs navigation

### Challenges Faced
- This being a documentation-only issue meant there was no bug to reproduce, so I confirmed the gap existed by checking the docs structure and the maintainer's comments on the issue instead.
- Hit a couple of RST formatting issues locally (a leftover placeholder directive and a stray markdown code fence from copy/paste) that needed manual cleanup.
- Could not install `hatch` locally to run a full docs build, so I verified formatting by reviewing the file structure carefully in VS Code instead. I plan to rely on CI feedback once a PR is opened.

### Testing Strategy
- Each code example was checked against the current Dishka API as shown in the project's own README/quickstart.
- Verified file structure visually in VS Code: heading underlines, blank lines around code blocks, no leftover placeholder content.
- A full Sphinx build was not run locally due to missing tooling; this is a known gap to close before opening a pull request.

### Branch Link
https://github.com/zeynabbbhuseynli/dishka/tree/docs/dependency-injector-migration
