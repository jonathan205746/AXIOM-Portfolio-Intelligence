# Dependency Residual Risk Register

## Final scan summary

Security hardening was evaluated independently for the complete repository
dependency snapshot and the deployed Streamlit runtime image.

**Verified snapshot:** 2026-09-21 on `main` commit `0a28dd6886e1a381193b03cb621bb3a960ba7c57`. The counts below are point-in-time scanner evidence, not a live vulnerability dashboard.

| Scope | Original | Final |
|---|---:|---:|
| Repository dependency scan | 22 HIGH / 0 CRITICAL | 16 HIGH / 0 CRITICAL |
| Runtime container scan | 15 HIGH / 0 CRITICAL | 2 HIGH / 0 CRITICAL |

No scanner coverage was disabled or globally excluded.

## Runtime residual risk

| Package | Advisory | Installed | Fixed | Exposure path | Mitigation / decision |
|---|---|---:|---:|---|---|
| msgpack | GHSA-6v7p-g79w-8964 | 1.1.2 | 1.2.1 | Vendored inside `pip 26.2.1` under `pip/_vendor/msgpack`; not installed or importable as an AXIOM application dependency | Accepted residual tooling exposure. AXIOM does not directly import or process MessagePack through this vendored copy. Continue monitoring pip/base-image updates and re-scan when the vendored version is refreshed. |
| setuptools | CVE-2025-47273 | 70.3.0 | 78.1.1 | Residual packaging metadata detected by Trivy despite AXIOM explicitly installing setuptools 84.0.0 | Accepted as residual packaging/base-image exposure. AXIOM's active setuptools is pinned to 84.0.0. Continue monitoring and remove stale/vendored copy when upstream image/tooling permits. |

## Remediated runtime findings

The hardening work removed the previously reported HIGH findings from:

- transformers
- cryptography
- pyasn1
- Pillow
- protobuf
- vulnerable wheel installation

The deployed runtime remains non-root using UID/GID 10001.

## Repository/development residual findings

This verified repository snapshot reports 16 HIGH findings in development
or notebook dependencies that are not used to construct the deployed Streamlit
runtime image.

Current residual families:

- `jupyter_server 2.20.0` — CVE-2026-86049 — fixed in 2.21.0
- `Pillow 10.4.0` — residual findings in the full development snapshot
- `protobuf 4.25.9` — CVE-2026-0994 — fixed in 5.29.6 / 6.33.5
- `tornado 6.5.7` — CVE-2026-82397 — fixed in 6.5.8

These findings are tracked separately from deployed runtime exposure. They are
retained temporarily in the broad development snapshot and should be modernized
in follow-up dependency-maintenance work without weakening Trivy coverage.

## Decision

Issue #45 materially reduced security exposure while preserving AXIOM behavior:

- repository HIGH findings: 22 -> 16
- runtime HIGH findings: 15 -> 2
- CRITICAL findings: 0 -> 0
- complete application test suite: 84 passing

The remaining findings are documented rather than hidden or excluded.