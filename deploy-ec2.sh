#!/bin/bash
set -e

# ── CONFIG ─────────────────────────────────────────────────
KEY_NAME="portfolio-key"          # Change to your existing AWS KeyPair name
REGION="us-east-1"
INSTANCE_TYPE="t3.medium"         # 2 vCPU, 4 GB RAM ($30/mo)
VOLUME_SIZE=30                    # GB

# ── Create Security Group ─────────────────────────────────
SG_NAME="portfolio-sg"
SG_ID=$(aws ec2 create-security-group \
  --group-name $SG_NAME \
  --description "Portfolio Optimizer" \
  --query 'GroupId' --output text 2>/dev/null || \
  aws ec2 describe-security-groups --group-names $SG_NAME --query 'SecurityGroups[0].GroupId' --output text)

echo "Security Group: $SG_ID"

# Open ports
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 22 --cidr 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8080 --cidr 0.0.0.0/0 2>/dev/null || true
aws ec2 authorize-security-group-ingress --group-id $SG_ID --protocol tcp --port 8501 --cidr 0.0.0.0/0 2>/dev/null || true

# ── Launch Instance ───────────────────────────────────────
AMI_ID=$(aws ssm get-parameters --names /aws/service/canonical/ubuntu/server/22.04/stable/current/amd64/hvm/ebs-gp2/ami-id --query 'Parameters[0].Value' --output text)

USER_DATA=$(cat <<'EOF'
#!/bin/bash
exec > >(tee /var/log/user-data.log) 2>&1

# Install Docker
apt-get update
apt-get install -y docker.io docker-compose git curl
systemctl enable docker
systemctl start docker
usermod -aG docker ubuntu

# Clone repo
cd /opt
git clone https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer.git app
cd app

# Write env file
cat > .env << 'ENVEOF'
NEWS_API_KEY_1=your-first-key-here
NEWS_API_KEY_2=your-second-key-here
GROQ_API_KEY=your-groq-key-here
GEMINI_API_KEY=your-gemini-key-here
ENVEOF

# Fix port mapping and run
cp docker-compose.aws.yml docker-compose.yml
docker-compose up -d --build

echo "Deploy complete at $(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
EOF
)

INSTANCE_ID=$(aws ec2 run-instances \
  --image-id $AMI_ID \
  --count 1 \
  --instance-type $INSTANCE_TYPE \
  --key-name $KEY_NAME \
  --security-group-ids $SG_ID \
  --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$VOLUME_SIZE,VolumeType=gp3}" \
  --user-data "$USER_DATA" \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=portfolio-optimizer}]' \
  --query 'Instances[0].InstanceId' --output text)

echo "Launching instance: $INSTANCE_ID"
echo "Waiting for public IP..."

PUBLIC_IP=$(aws ec2 describe-instances \
  --instance-ids $INSTANCE_ID \
  --query 'Reservations[0].Instances[0].PublicIpAddress' --output text)

echo ""
echo "============================================================"
echo "  Instance ID: $INSTANCE_ID"
echo "  Public IP:   $PUBLIC_IP"
echo ""
echo "  API:         http://$PUBLIC_IP:8080/health"
echo "  Dashboard:   http://$PUBLIC_IP:8501"
echo ""
echo "  SSH:         ssh -i ~/.ssh/$KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo "  Logs:        ssh ... 'tail -f /var/log/user-data.log'"
echo "============================================================"