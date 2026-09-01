# AXIOM Portfolio Intelligence — Setup and Operations Guide

This guide covers local Python setup, Docker execution, optional FastAPI startup, and AWS EC2 operations for the repository **AI-Powered-Portfolio-Optimizer**.

## Prerequisites

| Requirement | Recommended version | Check command |
| --- | --- | --- |
| Python | 3.10+ | `python --version` |
| pip | Current | `python -m pip --version` |
| Git | Current | `git --version` |
| Docker Desktop/Engine | Current supported release | `docker --version` |
| Docker Compose | Compose v2 | `docker compose version` |
| AWS CLI | v2 for AWS deployment | `aws --version` |

FinBERT and its dependencies require significant memory and disk space. CPU inference works but the first model load can be slow.

## Clone the repository

```bash
git clone https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer.git
cd AI-Powered-Portfolio-Optimizer
```

The repository name and product name are intentionally different:

```text
Product:    AXIOM Portfolio Intelligence
Repository: AI-Powered-Portfolio-Optimizer
```

## Local Python setup

### Windows PowerShell

```powershell
py -3.10 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements-frontend.txt
```

If PowerShell blocks activation for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

### macOS or Linux

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements-frontend.txt
```

Use `requirements.txt` instead when you intentionally need the repository’s complete dependency set.

## Environment configuration

Copy the example file:

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS or Linux:

```bash
cp .env.example .env
```

Example:

```env
NEWS_API_KEY=replace_with_one_valid_newsapi_key
GROQ_API_KEY=replace_with_your_groq_key
GROQ_MODEL=openai/gpt-oss-120b
SECRET_KEY=replace_with_a_long_random_value
DB_DIR=./data
FAISS_INDEX_PATH=./data/faiss_index
```

Rules:

- use exactly one value per API-key variable
- do not separate multiple keys with commas
- do not add Markdown quotes or links around values
- do not commit `.env`
- rotate any key exposed in logs, screenshots, or commit history
- use AWS Secrets Manager or SSM for a production deployment

## Run the Streamlit application

With the virtual environment activated:

```bash
streamlit run frontend/app.py
```

Open:

```text
http://localhost:8501
```

Health check:

```bash
curl -f http://localhost:8501/_stcore/health
```

## Run with Docker Compose

Make sure Docker is running and `.env` exists:

```bash
docker compose up -d --build --force-recreate frontend
```

Check status:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs --tail=200 frontend
```

Open:

```text
http://localhost:8501
```

Stop the containers:

```bash
docker compose down
```

`docker compose down` does not delete the named volume unless `--volumes` is added. Do not use `--volumes` if you need to preserve SQLite and FAISS data.

## Verify environment variables inside Docker

Check presence and format without printing secret values:

```bash
docker compose exec frontend python -c 'import os; k=os.getenv("GROQ_API_KEY", "").strip(); print({"present": bool(k), "length": len(k), "starts_with_gsk": k.startswith("gsk_")})'
```

News key check:

```bash
docker compose exec frontend python -c 'import os; k=os.getenv("NEWS_API_KEY", "").strip(); print({"present": bool(k), "length": len(k), "contains_comma": "," in k})'
```

## Verify the RAG provider

```bash
docker compose exec frontend python -c 'from src.models.rag_pipeline import RAGPipeline; r=RAGPipeline(); print("RAG initialized:", type(r).__name__, "model:", r.model_name)'
```

If ChatGroq reports that `api_key` must be a string, confirm the installed `langchain-groq` and Pydantic versions. Pass a stripped environment string using the constructor supported by the installed version, pin the compatible dependency set, rebuild the image, and add an initialization test.

## Verify persistence

The Docker deployment uses:

```text
DB_DIR=/data
FAISS_INDEX_PATH=/data/faiss_index
```

Inspect mounts:

```bash
docker inspect portfolio-dashboard --format '{{range .Mounts}}{{println .Type .Source "->" .Destination}}{{end}}'
```

Verify the database path and row counts:

```bash
docker compose exec frontend python -c 'import os, sqlite3; from src.database.db import DB_DIR, DB_PATH, init_db; init_db(); print("DB_DIR:", DB_DIR); print("DB_PATH:", DB_PATH); print("writable:", os.access(DB_DIR, os.W_OK)); print("exists:", os.path.isfile(DB_PATH)); c=sqlite3.connect(DB_PATH); print({t:c.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("users", "portfolios", "holdings", "optimization_runs")}); c.close()'
```

## Optional FastAPI service

The public AWS demo uses Streamlit directly. If the repository’s optional API profile is configured:

```bash
docker compose --profile api up -d --build
```

Open:

```text
http://localhost:8000/docs
```

Or run locally when `backend/app/main.py` exists:

```bash
uvicorn backend.app.main:app --reload --port 8000
```

Always compare `docs/api_reference.md` with the running `/openapi.json` schema.

## Code quality and tests

Compile-check:

```bash
python -m compileall -q frontend src backend
```

Run tests:

```bash
pytest tests -v
```

If development tools are installed:

```bash
black --check frontend src backend tests
ruff check frontend src backend tests
mypy frontend src backend
```

## AWS deployment prerequisites

Before deployment, confirm:

