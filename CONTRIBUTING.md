# Contributing to AXIOM Portfolio Intelligence

Thanks for improving AXIOM. This repository treats reproducibility, security, and honest evaluation as part of the product rather than post-release cleanup.

## Development workflow

1. Create a focused branch from the latest `main`.
2. Keep changes scoped; avoid mixing feature work with repository or deployment hardening.
3. Add or update tests for behavioral changes.
4. Run the same quality contract that CI runs.
5. Open a pull request and wait for required status checks before merging.

## Local setup

```bash
python -m venv .venv
make install-dev
```

Copy the environment template and add only local test credentials:

```bash
cp .env.example .env
```

Never commit `.env`, cloud credentials, API keys, private keys, databases containing user data, or production reports.

## Required quality gate

```bash
make check
git diff --check
```

The gate includes:

- Python compilation
- Black format verification
- Ruff linting
- mypy type checking
- the complete pytest suite

Do not bypass a failing gate by deleting tests, weakening assertions, or marking failures as allowed without documenting the reason in the pull request.

## Security expectations

Pull requests also run:

- Gitleaks against Git history;
- Trivy dependency scanning that reports high/critical findings and blocks critical vulnerabilities; and
- Trivy scanning of the built runtime container with the same policy.

Third-party GitHub Actions are pinned to full commit SHAs. When updating an action, verify the upstream release/tag and pin the resolved commit rather than a mutable tag.

Do not report vulnerabilities in a public issue. Follow [`SECURITY.md`](SECURITY.md).

## Containers

Runtime containers must remain non-root. UID/GID `10001` owns application data paths. Streamlit XSRF protection must remain enabled unless a specific, documented architecture requires a different control and an equivalent mitigation is implemented.

## Pull requests

A useful pull request description should include:

- the problem being solved;
- the files/components affected;
- validation performed;
- security or deployment impact; and
- rollback considerations for production-facing changes.

Human approval is not required for a solo-maintainer repository, but required automated checks should still protect `main`.

## Releases

Do not publish placeholder evidence as release notes. Start from [`docs/release-notes-template.md`](docs/release-notes-template.md), replace every placeholder with evidence from the exact release commit, complete the checklist, and follow [`docs/AXIOM_PRODUCTION_RELEASE_GUIDE.md`](docs/AXIOM_PRODUCTION_RELEASE_GUIDE.md).
