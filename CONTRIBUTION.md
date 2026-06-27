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
