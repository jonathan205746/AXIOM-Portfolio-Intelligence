# AWS deployment: single EC2 host

This is the recommended first AWS deployment for this repository. It runs the existing Streamlit Docker image on one Amazon Linux 2023 EC2 host and keeps the application's SQLite database and FAISS index on the encrypted EBS root volume.

It is intentionally a single-host deployment: the application currently uses local SQLite/FAISS storage, so services such as App Runner or ECS without an attached persistent volume are not a suitable drop-in deployment.

## Before you begin

Install and configure AWS CLI v2, then create an EC2 key pair in your selected Region. Use a public subnet in a VPC with Internet access and automatic public IPv4 assignment.

The default `t3.large` is the safer choice for Streamlit plus FinBERT. `t3.medium` can be used for a short dashboard-only demo, but may be constrained while the model is loading or running an analysis.

Create local secrets without committing them:

```powershell
Copy-Item .env.example .env
```

Set `NEWS_API_KEY` and `GROQ_API_KEY` if you want news retrieval and LLM recommendations. The app runs without them, but with reduced functionality.

## Deploy

1. Find your public IPv4 address and choose a Region. This example uses Mumbai (`ap-south-1`).

```powershell
$Region = 'ap-south-1'
$MyIp = (Invoke-RestMethod 'https://checkip.amazonaws.com').Trim()
```

2. List VPCs and public subnets, then note the IDs you want to use.

```powershell
aws ec2 describe-vpcs --region $Region --query 'Vpcs[].{Id:VpcId,Default:IsDefault}' --output table
aws ec2 describe-subnets --region $Region --query 'Subnets[].{Id:SubnetId,Vpc:VpcId,Az:AvailabilityZone}' --output table
```

3. Create the CloudFormation stack. Replace the VPC, subnet, and key-pair values.

```powershell
aws cloudformation deploy `
  --region $Region `
  --stack-name portfolio-optimizer `
  --template-file deploy/aws/ec2-stack.yaml `
  --parameter-overrides `
    VpcId=vpc-xxxxxxxx `
    SubnetId=subnet-xxxxxxxx `
    KeyName=your-key-pair `
    AllowedCidr="$MyIp/32"
```

4. Wait about 10–20 minutes for Docker to build the image. Read the dashboard address from the stack output.

```powershell
aws cloudformation describe-stacks --region $Region --stack-name portfolio-optimizer `
  --query 'Stacks[0].Outputs' --output table
```

5. Copy the local `.env` file to the instance, then restart the dashboard to load its secrets.

```powershell
scp -i .\your-key-pair.pem .env ec2-user@PUBLIC_IP:/opt/portfolio/.env
ssh -i .\your-key-pair.pem ec2-user@PUBLIC_IP `
  'cd /opt/portfolio && docker compose up -d --force-recreate frontend'
```

Open the `DashboardUrl` output in your browser. The security group permits ports 22 and 8501 only from your public IP; do not broaden SSH to `0.0.0.0/0`.

## Verify and troubleshoot

```bash
ssh -i your-key-pair.pem ec2-user@PUBLIC_IP
cd /opt/portfolio
docker compose ps
docker compose logs -f frontend
curl -f http://localhost:8501/_stcore/health
sudo tail -n 200 /var/log/portfolio-bootstrap.log
```

The first optimization can take several minutes because the FinBERT model is downloaded and cached.

## Updating the app

Push changes to the configured branch, then on the instance:

```bash
cd /opt/portfolio
git pull --ff-only
docker compose up --build -d
```

## Cost and cleanup

You pay for EC2, EBS, and public IPv4 while the instance is running. Stop the instance when unused:

```powershell
aws ec2 stop-instances --region $Region --instance-ids i-xxxxxxxx
```

The template keeps the EBS volume after stack deletion (`DeleteOnTermination: false`), protecting SQLite/FAISS data. Delete that volume manually only after you have a backup.

For a shared or production deployment, put the app behind HTTPS (for example, an Application Load Balancer with ACM), move SQLite to RDS, and store secrets in Secrets Manager or Parameter Store.
