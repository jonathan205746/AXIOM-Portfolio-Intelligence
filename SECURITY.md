# Security Policy

## Supported versions

AXIOM Portfolio Intelligence is under active development. Security fixes are
provided for the latest commit on the `main` branch only.

| Version | Supported |
| --- | --- |
| Latest `main` | Yes |
| Older commits, branches, and releases | No |

## Reporting a vulnerability

Please do not open a public GitHub issue for a suspected vulnerability.

Use GitHub's private vulnerability reporting feature:

1. Open the repository's **Security** tab.
2. Select **Advisories**.
3. Select **Report a vulnerability**.
4. Include the affected component, reproduction steps, potential impact, and
   any suggested remediation.

Repository security page:

`https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer/security`

Do not include real passwords, API keys, JWT signing keys, AWS credentials,
private keys, database files, or private portfolio information in a report.
Replace sensitive values with clearly marked test values.

## Response process

The maintainer will aim to:

- acknowledge a complete report within 5 business days;
- validate and assess the reported impact;
- coordinate remediation privately;
- publish a security advisory when disclosure is appropriate; and
- credit the reporter if requested and permitted.

Response times are targets rather than a service-level agreement.

## Security model

- New passwords are hashed with bcrypt.
- Legacy SHA-256 password hashes are accepted only for migration and are
  replaced with bcrypt after successful authentication.
- FastAPI access tokens are signed using a non-placeholder `SECRET_KEY` of at
  least 32 characters.
- Protected API resources are scoped to the authenticated user.
- Browser origins are restricted using `CORS_ORIGINS`.
- Local `.env` files, databases, generated reports, and private keys must not
  be committed.
- Password recovery by username and email alone is disabled.

## Deployment responsibilities

Operators are responsible for:

- terminating public traffic with HTTPS;
- rotating any secret exposed in logs, screenshots, messages, or Git history;
- storing production secrets in AWS Secrets Manager or Systems Manager
  Parameter Store;
- restricting security-group ingress;
- applying dependency and operating-system security updates;
- monitoring authentication, application, and infrastructure failures; and
- backing up and testing restoration of persistent data.

## Scope

Security reports may cover authentication, authorization, secret exposure,
injection, unsafe report rendering, dependency vulnerabilities, container or
cloud configuration, and unintended disclosure of portfolio data.

The project is provided for education and research and is not a financial,
brokerage, custody, or trading service.
