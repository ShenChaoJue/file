# llmdoc Index

This directory is the stable project memory for the Personal File Manager repository. Start with `startup.md`, then read the MUST docs relevant to your task before opening code.

## Startup

- `startup.md` — minimal onboarding path for future agents.

## MUST Docs

- `must/security-boundaries.md` — required security rules for filesystem and auth work.
- `must/verification.md` — commands and known verification limits.
- `must/deployment-config.md` — required deployment and environment assumptions.

## Overview

- `overview/project-overview.md` — product scope, non-goals, and main capabilities.

## Architecture

- `architecture/backend.md` — backend modules, startup, API responsibilities, and persistence.
- `architecture/frontend.md` — React app structure, state flow, and UI components.
- `architecture/deployment.md` — Docker Compose and runtime layout.

## Guides

- `guides/development.md` — local development workflow.
- `guides/adding-file-operation.md` — how to add or modify file operations safely.

## Reference

- `reference/api.md` — backend API surface.
- `reference/configuration.md` — environment variables and storage paths.

## Memory

`memory/reflections/` and `memory/decisions/` are reserved for dated project memories. They are not part of the stable startup path unless linked from this index later.

## Scratch Space

`.llmdoc-tmp/` contains investigation notes and should not be treated as stable documentation.
