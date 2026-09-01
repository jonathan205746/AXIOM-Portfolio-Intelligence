# Cheapest demo: one EC2 host in `ap-south-1`

Streamlit is the app users open. FastAPI is optional and **doubles RAM** (second PyTorch process). Default Compose starts Streamlit only.

| Instance | RAM | Use |
|---|---|---|
| **t3.medium** | 4 GB | Dashboard only (`docker compose up`) |
| t3.large | 8 GB | Dashboard + API (`docker compose --profile api up`) |

Leave it running 24/7 in Mumbai and expect roughly **$35–45/month** (instance + 30 GB gp3 + public IPv4). Stop the instance when you are not demoing.

## 1. One-time on your laptop

- AWS CLI configured for an account that can create EC2 in `ap-south-1`
- An EC2 key pair **in `ap-south-1`**
- A `.env` copied from `.env.example` (never commit it)

```powershell
copy .env.example .env
# fill NEWS_API_KEY, GROQ_API_KEY; for the API profile also set SECRET_KEY
```

Generate `SECRET_KEY` if you will start the API:

```powershell
python -c "import secrets; print(secrets.token_hex(32))"
```

## 2. Launch the instance

```powershell
$env:KEY_NAME = "your-ap-south-1-keypair"
.\deploy\ec2\launch.ps1
```

The script opens SSH, Streamlit (`8501`), and API (`8000`) **only from your current public IP**. First boot takes a few minutes (Docker install).

## 3. Copy the project and start Compose

```bash
ssh -i your-ap-south-1-keypair.pem ec2-user@PUBLIC_IP
sudo yum install -y git   # if user-data has not finished
# wait until: docker compose version

sudo mkdir -p /opt/portfolio
sudo chown ec2-user:ec2-user /opt/portfolio
cd /opt/portfolio
git clone https://github.com/Parmodk2310/AI-Powered-Portfolio-Optimizer.git .
```

Upload `.env` from your PC (Git will not contain secrets):

```powershell
scp -i your-ap-south-1-keypair.pem .env ec2-user@PUBLIC_IP:/opt/portfolio/.env
```

On the instance:

```bash
cd /opt/portfolio
docker compose up --build -d
docker compose logs -f frontend
```

Open `http://PUBLIC_IP:8501`. First analysis can take several minutes while FinBERT downloads.

Optional mobile API (needs **t3.large**):

```bash
docker compose --profile api up --build -d
```

API docs: `http://PUBLIC_IP:8000/docs`

## 4. Stop paying when idle

```powershell
aws ec2 stop-instances --region ap-south-1 --instance-ids i-xxxxxxxx
aws ec2 start-instances --region ap-south-1 --instance-ids i-xxxxxxxx
```

Stopped instances still charge a little for the EBS volume. Terminate the instance to stop almost all of it (the Docker volume / SQLite data is deleted with the disk).

## Notes

- Analysis runs **inside Streamlit**, not via `API_BASE_URL`. The API container is only for a Flutter/JWT client.
- SQLite and FAISS live in the `app-data` Docker volume. They survive `compose restart` but not instance terminate unless you snapshot the volume.
- Do not open `0.0.0.0/0` on port 22. If you must share the demo, open **8501** to the world and keep SSH locked to your IP.
