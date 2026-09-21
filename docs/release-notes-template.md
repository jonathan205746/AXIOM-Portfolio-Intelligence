# AXIOM Portfolio Intelligence — Release Notes Template

> **Template only.** This file is not evidence that a release has been completed or published. Copy it to a version-specific file, replace every placeholder, and check every required item before creating a GitHub Release.

## Release identity

- Version: \`<VERSION>\`
- Release commit: \`<RELEASE_SHA>\`
- Release date (UTC): \`<UTC_DATE>\`

## Highlights

- <HIGHLIGHT_1>
- <HIGHLIGHT_2>
- <HIGHLIGHT_3>

## Verified quantitative evaluation

Document only metrics reproduced for the exact release commit. Do not add historical sentiment-performance claims without a point-in-time news dataset.

| Metric | Quantitative strategy | Equal weight | Benchmark |
|---|---:|---:|---:|
| Net CAGR | <VALUE> | <VALUE> | <VALUE> |
| Annualized volatility | <VALUE> | <VALUE> | <VALUE> |
| Sharpe ratio | <VALUE> | <VALUE> | <VALUE> |
| Maximum drawdown | <VALUE> | <VALUE> | <VALUE> |

## Required release evidence

- [ ] \`make check\` passed on \`<RELEASE_SHA>\`
- [ ] Security workflow passed on \`<RELEASE_SHA>\`
- [ ] Patch/documentation checks passed
- [ ] ECR image digest recorded: \`<ECR_IMAGE_DIGEST>\`
- [ ] OIDC-authenticated Actions run recorded: \`<RUN_URL>\`
- [ ] SSM deployment command recorded: \`<COMMAND_ID>\`
- [ ] Production health check passed at \`<UTC_TIMESTAMP>\`
- [ ] Desktop and approved mobile/network smoke tests passed
- [ ] SES reset-email smoke test passed with private details redacted
- [ ] Rollback from \`<RELEASE_SHA>\` to \`<PREVIOUS_SHA>\` passed
- [ ] Final \`<RELEASE_SHA>\` redeployed after the rollback drill
- [ ] Screenshots, GIFs, logs, and sample reports reviewed for secrets and personal information

**Do not create the GitHub Release while any required item is unchecked.**

## Deployment evidence

\`\`\`text
GitHub Actions -> IAM OIDC -> ECR -> SSM -> EC2 -> Streamlit health check
\`\`\`

- ECR repository: \`<ECR_REPOSITORY>\`
- Image tag: \`<RELEASE_SHA>\`
- Image digest: \`<ECR_IMAGE_DIGEST>\`
- Workflow run: \`<RUN_URL>\`
- SSM command: \`<COMMAND_ID>\`

## Upgrade and rollback

Deploy the immutable ECR tag matching the release SHA. Roll back to a previously verified successful SHA, verify the exact running image and health endpoint, test the core workflow, and preserve \`/data\`.

Container rollback does not reverse database migrations. Backward-incompatible schema changes require a separately tested backup/restore plan or forward fix.

## Known limitations

- Educational and research software; not financial advice.
- Single-host deployment is not highly available.
- SQLite is intended for the current single-instance usage model.
- External providers can be unavailable or rate-limited.
- The current operator-restricted HTTP demo is not a stable public HTTPS endpoint.
- Historical results do not guarantee future performance.

See [the production release guide](AXIOM_PRODUCTION_RELEASE_GUIDE.md).
