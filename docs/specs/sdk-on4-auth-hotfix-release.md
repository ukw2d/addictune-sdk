# SDK 0.4.3 / CLI 0.3.1 authentication hotfix

Status: current
Task: sdk-on4 (SDK ledger; cross-repository release)

## Goal and evidence
Release SDK commit 405bbaa's member-session application-authentication fix and make CLI installers consume it. Old application authentication returned HTTP 401 Basic denial; replacement was verified live with DI login 201, authenticated member GET 200, and ensure_session across all six networks. SDK 172 tests and CLI 31 auth tests passed before release preparation.

## Scope and contracts
- SDK: version 0.4.3, lockfile, changelog and GitHub release notes; publish only 0.4.3 wheel/sdist with uv publish.
- CLI: version 0.3.1, addictune-sdk>=0.4.3, lockfile using published PyPI artifact, hotfix release notes; tag invokes existing binary workflow; verify artifacts before publishing beta release.
- Ownership: SDK owns API authentication; CLI owns dependency selection and packaging. No authentication fallbacks, account data changes, new settings/stores or error-reporting changes (at-de2).
- Preserve pre-existing SDK .beads/interactions.jsonl diff. No credential values in release notes or validation output.

## Failure and rollback
PyPI publication is irreversible: independently review SDK release before uploading exact-version artifacts. Stop on credential/authentication blockers. Do not overwrite tags or published releases. If CLI CI fails, leave release draft and diagnose before publication. Do not republish the same version. SDK identity remains undocumented/revocable.

## Acceptance and validation
SDK tests and build pass; inspect distribution metadata and contents; PyPI 0.4.3 is retrievable. CLI locked sync resolves published SDK 0.4.3; just check and build pass. Review CLI final release diff independently. Commit/push reviewed versions, create tags/releases, monitor binary workflow, verify four installers and SHA256SUMS. Provide arm64 macOS build/reinstall commands. User explicitly authorized publishing and GitHub hotfix release.
