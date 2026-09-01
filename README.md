# AXIOM Portfolio Intelligence

### AI-Powered Portfolio Optimization and Research Platform

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FinBERT](https://img.shields.io/badge/NLP-FinBERT-F59E0B)](https://huggingface.co/ProsusAI/finbert)
[![FAISS](https://img.shields.io/badge/Vector_Search-FAISS-0467DF)](https://github.com/facebookresearch/faiss)
[![Groq](https://img.shields.io/badge/LLM-Groq-F55036)](https://groq.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![AWS](https://img.shields.io/badge/AWS-EC2-FF9900?logo=amazonaws&logoColor=white)](deploy/aws/ec2-stack.yaml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

> **Product name:** AXIOM Portfolio Intelligence  
> **Repository:** AI-Powered-Portfolio-Optimizer  
> **Deployment:** Docker on AWS EC2, provisioned with CloudFormation

**AXIOM Portfolio Intelligence** is an AI-powered portfolio research and optimization platform that combines adaptive Modern Portfolio Theory, market data, financial-news sentiment, risk analytics, and retrieval-augmented generation to produce explainable portfolio allocations and evidence-grounded recommendations.

The platform uses FinBERT for financial sentiment analysis, FAISS for semantic retrieval, LangChain and Groq for recommendation generation, and Streamlit for the interactive dashboard. It is containerized with Docker and deployed on AWS EC2 using CloudFormation.

> [!IMPORTANT]
> AXIOM Portfolio Intelligence is intended for educational, research, and portfolio-demonstration purposes. It does not provide financial advice or guarantee investment performance.

## Project links

- **Live demo:** [Open AXIOM Portfolio Intelligence](http://13.207.84.157:8501)
- **Portfolio case study:** [View the case study](https://parmodk2310.vercel.app/projects/portfolio)
- **Source code:** [GitHub repository](https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer)

> The live demo currently uses an EC2 public IPv4 address. The address may change if the instance is stopped and started unless an Elastic IP is assigned.

## Table of contents

- [AXIOM Portfolio Intelligence](#axiom-portfolio-intelligence)
    - [AI-Powered Portfolio Optimization and Research Platform](#ai-powered-portfolio-optimization-and-research-platform)
  - [Project links](#project-links)
  - [Table of contents](#table-of-contents)
  - [Problem statement](#problem-statement)
  - [Why this project](#why-this-project)
  - [What AXIOM does](#what-axiom-does)
  - [Key features](#key-features)
  - [System architecture](#system-architecture)
  - [Analysis pipeline](#analysis-pipeline)
    - [Quantitative analysis](#quantitative-analysis)
    - [Sentiment analysis](#sentiment-analysis)
    - [Retrieval-augmented generation](#retrieval-augmented-generation)
  - [Technology stack](#technology-stack)
    - [Application](#application)
    - [Quantitative analysis](#quantitative-analysis-1)
    - [AI and NLP](#ai-and-nlp)
    - [Data sources](#data-sources)
    - [Deployment](#deployment)
    - [Optional services](#optional-services)
  - [Project structure](#project-structure)
  - [Quick start](#quick-start)
    - [Prerequisites](#prerequisites)
    - [1. Clone the repository](#1-clone-the-repository)
    - [2. Create a virtual environment](#2-create-a-virtual-environment)
    - [3. Install dependencies](#3-install-dependencies)
    - [4. Create the environment file](#4-create-the-environment-file)
    - [5. Run the Streamlit application](#5-run-the-streamlit-application)
  - [Configuration](#configuration)
  - [Running with Docker](#running-with-docker)
  - [AWS deployment](#aws-deployment)
    - [Current deployment design](#current-deployment-design)
    - [Validate the CloudFormation template](#validate-the-cloudformation-template)
    - [Deploy the stack](#deploy-the-stack)
    - [Get stack outputs](#get-stack-outputs)
    - [Connect to the EC2 instance](#connect-to-the-ec2-instance)
  - [Optional API service](#optional-api-service)
  - [Database and persistence](#database-and-persistence)
  - [Testing](#testing)
  - [Verified walk-forward backtest](#verified-walk-forward-backtest)
  - [Security notes](#security-notes)
  - [Known limitations](#known-limitations)
  - [Roadmap](#roadmap)
  - [Documentation](#documentation)
  - [Contributing](#contributing)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Problem statement

Retail investors and portfolio learners commonly use separate tools for holdings, market prices, risk calculations, financial news, and AI-generated commentary. This fragmentation makes it difficult to evaluate a portfolio through one repeatable and explainable workflow.

Common problems include:

- portfolio allocation and risk are evaluated separately from financial news
- raw charts do not explain concentration or downside exposure
- portfolio optimizers can appear precise despite noisy historical estimates
- generic LLM responses may contain unsupported financial claims
- analysis results are often not stored for later comparison or auditing
- research workflows are difficult to reproduce across users and environments

AXIOM addresses these problems by combining quantitative optimization, risk diagnostics, financial sentiment, retrieved evidence, AI-generated explanations, persistent history, and downloadable reporting in one application.

## Why this project

This project was created to demonstrate an end-to-end AI and data-science system rather than an isolated notebook or model.

It brings together:

- quantitative finance and statistical optimization
- transformer-based financial sentiment analysis
- vector retrieval and retrieval-augmented generation
- application development and interactive visualization
- database design and persistent user workflows
- Docker containerization
- AWS infrastructure and deployment automation
- testing, debugging, monitoring, and security considerations

The project is especially useful for demonstrating the combined responsibilities of a Data Scientist, ML Engineer, AI Engineer, and Software Engineer.

## What AXIOM does

AXIOM allows a user to:

1. register or sign in
2. create and manage portfolios
3. add stock holdings and purchase information
4. retrieve historical market prices
5. calculate asset and portfolio returns
6. generate candidate portfolio allocations
7. analyze volatility, drawdown, Value at Risk, and correlations
8. fetch recent financial-news articles
9. score news sentiment using FinBERT
10. retrieve relevant context using FAISS
11. generate evidence-grounded recommendations using LangChain and Groq
12. save optimization results in SQLite
13. review historical analysis runs
14. compare portfolio performance and benchmarks
15. download a self-contained HTML analysis report

## Key features

- Historical market-data acquisition using Yahoo Finance
- Adaptive Modern Portfolio Theory portfolio optimization
- Sharpe-oriented allocation with configurable concentration constraints
- Equal-weight baseline and efficient-frontier comparison
- Risk analysis covering volatility, Value at Risk, maximum drawdown, and correlation
- FinBERT financial-news sentiment analysis
- FAISS-backed retrieval of relevant financial context
- LangChain and Groq-powered recommendation generation
- Graceful fallback when news or LLM services are unavailable
- Portfolio and holdings management
- SQLite persistence for users, portfolios, holdings, and optimization history
- Interactive Streamlit dashboard with Plotly visualizations
- Correlation matrix and per-asset volatility analysis
- Recent-news and sentiment views
- Downloadable self-contained HTML reports
- Docker Compose containerization
- AWS EC2 deployment using CloudFormation
- Persistent SQLite and FAISS data through a Docker volume

## System architecture

```text
User
  │
  ▼
AXIOM Streamlit Dashboard
  │
  ├── Portfolio and authentication workflows
  │
  ├── Market Data Pipeline
  │     └── Yahoo Finance
  │
  ├── Financial News Pipeline
  │     └── NewsAPI
  │
  ├── Intelligence Layer
  │     ├── FinBERT sentiment analysis
  │     ├── FAISS semantic retrieval
  │     └── LangChain + Groq recommendations
  │
  ├── Portfolio Engine
  │     ├── Adaptive MPT optimization
  │     ├── Efficient frontier
  │     └── Risk analytics
  │
  └── Persistence
        ├── SQLite database
        └── FAISS index

AWS Deployment
  │
  ├── AWS CloudFormation
  ├── Amazon EC2
  ├── Amazon Linux 2023
  ├── Docker Compose
  └── Persistent Docker volume mounted at /data
```

The system is organized into four logical layers:

1. **Experience layer:** Streamlit pages, user session state, charts, forms, history, and reports.
2. **Application layer:** orchestration of market data, news, models, optimization, and persistence.
3. **Intelligence layer:** FinBERT, FAISS, LangChain, Groq, Modern Portfolio Theory, and risk analytics.
4. **Infrastructure layer:** Docker, persistent storage, EC2, and CloudFormation.

## Analysis pipeline

The main analysis workflow follows these steps:

```text
Portfolio holdings
        │
        ├───────────────┐
        ▼               ▼
Historical prices   Financial news
        │               │
        ▼               ▼
Returns and risk    FinBERT sentiment
        │               │
        └───────┬───────┘
                ▼
        Adaptive MPT optimizer
                │
                ├── Final allocation
                ├── Efficient frontier
                ├── Risk report
                └── Health score
                │
                ▼
        FAISS retrieval + Groq RAG
                │
                ▼
      Recommendation and HTML report
                │
                ▼
          SQLite run history
```

### Quantitative analysis

For portfolio weights `w`, expected returns `μ`, and covariance matrix `Σ`:

```text
Expected portfolio return = wᵀμ
Portfolio variance        = wᵀΣw
Sharpe ratio              = (portfolio return - risk-free rate) / volatility
```

The optimizer evaluates allocations under constraints such as weights summing to one and concentration limits. Historical results are decision-support signals and are not forecasts or guarantees.

### Sentiment analysis

FinBERT classifies financial headlines as positive, negative, or neutral. Article-level outputs are aggregated into a per-ticker sentiment signal. News coverage and model confidence should be considered when interpreting this score.

### Retrieval-augmented generation

FAISS retrieves relevant financial context. LangChain combines that context with portfolio weight, sentiment, and risk information before sending the prompt to Groq.

RAG reduces unsupported generation by grounding the model in retrieved evidence, but it does not guarantee correctness. Generated recommendations should always be reviewed alongside the underlying data.

## Technology stack

### Application

- Python 3.10+
- Streamlit
- Plotly
- pandas
- NumPy
- SQLite

### Quantitative analysis

- Modern Portfolio Theory
- Adaptive signal blending
- Efficient-frontier analysis
- Sharpe ratio
- Value at Risk
- Maximum drawdown
- Correlation and volatility analysis

### AI and NLP

- FinBERT
- Hugging Face Transformers
- FAISS
- LangChain
- Groq
- `openai/gpt-oss-120b` through Groq by default

### Data sources

- Yahoo Finance through `yfinance`
- NewsAPI

### Deployment

- Docker
- Docker Compose
- AWS EC2
- AWS CloudFormation
- Amazon Linux 2023
- Persistent Docker volume

### Optional services

- FastAPI API service, when enabled with the API profile

## Project structure

```text
AI-Powered-Portfolio-Optimizer/
├── .env.example
├── .gitignore
├── .dockerignore
├── Dockerfile
├── Dockerfile.api
├── docker-compose.yml
├── LICENSE
├── Makefile
├── README.md
├── requirements.txt
├── requirements-backend.txt
├── requirements-frontend.txt
├── requirements-dev.txt
├── deploy/
│   ├── aws/
│   │   ├── README.md
│   │   └── ec2-stack.yaml
├── docs/
│   ├── api_reference.md
│   ├── architecture.md
│   └── setup.md
├── frontend/
│   ├── app.py
│   ├── pages/
│   └── ui/
├── backend/
│   └── app/
├── src/
│   ├── data/
│   ├── database/
│   ├── models/
│   ├── optimization/
│   └── utils/
├── data/
│   ├── faiss_index/
│   ├── plots/
│   └── portfolio_optimizer.db
├── notebooks/
└── tests/
```

## Quick start

### Prerequisites

- Python 3.10 or later
- Git
- pip
- Python virtual-environment support
- Docker and Docker Compose for container deployment

### 1. Clone the repository

```bash
git clone https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer.git
cd AI-Powered-Portfolio-Optimizer
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies

For the complete development environment:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

For the Streamlit application only:

```bash
pip install -r requirements-frontend.txt
```

### 4. Create the environment file

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

macOS or Linux:

```bash
cp .env.example .env
```

Add the required API keys and configuration values to `.env`.

### 5. Run the Streamlit application

```bash
streamlit run frontend/app.py
```

Open:

```text
http://localhost:8501
```

## Configuration

The application uses environment variables for external integrations and runtime configuration.

| Variable | Required | Purpose |
| --- | --- | --- |
| `NEWS_API_KEY` | For news features | Retrieves recent financial-news articles |
| `GROQ_API_KEY` | For LLM features | Generates AI-powered portfolio recommendations |
| `GROQ_MODEL` | Optional | Selects the Groq-hosted model |
| `SECRET_KEY` | Recommended | Supports authentication/session security where used |
| `DB_DIR` | Optional | Directory containing the SQLite database |
| `FAISS_INDEX_PATH` | Optional | Location of the persisted FAISS index |
| `DEMO_MODE` | Optional | Enables simplified demonstration behavior where supported |

Example `.env` file:

```env
NEWS_API_KEY=replace_with_your_newsapi_key
GROQ_API_KEY=replace_with_your_groq_key
GROQ_MODEL=openai/gpt-oss-120b
SECRET_KEY=replace_with_a_long_random_value
DB_DIR=/data
FAISS_INDEX_PATH=/data/faiss_index
```

Never commit `.env`, AWS credentials, API keys, or private-key files to Git.

## Running with Docker

Make sure `.env` exists, then run:

```bash
docker compose up --build -d
```

Check the service:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs --tail=200 frontend
```

Verify the Streamlit health endpoint:

```bash
curl -f http://localhost:8501/_stcore/health
```

The expected response is:

```text
ok
```

Stop the containers:

```bash
docker compose down
```

The named Docker volume is intentionally retained so application data survives container recreation.

## AWS deployment

The public AXIOM demo runs as a Docker container on an Amazon Linux 2023 EC2 instance. The infrastructure is provisioned using the CloudFormation template included in the repository.

### Current deployment design

| Component | Value |
| --- | --- |
| Product | AXIOM Portfolio Intelligence |
| Repository | AI-Powered-Portfolio-Optimizer |
| CloudFormation stack | `portfolio-optimizer` |
| AWS Region | `ap-south-1` |
| Docker service | `frontend` |
| Container | `portfolio-dashboard` |
| Application port | `8501` |
| Persistent directory | `/data` |
| SQLite database | `/data/portfolio_optimizer.db` |
| FAISS index | `/data/faiss_index` |

The product, repository, CloudFormation stack, and Docker service do not need to have identical names. They serve different purposes.

Deployment resources:

- [CloudFormation template](deploy/aws/ec2-stack.yaml)
- [AWS deployment guide](deploy/aws/README.md)

### Validate the CloudFormation template

```powershell
$Region = "ap-south-1"

aws cloudformation validate-template `
  --region $Region `
  --template-body file://deploy/aws/ec2-stack.yaml
```

### Deploy the stack

Replace the example networking and key-pair values:

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

### Get stack outputs

```powershell
aws cloudformation describe-stacks `
  --region $Region `
  --stack-name portfolio-optimizer `
  --query "Stacks[0].Outputs" `
  --output table
```

### Connect to the EC2 instance

```powershell
$PemPath = "$env:USERPROFILE\.ssh\portfolio-optimizer-key.pem"
$PublicIp = "YOUR_EC2_PUBLIC_IP"

ssh -i $PemPath "ec2-user@$PublicIp"
```

After entering the EC2 server:

```bash
cd /opt/portfolio
sudo docker compose ps
sudo docker compose logs --tail=200 frontend
curl -f http://localhost:8501/_stcore/health
```

Commands under `/opt/portfolio` must run inside the EC2 SSH session, not in Windows PowerShell.

## Optional API service

The repository may also run a FastAPI service when the API profile and corresponding backend files are enabled.

Start it with Docker Compose:

```bash
docker compose --profile api up --build -d
```

When configured, the API is normally available at:

```text
http://localhost:8000
```

API documentation is normally available at:

```text
http://localhost:8000/docs
```

The current public AWS demo uses the Streamlit single-host deployment. Verify the backend routes in `backend/app/` and `docs/api_reference.md` before publishing endpoint-specific guarantees.

## Database and persistence

The Streamlit container uses:

```env
DB_DIR=/data
FAISS_INDEX_PATH=/data/faiss_index
```

Docker Compose mounts a named volume at `/data`. This allows the SQLite database and FAISS index to survive container rebuilds and recreation.

Primary entities include:

- users
- portfolios
- holdings
- optimization runs
- sentiment results
- AI recommendations
- risk reports

SQLite is suitable for the current single-host demonstration. PostgreSQL is recommended for higher concurrency, managed backups, and multi-instance deployment.

## Testing

Run the test suite:

```bash
pytest tests -v
```

Compile-check the Python application:

```bash
python -m compileall -q frontend src
```

Useful deployment smoke tests:

```bash
docker compose ps
curl -f http://localhost:8501/_stcore/health
docker compose logs --tail=200 frontend
```

Recommended test coverage includes:

- return calculations and weight normalization
- optimizer constraints
- Value at Risk and drawdown calculations
- sentiment-score aggregation
- API-client failure handling
- database transactions and persistence
- RAG initialization and fallback behavior
- report generation and HTML escaping
- Docker health checks

## Verified walk-forward backtest

A reproducible price-only walk-forward backtest evaluates the quantitative optimizer, monthly equal weight, and the S&P 500 benchmark from 4 January 2021 through 31 December 2025.

Configuration:

- assets: `AAPL`, `MSFT`, `GOOGL`, `AMZN`, `META`
- benchmark: `^GSPC`
- lookback: 252 trading days
- rebalance frequency: monthly
- annual risk-free rate: 5%
- weight range: 2% minimum and 35% maximum
- transaction cost: 15 basis points per traded notional

| Metric | AXIOM combined | Quantitative only | Equal weight | Benchmark |
| --- | ---: | ---: | ---: | ---: |
| CAGR | Not measured* | 16.83% | 20.59% | 13.12% |
| Annualized volatility | Not measured* | 26.51% | 26.76% | 16.96% |
| Sharpe ratio | Not measured* | 0.531 | 0.648 | 0.519 |
| Sortino ratio | Not measured* | 0.790 | 0.909 | 0.712 |
| Maximum drawdown | Not measured* | -39.63% | -46.55% | -25.43% |
| Annual turnover | Not measured* | 174.27% | 25.04% | N/A |
| Transaction-cost drag | Not measured* | 3.84% | 0.55% | 0.00% |

*AXIOM combined is not measured because the repository does not yet contain a point-in-time historical news and sentiment dataset. Current news must not be used to simulate past decisions.*

Equal weighting produced the strongest CAGR and Sharpe ratio for this concentrated large-cap technology universe. Quantitative MPT reduced maximum drawdown relative to equal weight but generated materially higher turnover and transaction costs. The diversified S&P 500 benchmark produced the lowest volatility and drawdown.

Annual turnover uses the standard one-way definition:

`turnover = 0.5 × Σ |target weight − pre-trade weight|`

Transaction costs use the complete traded notional across purchases and sales. See [backtesting.md](backtesting.md) for methodology, limitations, and reproducibility requirements.

> Historical performance does not guarantee future results. The backtest is provided for research and educational use only.

## Security notes

- Never commit `.env`, `.pem`, access keys, or API keys.
- Rotate any credential that has been exposed in logs, screenshots, or commit history.
- Use AWS Secrets Manager or Systems Manager Parameter Store for production secrets.
- Use an IAM role instead of long-lived AWS access keys on EC2.
- Restrict ports `22` and `8501` to trusted CIDR ranges during development.
- Use HTTPS and a stable domain before treating the dashboard as a public service.
- Use Argon2id or bcrypt for password hashing rather than general-purpose hashing.
- Treat retrieved news as untrusted input and escape article content in HTML reports.
- RAG reduces unsupported output but does not eliminate hallucination.

## Known limitations

- Historical return and covariance estimates may not represent future market behavior.
- Optimized weights can be sensitive to estimation error and the selected time window.
- News availability depends on the external provider and API plan.
- FinBERT sentiment may misinterpret ambiguous headlines or unusual market language.
- LLM recommendations may be incomplete or incorrect even when context is retrieved.
- The current AWS deployment uses a single EC2 instance and is not highly available.
- SQLite is not designed for high-concurrency, horizontally scaled deployment.
- A public EC2 IP is not a stable production URL unless an Elastic IP or domain is configured.
- The current live URL uses HTTP rather than HTTPS.
- Small EC2 instances may experience slow FinBERT loading or analysis latency.

## Roadmap

- [ ] Add a stable domain and HTTPS
- [ ] Store secrets in AWS Secrets Manager or SSM Parameter Store
- [ ] Add CloudWatch logs, metrics, dashboards, and alarms
- [ ] Pin and continuously test dependency versions
- [ ] Add walk-forward backtesting with transaction costs
- [ ] Add covariance shrinkage and robust allocation objectives
- [ ] Add PostgreSQL migrations and managed backups
- [ ] Add RAG retrieval and groundedness evaluation
- [ ] Add source citations to generated recommendations
- [ ] Add immutable run metadata, model versions, and container image identifiers
- [ ] Add CI/CD deployment with health-gated rollback
- [ ] Replace the single-host design with managed services if usage grows

## Documentation

Additional documentation is available in:

- [Setup guide](docs/setup.md)
- [Architecture overview](docs/architecture.md)
- [API reference](docs/api_reference.md)
- [AWS deployment guide](deploy/aws/README.md)

## Contributing

Contributions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make focused changes.
4. Add or update tests.
5. Run the test suite locally.
6. Open a pull request with a clear description.

Please avoid committing credentials, private portfolio data, generated databases, large model artifacts, or private keys.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

AXIOM Portfolio Intelligence builds on open-source tools and research from the Python, Streamlit, Hugging Face, FAISS, LangChain, Groq, Docker, and quantitative-finance communities.

If you use this project for learning or research, please reference the repository:

```text
Parmod K. — AXIOM Portfolio Intelligence
AI-Powered Portfolio Optimization and Research Platform
https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer
```
