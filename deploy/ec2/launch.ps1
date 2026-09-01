# Launch a cheapest-demo EC2 host in ap-south-1 and print SSH / next steps.
# Prerequisites: AWS CLI v2, a key pair in ap-south-1, and an IAM principal that can run EC2.
#
# Usage (PowerShell):
#   $env:KEY_NAME = "your-ap-south-1-keypair"
#   .\deploy\ec2\launch.ps1
#
# Optional:
#   $env:MY_IP = "1.2.3.4"            # defaults to your current public IP
#   $env:INSTANCE_TYPE = "t3.medium"  # t3.large if you will enable the api compose profile

$ErrorActionPreference = "Stop"

$Region = "ap-south-1"
$KeyName = $env:KEY_NAME
if (-not $KeyName) {
    Write-Error "Set KEY_NAME to an existing EC2 key pair in ap-south-1."
}

$InstanceType = if ($env:INSTANCE_TYPE) { $env:INSTANCE_TYPE } else { "t3.medium" }
$MyIp = $env:MY_IP
if (-not $MyIp) {
    $MyIp = (Invoke-RestMethod -Uri "https://checkip.amazonaws.com").Trim()
}
$Cidr = "$MyIp/32"

Write-Host "Region=$Region InstanceType=$InstanceType SSH/app CIDR=$Cidr"

$Ami = aws ssm get-parameter `
    --region $Region `
    --name "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64" `
    --query "Parameter.Value" `
    --output text
if ($LASTEXITCODE -ne 0 -or -not $Ami) {
    Write-Error "Could not resolve Amazon Linux 2023 AMI. Is AWS CLI configured?"
}

$VpcId = aws ec2 describe-vpcs `
    --region $Region `
    --filters "Name=isDefault,Values=true" `
    --query "Vpcs[0].VpcId" `
    --output text
if ($LASTEXITCODE -ne 0 -or -not $VpcId -or $VpcId -eq "None") {
    Write-Error "No default VPC in ap-south-1. Create a VPC or pick a subnet manually."
}

$GroupId = aws ec2 describe-security-groups `
    --region $Region `
    --filters "Name=group-name,Values=portfolio-demo-sg" "Name=vpc-id,Values=$VpcId" `
    --query "SecurityGroups[0].GroupId" `
    --output text

if (-not $GroupId -or $GroupId -eq "None") {
    $GroupId = aws ec2 create-security-group `
        --region $Region `
        --group-name portfolio-demo-sg `
        --description "Portfolio optimizer demo (SSH + Streamlit + optional API)" `
        --vpc-id $VpcId `
        --query GroupId `
        --output text
    if ($LASTEXITCODE -ne 0) { Write-Error "Failed to create security group." }
}

function Add-Ingress([int]$Port) {
    aws ec2 authorize-security-group-ingress `
        --region $Region `
        --group-id $GroupId `
        --protocol tcp `
        --port $Port `
        --cidr $Cidr | Out-Null
}

Add-Ingress 22
Add-Ingress 8501
Add-Ingress 8000

$UserDataUnix = (Get-Content -Raw (Join-Path $PSScriptRoot "user-data.sh")) -replace "`r`n", "`n"
$UserDataFile = Join-Path $env:TEMP "portfolio-ec2-user-data.sh"
[System.IO.File]::WriteAllText($UserDataFile, $UserDataUnix)
$UserDataUri = "file://" + ($UserDataFile -replace "\\", "/")

$InstanceId = aws ec2 run-instances `
    --region $Region `
    --image-id $Ami `
    --instance-type $InstanceType `
    --key-name $KeyName `
    --security-group-ids $GroupId `
    --user-data $UserDataUri `
    --block-device-mappings "DeviceName=/dev/xvda,Ebs={VolumeSize=30,VolumeType=gp3,Encrypted=true,DeleteOnTermination=true}" `
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=portfolio-demo}]" `
    --query "Instances[0].InstanceId" `
    --output text
if ($LASTEXITCODE -ne 0 -or -not $InstanceId) {
    Write-Error "run-instances failed."
}

Write-Host "Waiting for $InstanceId to be running..."
aws ec2 wait instance-running --region $Region --instance-ids $InstanceId
aws ec2 wait instance-status-ok --region $Region --instance-ids $InstanceId

$PublicIp = aws ec2 describe-instances `
    --region $Region `
    --instance-ids $InstanceId `
    --query "Reservations[0].Instances[0].PublicIpAddress" `
    --output text

Write-Host ""
Write-Host "Instance: $InstanceId"
Write-Host "Public IP: $PublicIp"
Write-Host "SSH: ssh -i `"$KeyName.pem`" ec2-user@$PublicIp"
Write-Host "Next: copy the repo and .env, then docker compose up --build -d"
Write-Host "Dashboard will be http://${PublicIp}:8501"
Write-Host "Stop billing: aws ec2 stop-instances --region $Region --instance-ids $InstanceId"
