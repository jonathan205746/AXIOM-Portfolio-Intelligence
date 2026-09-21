# AXIOM Production Release Guide

This runbook covers SES, IAM OIDC, ECR, SSM deployment, rollback, mobile
testing, demo production, and publishing a versioned release.

## 1. Release gates

Do not tag the release until the exact release commit passes:

1. clean working tree, compilation, and full tests;
2. one commit-SHA image built and stored in ECR;
3. OIDC-authenticated SSM deployment and health check;
4. desktop, mobile, and SES smoke tests;
5. rollback to a previous healthy SHA without losing `/data`;
6. redeployment of the final release SHA;
7. privacy review of README, screenshots, GIF, and release notes.

## 2. Create the release candidate

Windows PowerShell:

```powershell
git switch main
git pull --ff-only
git status --short
python -m compileall -q frontend src backend
python -m pytest -q tests
git diff --check
$ReleaseSha = git rev-parse HEAD
```

The status and diff checks should return no output. Record the actual test count;
do not assume an earlier `80 passed` result remains current.

## 3. Verify Amazon SES

Keep these identities separate:

- the **EC2 instance role** sends password-reset email;
- the **GitHub OIDC role** pushes ECR images and starts SSM commands.

The deployment role should not receive SES permission.

In `ap-south-1`, confirm the sender identity and `PortfolioPasswordReset`
template exist. While SES is in sandbox, the test recipient must also be
verified; request production access before mailing arbitrary registered users.

Example EC2 role policy (replace the address):

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["ses:SendEmail", "ses:SendTemplatedEmail"],
    "Resource": "*",
    "Condition": {
      "StringEquals": {"ses:FromAddress": "verified-sender@example.com"}
    }
  }]
}
```

On EC2, verify without printing secrets:

```bash
aws sts get-caller-identity --query Arn --output text
docker exec portfolio-dashboard printenv AWS_REGION
docker exec portfolio-dashboard printenv SES_FROM_EMAIL
docker exec portfolio-dashboard printenv SES_PASSWORD_RESET_TEMPLATE
aws ses get-template --region ap-south-1 \
  --template-name PortfolioPasswordReset \
  --query 'Template.SubjectPart' --output text
```

Use a dedicated demo account for one reset test. Confirm the code is expiring
and single-use, resend/attempt limits work, and the UI does not reveal whether
an arbitrary account exists. Redact the email and reset code.

## 4. Verify IAM OIDC

Create the GitHub provider once:

```text
URL: https://token.actions.githubusercontent.com
Audience: sts.amazonaws.com
```

Restrict the role trust to this repository's protected `production`
environment, matching the current workflow:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
    },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
      },
      "StringLike": {
        "token.actions.githubusercontent.com:sub": "repo:Parmodk2310/AI-Powered-Portfolio-Optimizer:environment:production"
      }
    }
  }]
}
```

The workflow currently declares `environment: production`, so a branch-form
subject would not match. Confirm the emitted `aud` and `sub` claims in the
sanitized Actions log before changing the trust policy. The workflow needs:

```yaml
permissions:
  contents: read
  id-token: write
```

Grant the role only ECR push for the AXIOM repository, SSM command execution for
the AXIOM instance, and the minimal describe/result actions required. Do not
store `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` in GitHub.

## 5. Build and verify the ECR image

Build once and push the full commit SHA:

```bash
REGISTRY="<account>.dkr.ecr.ap-south-1.amazonaws.com"
IMAGE_URI="$REGISTRY/<repository>"
aws ecr get-login-password --region ap-south-1 \
  | docker login --username AWS --password-stdin "$REGISTRY"
docker build -t "$IMAGE_URI:$GITHUB_SHA" .
docker push "$IMAGE_URI:$GITHUB_SHA"
```

Verify from PowerShell:

```powershell
aws ecr describe-images `
  --region ap-south-1 `
  --repository-name <repository> `
  --image-ids imageTag=$ReleaseSha `
  --query "imageDetails[0].{Digest:imageDigest,Pushed:imagePushedAt,Tags:imageTags}" `
  --output table
```

Record the SHA and digest. Never use `latest` for deployment proof or rollback.

## 6. Deploy through SSM

The EC2 profile needs `AmazonSSMManagedInstanceCore` and permission to pull the
selected ECR repository. The deployment script should save the current image,
pull the target SHA, recreate `frontend`, poll health through the FinBERT cold
start, and restore the previous image if health fails.

After the Actions run, verify on EC2:

```bash
cd /opt/portfolio
sudo docker compose ps
sudo docker inspect portfolio-dashboard --format '{{.Config.Image}}'
curl --fail --silent --show-error http://localhost:8501/_stcore/health
sudo docker logs --tail=200 portfolio-dashboard
```

The image must end with `$ReleaseSha`. Compose must reference
`${FRONTEND_IMAGE}` rather than a fixed local image.

## 7. Roll back step by step

### Choose the correct image

Select the latest production run that passed deployment and smoke tests before
the candidate. Copy its full SHA; do not assume `HEAD~1` is healthy.

```powershell
$PreviousSha = "<40-character-previous-successful-sha>"
aws ecr describe-images `
  --region ap-south-1 `
  --repository-name <repository> `
  --image-ids imageTag=$PreviousSha `
  --query "imageDetails[0].{Digest:imageDigest,Tags:imageTags}" `
  --output table
```

Stop if the immutable image is missing.

### Execute rollback

