# AXIOM Documentation Guide

AXIOM Portfolio Intelligence is a production-oriented portfolio research project. This guide separates the fastest portfolio review path from architecture, operations, API, release, and security detail.

## Recruiter / five-minute path

1. [Project README](../README.md) — product story, screenshots, quantitative evidence, security posture, and limitations.
2. [System Architecture](AXIOM_ARCHITECTURE.md) — components, request flow, AWS topology, and design trade-offs.
3. [v1.0.0 Release Notes](release-notes-v1.0.0.md) — stable release evidence and known limitations.
4. [Dependency Residual-Risk Register](security/dependency-risk-register.md) — documented security-hardening result and accepted residual findings.

## Senior engineer / deep-dive path

1. [System Architecture](AXIOM_ARCHITECTURE.md)
2. [Setup and Operations Guide](AXIOM_SETUP_GUIDE.md)
3. [API Reference](AXIOM_API_REFERENCE.md)
4. [Production Release Guide](AXIOM_PRODUCTION_RELEASE_GUIDE.md)
5. [Dependency Residual-Risk Register](security/dependency-risk-register.md)

## Operations / release path

Use these documents when reproducing or operating the deployed demonstration:

- [Setup and Operations Guide](AXIOM_SETUP_GUIDE.md) — local Python, Docker, optional FastAPI, AWS setup, and troubleshooting.
- [Production Release Guide](AXIOM_PRODUCTION_RELEASE_GUIDE.md) — release gates, OIDC/ECR/SSM deployment, rollback, and publication evidence.
- [Release Notes Template](release-notes-template.md) — checklist for a future semantic release.
- [v1.0.0 Release Notes](release-notes-v1.0.0.md) — immutable release-specific evidence.

The supported delivery story is:

```text
GitHub Actions
  -> IAM OIDC
  -> immutable ECR image
  -> AWS Systems Manager
  -> Docker on EC2
  -> Streamlit health verification
```

Manual SSH/SCP procedures in the setup guide are recovery/debugging tools for the current single-host demonstration, not the preferred long-term production deployment or secret-management model.

## Security evidence

The security workflow separates the broad repository/development dependency snapshot from the deployed Streamlit runtime image.

See [Dependency Residual-Risk Register](security/dependency-risk-register.md) for the verified point-in-time findings, exposure paths, mitigations, and accepted residual risk.

Security counts are snapshots tied to a scan/commit. They should not be interpreted as a live vulnerability dashboard.

## Documentation status

| Document | Status |
| --- | --- |
| Project README | Current portfolio overview |
| System Architecture | Current architecture and design boundaries |
| Setup and Operations Guide | Current operational guidance |
| API Reference | Current optional FastAPI contract guidance |
| Production Release Guide | Current release/runbook process |
| v1.0.0 Release Notes | Historical immutable release record |
| Dependency Risk Register | Point-in-time security evidence; re-scan for current findings |

## Scope boundaries

AXIOM does not claim that AI improves investment returns, that historical performance predicts future results, or that the current single-EC2/SQLite topology is highly available.

The AWS environment is an operator-restricted HTTP demonstration, not a stable public HTTPS service. Quantitative portfolio weights remain deterministic and separate from generated commentary. Point-in-time historical news is not available, so historical sentiment-performance claims are intentionally excluded.
