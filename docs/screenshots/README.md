# Screenshot and Demo Plan

Use real, sanitized evidence. Do not commit placeholders or screenshots containing secrets, account IDs, tokens, email addresses, private holdings, or browser bookmarks.

## README product images

Capture at 1440 × 900 where possible:

| File | Evidence |
|---|---|
| `01-dashboard.png` | Product landing/dashboard and navigation |
| `02-portfolio.png` | Holdings input and validation |
| `03-optimization.png` | Current versus recommended allocation |
| `04-risk.png` | Risk metrics, drawdown, and correlation |
| `05-sentiment-rag.png` | Relevant news, FinBERT result, and grounded commentary |
| `06-report.png` | Generated HTML report |

After the files exist, place a compact gallery near the top of `README.md`. Keep the first image above the fold and avoid showing six full-width images consecutively.

## Release engineering evidence

Store these under `docs/screenshots/release/`:

| File | Evidence |
|---|---|
| `01-tests.png` | Exact release SHA and passing tests |
| `02-actions.png` | Successful production workflow |
| `03-oidc.png` | Sanitized OIDC claim names and role step |
| `04-ecr.png` | SHA-tagged image and push time |
| `05-ssm.png` | Successful deployment command |
| `06-ec2-health.png` | Container image plus `ok` health result |
| `07-mobile.png` | Real phone view at narrow width |
| `08-rollback.png` | Previous image restored and healthy |
| `09-final-release.png` | Final release SHA redeployed |

These screenshots are audit evidence; only the strongest one or two belong in the public README.

## 40-second demo GIF storyboard

Record a clean 1280 × 720 browser window:

| Time | Scene |
|---:|---|
| 0–4 s | AXIOM title and portfolio overview |
| 4–10 s | Add/select holdings and run analysis |
| 10–17 s | Compare current and optimized allocation |
| 17–24 s | Show risk metrics and correlation view |
| 24–31 s | Show relevant news and FinBERT sentiment |
| 31–37 s | Show grounded AI commentary |
| 37–40 s | Open the downloadable HTML report |

Save the result as `docs/demo/axiom-v1-demo.gif`. Keep it below roughly 10 MB by reducing frame rate, dimensions, or color count. Also retain an MP4 for the portfolio site and LinkedIn because it provides better quality at a smaller size.

Recommended README placement after recording:

```markdown
![AXIOM product demo](docs/demo/axiom-v1-demo.gif)
```

## Final visual QA

- Use a demo account and non-sensitive holdings.
- Keep zoom, theme, and window size consistent.
- Close developer tools and unrelated tabs.
- Wait for charts and fonts to finish rendering.
- Crop empty margins.
- Verify every filename matches README links exactly, including case.