- AWS CLI is authenticated
- the target region is `ap-south-1` or your chosen region
- VPC and public subnet IDs are correct
- the subnet can assign/reach a public IPv4 address
- the EC2 key pair exists in the same region
- the private `.pem` file matches that key pair
- your current public IPv4 address is available for `AllowedCidr`

Configure AWS CLI:

```powershell
aws configure
aws sts get-caller-identity
```

## Validate CloudFormation

```powershell
$Region = "ap-south-1"

aws cloudformation validate-template `
  --region $Region `
  --template-body file://deploy/aws/ec2-stack.yaml
```

## Deploy the stack

```powershell
$Region = "ap-south-1"
$VpcId = "vpc-xxxxxxxxxxxxxxxxx"
$SubnetId = "subnet-xxxxxxxxxxxxxxxxx"
$MyIp = (Invoke-RestMethod "https://checkip.amazonaws.com").Trim()

$DeployArgs = @(
  "cloudformation", "deploy"
  "--region", $Region
  "--stack-name", "portfolio-optimizer"
  "--template-file", "deploy/aws/ec2-stack.yaml"
  "--parameter-overrides"
  "VpcId=$VpcId"
  "SubnetId=$SubnetId"
  "KeyName=portfolio-optimizer-key"
  "AllowedCidr=$MyIp/32"
  "InstanceType=t3.small"
  "--capabilities", "CAPABILITY_NAMED_IAM"
)

aws @DeployArgs
```

Use quoted PowerShell strings for VPC and subnet IDs. Do not add line-continuation backticks to ordinary variable assignments.

## Get AWS outputs

```powershell
aws cloudformation describe-stacks `
  --region $Region `
  --stack-name portfolio-optimizer `
  --query "Stacks[0].Outputs" `
  --output table
```

The output includes the instance ID, public IP, and dashboard URL.

## SSH from Windows PowerShell

```powershell
$PemPath = "$env:USERPROFILE\.ssh\portfolio-optimizer-key.pem"
$PublicIp = "YOUR_CURRENT_PUBLIC_IP"

Test-Path $PemPath
ssh -o ConnectTimeout=20 -i $PemPath "ec2-user@$PublicIp"
```

After the Amazon Linux prompt appears, run Linux commands:

```bash
cd /opt/portfolio
sudo docker compose ps
sudo docker compose logs --tail=200 frontend
curl -f http://localhost:8501/_stcore/health
```

Do not run `cd /opt/portfolio` or `sudo docker` in Windows PowerShell. Those commands belong inside the EC2 SSH session.

## Deploy updated application code

Commit and push locally first:

```powershell
git add frontend src README.md docs Makefile
git commit -m "Update AXIOM application and documentation"
git push origin main
```

Then SSH to EC2 and rebuild:

```bash
cd /opt/portfolio
git pull origin main
sudo docker compose up -d --build --force-recreate frontend
sudo docker compose ps
sudo docker compose logs --tail=200 frontend
```

## Upload `.env` to EC2

Run `scp` from Windows PowerShell, not inside EC2:

```powershell
scp -i $PemPath ".env" "ec2-user@${PublicIp}:/opt/portfolio/.env"
```

Then SSH to EC2:

```bash
cd /opt/portfolio
chmod 600 .env
sudo docker compose up -d --force-recreate frontend
```

## Common problems

### NewsAPI returns `401 Unauthorized`

- verify the key is active
- remove whitespace
- ensure `NEWS_API_KEY` contains one key only
- confirm there is no comma in the value
- rotate the key if it was exposed
- recreate the container after changing `.env`

### RAG says `api_key` must be a string

- inspect installed package versions
- reproduce the provider constructor in a short Python command
- use a stripped string rather than an incompatible secret-wrapper type
- pin compatible dependencies
- rebuild the Docker image

### Streamlit is unhealthy during startup

FinBERT can take time to load. Inspect:

```bash
docker compose ps
docker compose logs --tail=200 frontend
```

The configured health-check start period should allow for model cold start.

### SSH connects to port 22 but times out during banner exchange

This can indicate EC2 memory or CPU pressure rather than a security-group failure. Check EC2 status checks, monitoring, system logs, and instance capacity. The project moved from `t3.micro` to `t3.small` for improved stability.

### SSH permission denied

Confirm the private key matches the EC2 key pair:

```powershell
ssh-keygen -y -f $PemPath | ssh-keygen -lf -

$AwsPublicKey = aws ec2 describe-key-pairs `
  --region $Region `
  --key-names "portfolio-optimizer-key" `
  --include-public-key `
  --query "KeyPairs[0].PublicKey" `
  --output text

$AwsPublicKey | ssh-keygen -lf -
```

The fingerprints must match.

### Browser shows React error `#231`

Search for string-valued inline event handlers:

```powershell
Get-ChildItem frontend,src -Recurse -File -Include "*.py" |
Select-String -Pattern "onmouseover|onmouseout"
```

Replace raw inline handlers with CSS pseudo-classes or supported Streamlit components, rebuild, and hard-refresh the browser.

## Production recommendations

- assign a stable domain and enable HTTPS
- use Secrets Manager or SSM instead of a long-lived `.env`
- use an EC2 IAM role instead of embedded AWS credentials
- add CloudWatch logs, metrics, dashboards, and alarms
- migrate SQLite to PostgreSQL for multi-user scale
- use Argon2id or bcrypt for password hashing
- add backups and restore testing
- build immutable container images in CI
- add health-gated deployment and rollback
