# AXIOM Production Release Guide

This runbook covers the implemented path:

```text
GitHub Actions → IAM OIDC → Amazon ECR → Systems Manager → Docker on EC2
```

It separates routine deployment, automatic failure recovery, a deliberate rollback drill, mobile validation, and GitHub release publication.

## 1. Required GitHub environment variables

In **Repository → Settings → Environments → production**, configure:

| Variable | Example/purpose |
|---|---|
| `AWS_DEPLOY_ROLE_ARN` | IAM role assumed by GitHub Actions |
| `AWS_REGION` | `ap-south-1` |
| `ECR_REGISTRY` | Account ECR registry hostname |
| `ECR_REPOSITORY` | AXIOM image repository name |
| `EC2_INSTANCE_ID` | Target managed instance ID |
| `APP_DIRECTORY` | `/opt/portfolio` |
| `CONTAINER_NAME` | `portfolio-dashboard` |
| `HEALTHCHECK_URL` | `http://localhost:8501/_stcore/health` |

Use environment protection rules if available. Do not store an AWS access-key pair: the workflow requires `id-token: write` and obtains temporary credentials through OIDC.

## 2. OIDC trust boundary

The IAM role trust policy should restrict the GitHub identity provider to this repository and production environment. The significant claims are:

```text
aud = sts.amazonaws.com
sub = repo:Parmodk2310/AI-Powered-Portfolio-Optimizer:environment:production
```

The deployment role needs only the ECR operations required to inspect and push images plus SSM operations required to send and inspect a command for the target instance. Scope repository and instance resources wherever AWS supports it.

The EC2 instance profile separately needs:

- Systems Manager managed-instance permissions
- permission to authenticate to and pull from the selected ECR repository

Do not combine the GitHub deployment role and EC2 runtime role.

## 3. Pre-release validation

Run from the repository root:

```powershell
git switch main
git pull --ff-only
git status --short
python -m compileall -q frontend src backend
python -m pytest -q tests
git diff --check
```

Record the exact candidate SHA:

```powershell
$ReleaseSha = git rev-parse HEAD
$ReleaseSha
```

Do not tag a dirty, untested, or different commit.

## 4. Normal production deployment

A push to `main` triggers `.github/workflows/deploy-production.yml`.

1. Tests and compilation must pass.
2. GitHub requests an OIDC token for `sts.amazonaws.com`.
3. AWS returns temporary credentials for the configured role.
4. The workflow checks for an existing `$ReleaseSha` image.
5. If absent, Buildx builds and pushes it to ECR.
6. Systems Manager transfers and runs `scripts/deploy_ec2.sh`.
7. EC2 pulls the SHA image and recreates the frontend container.
8. The script polls the health endpoint for up to three minutes.

Verify the ECR image:

```powershell
aws ecr describe-images `
  --region ap-south-1 `
  --repository-name YOUR_ECR_REPOSITORY `
  --image-ids "imageTag=$ReleaseSha"
```

Verify the instance through SSM or an existing administrative session:

```bash
docker inspect portfolio-dashboard --format '{{.Config.Image}}'
curl --fail http://localhost:8501/_stcore/health
docker compose -f /opt/portfolio/docker-compose.yml ps
```

The image reference must end in the release SHA and health must return `ok`.

## 5. Automatic rollback behavior

Before replacing the container, `scripts/deploy_ec2.sh` records the current Docker image ID. If the new container never becomes healthy, the script:

1. captures recent frontend logs;
2. tags the previous image locally as `portfolio-frontend:rollback`;
3. recreates the frontend from that image;
4. verifies health again; and
5. exits with status 1 even if recovery succeeds.

The failed workflow is intentional: production may be restored, but the attempted release still failed.

## 6. Deliberate rollback to a previous ECR version

Use this when the current release is healthy at first but later proves defective.

List recent immutable images:

```powershell
aws ecr describe-images `
  --region ap-south-1 `
  --repository-name YOUR_ECR_REPOSITORY `
  --query "sort_by(imageDetails,& imagePushedAt)[-10:].{Pushed:imagePushedAt,Tags:imageTags,Digest:imageDigest}" `
  --output table