The current production workflow has no `image_tag` input; do not claim that a
manual dispatch can select an older image. Until a dedicated rollback workflow
is implemented, select a verified prior SHA and invoke the approved deployment
script through an authorized SSM command or administrative EC2 session. Record
the operator, target SHA, ECR digest, command ID, timestamps, and health result.

If using the approved SSM script, its EC2-side logic can be:

```bash
set -euo pipefail
REGION="ap-south-1"
REGISTRY="<account>.dkr.ecr.ap-south-1.amazonaws.com"
TARGET_IMAGE="$REGISTRY/<repository>:<previous-successful-sha>"
CURRENT_IMAGE="$(sudo docker inspect portfolio-dashboard --format '{{.Config.Image}}')"

aws ecr get-login-password --region "$REGION" \
  | sudo docker login --username AWS --password-stdin "$REGISTRY"
sudo docker pull "$TARGET_IMAGE"

cd /opt/portfolio
sudo env FRONTEND_IMAGE="$TARGET_IMAGE" \
  docker compose up -d --no-build --force-recreate frontend

healthy=false
for attempt in $(seq 1 36); do
  if curl --fail --silent http://localhost:8501/_stcore/health >/dev/null; then
    healthy=true
    break
  fi
  sleep 5
done

if [ "$healthy" != true ]; then
  sudo env FRONTEND_IMAGE="$CURRENT_IMAGE" \
    docker compose up -d --no-build --force-recreate frontend
  exit 1
fi

sudo docker inspect portfolio-dashboard --format '{{.Config.Image}}'
```

Accept rollback only after the exact SHA is running, health passes, login,
portfolio load, analysis, history, and report export work, `/data` persists,
and logs contain no migration/startup error. Then redeploy `$ReleaseSha` and
repeat every check.

> Image rollback does not reverse database migrations. Backward-incompatible
> migrations require a separately tested backup/restore or forward fix.

## 8. Mobile access and responsive testing

A phone browser does not require a separate mobile app or FastAPI service.
Validate network access, layout, and workflow separately.

On EC2:

```bash
sudo docker compose ps
sudo ss -lntp | grep 8501
curl -f http://localhost:8501/_stcore/health
```

Docker should publish `0.0.0.0:8501`, not only `127.0.0.1:8501`.

For a short test only:

| Port | Source |
| ---: | --- |
| 8501/TCP | Phone public IP `/32`, or temporarily `0.0.0.0/0` |
| 22/TCP | Administrator IP `/32` only |

Open `http://<current-public-ip>:8501` and ensure the browser does not change it
to HTTPS. Test on Wi-Fi and mobile data because their public IPs differ. Remove
the world-open port-8501 rule after testing.

If neither works, check the current EC2 public IP, 2/2 status checks, subnet
route to an Internet Gateway, network ACL, and host firewall.

For layout testing, use Chrome DevTools Device Toolbar and test 360×800,
390×844, 412×915, tablet width, portrait, and landscape. Exercise navigation,
forms, Plotly charts, tables, downloads, and long AI text. Then repeat on a real
Android/iPhone; emulation does not prove network or touch behavior.

For public release, use:

```text
Browser -> HTTPS :443 -> ALB or reverse proxy -> private Streamlit :8501
```

Use a stable domain, TLS certificate, authentication, rate limits, managed
secrets, monitoring, and backups. Keep port `8501` private.

## 9. Screenshots and demo GIF

Use the standalone `AXIOM_SCREENSHOT_GIF_GUIDE.md`. It defines the product
storyboard, engineering-evidence captures, privacy checklist, recording setup,
editing workflow, compression commands, filenames, and README layout. Keep
visual-production instructions out of this operational release runbook.

## 10. Publish `v1.0.0`

Start from the repository release-note template. Do not publish placeholders as completed release evidence:

```powershell
Copy-Item docs\release-notes-template.md docs\release-notes-v1.0.0.md
```

Fill every placeholder, check every required evidence item, and review the completed notes before tagging. Commit documentation, then deploy this new exact commit:

```powershell
git add README.md docs
git diff --cached --check
git diff --cached --name-status
git commit -m "Prepare AXIOM v1.0.0 documentation"
git push origin main
$ReleaseSha = git rev-parse HEAD
```

Run the final deployment, rollback drill, release-SHA redeployment, and evidence
checklist. Then check for an existing tag/release:

```powershell
git tag --list v1.0.0
gh release view v1.0.0
```

Stop if either exists. Never silently move a public tag. If neither exists:

```powershell
git tag -a v1.0.0 $ReleaseSha -m "AXIOM Portfolio Intelligence v1.0.0"
git show --no-patch --decorate v1.0.0
git push origin v1.0.0

gh release create v1.0.0 `
  --title "AXIOM Portfolio Intelligence v1.0.0" `
  --notes-file docs/release-notes-v1.0.0.md `
  --verify-tag `
  --latest
```

Optionally attach the MP4 demo and sanitized sample report:

```powershell
gh release upload v1.0.0 `
  docs\demo\axiom-v1-demo.mp4 `
  docs\samples\sample-portfolio-report.html
```

Verify with `gh release view v1.0.0 --web` and
`git ls-remote --tags origin v1.0.0`.

## 11. Evidence record

```text
Release/version:          v1.0.0
Release SHA:              <full SHA>
ECR digest:               <sha256 digest>
GitHub Actions run:       <URL>
SSM command ID:           <ID>
Production health UTC:    <timestamp>
Previous healthy SHA:     <full SHA>
Rollback:                 PASS/FAIL
Release SHA restored:     YES/NO
Desktop/mobile/SES tests: PASS/FAIL
Automated tests:          <count passed>
Reviewer:                 <name>
```