```

Choose a known successful SHA—never guess and do not use `latest`. Then execute the existing deployment script through Systems Manager with the previous full image URI. The safest repeatable method is to dispatch a dedicated rollback workflow or reuse the same SSM command construction as the production workflow.

On the instance, an authorized operator can perform the equivalent recovery:

```bash
cd /opt/portfolio

aws ecr get-login-password --region ap-south-1 |
  docker login --username AWS --password-stdin YOUR_ECR_REGISTRY

docker pull YOUR_ECR_REGISTRY/YOUR_ECR_REPOSITORY:PREVIOUS_SUCCESSFUL_SHA

FRONTEND_IMAGE=YOUR_ECR_REGISTRY/YOUR_ECR_REPOSITORY:PREVIOUS_SUCCESSFUL_SHA \
  docker compose up -d --no-build --force-recreate frontend

curl --fail http://localhost:8501/_stcore/health
docker inspect portfolio-dashboard --format '{{.Config.Image}}'
```

If health fails, inspect logs immediately:

```bash
docker compose logs --tail=200 frontend
```

### Database warning

Container rollback does not reverse SQLite schema or data changes. Before any migration:

1. stop writes or place the app in maintenance mode;
2. create and verify a database backup;
3. confirm the previous application version supports the new schema; and
4. document a forward-fix or database restore procedure.

## 7. Mobile-access validation

First confirm the application works inside EC2:

```bash
curl --fail http://localhost:8501/_stcore/health
sudo ss -lntp | grep 8501
docker compose ps
```

The service should be published on `0.0.0.0:8501`, not only `127.0.0.1:8501`.

For a temporary test, add a security-group inbound rule for TCP `8501` from the phone's current public IP. Mobile data and home Wi-Fi normally use different public IPs. Opening `8501` to `0.0.0.0/0` is acceptable only for a brief controlled test; remove that rule afterwards. Keep SSH port 22 restricted.

On the phone, type the full address with the scheme and port:

```text
http://PUBLIC_IP:8501
```

If EC2 health passes but the phone cannot connect, check:

- the instance still has the same public IP;
- the security group includes the phone network;
- the subnet route table has an internet-gateway route;
- the network ACL permits the request and return traffic;
- the browser has not changed `http` to `https`.

For a public release, assign an Elastic IP or use a load balancer, attach a domain, terminate TLS on port 443, redirect port 80 to HTTPS, and stop exposing 8501 directly.

## 8. Screenshot and demo evidence

Follow [`docs/screenshots/README.md`](screenshots/README.md). Never capture secrets, AWS account IDs, session tokens, email addresses, private portfolio values, or browser bookmarks.

## 9. Publish `v1.0.0`

Only continue after the checklist in `RELEASE_NOTES_v1.0.0.md` is complete and the final release SHA has been redeployed after any rollback drill.

```powershell
git switch main
git pull --ff-only
$ReleaseSha = git rev-parse HEAD

python -m compileall -q frontend src backend
python -m pytest -q tests
git status --short

git tag --list v1.0.0
gh release view v1.0.0
```

If the tag and release do not exist:

```powershell
git tag -a v1.0.0 $ReleaseSha -m "AXIOM Portfolio Intelligence v1.0.0"
git push origin v1.0.0

gh release create v1.0.0 `
  --title "AXIOM Portfolio Intelligence v1.0.0" `
  --notes-file RELEASE_NOTES_v1.0.0.md `
  --latest
```

Verify the published release and tag:

```powershell
gh release view v1.0.0
git ls-remote --tags origin v1.0.0
```

Do not publish the version merely because documentation exists. The tag must identify the exact tested production image.
