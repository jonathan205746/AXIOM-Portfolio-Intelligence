# AXIOM — Play Store Compliance Implementation Guide

Step-by-step runbooks for each launch-blocking requirement.

---

## 1. Privacy Policy, Terms & Account Deletion Pages

### 1.1 Create the Content

**Files to create in your repo:**
```
docs/legal/
├── privacy-policy.md
├── terms-of-service.md
└── account-deletion.md
```

**Privacy Policy Template (DPDP Act 2023 compliant):**
```markdown
# AXIOM Portfolio Intelligence — Privacy Policy
Effective: 2026-09-29 | Version 1.0

## 1. Data Fiduciary
**Entity:** Parmod Kumar (Individual Developer)
**Contact:** privacy@axiom.example.com
**Grievance Officer:** grievance@axiom.example.com

## 2. Personal Data Collected
| Category | Data Points | Purpose | Legal Basis |
|----------|-------------|---------|-------------|
| Account | Username, email, bcrypt password hash | Authentication | Consent (Art 7) |
| Portfolio | Portfolio names, stock tickers, quantities, buy prices, currency | Analytics | Consent + Legitimate Interest |
| Usage | API request logs (IP, request ID, timestamps), device info | Security, debugging | Legitimate Interest |
| AI Commentary | Portfolio tickers, weights, news headlines (sent to Groq) | LLM commentary | Explicit consent |

## 3. Data Processing
- **No automated decision-making** affecting legal rights
- **No profiling** beyond portfolio risk scoring
- **Third-party processors:** AWS (hosting), Groq (LLM), NewsAPI (news)
- **Cross-border transfers:** Groq (US) → SCCs in place

## 4. Retention
| Data | Retention | Deletion Trigger |
|------|-----------|------------------|
| Account credentials | Until account deletion | User request |
| Portfolio data | Until account deletion | User request |
| API logs | 180 days | Auto-expiry (CERT-In) |
| AI commentary cache | 30 days | Auto-expiry |

## 5. User Rights (DPDP Act Sections 11-14)
- **Access:** Export via Settings → Export My Data
- **Correction:** Edit profile in Settings
- **Erasure:** Settings → Delete Account (in-app) or https://axiom.example.com/account-deletion
- **Grievance:** grievance@axiom.example.com (24h ack, 30-day resolution)

## 6. Security
- bcrypt password hashing
- JWT (30min access, 30-day refresh, rotation)
- TLS 1.3 in transit, AES-256 at rest
- OWASP MASVS Level 2 tested

## 7. Children
App not directed to children under 18. No knowingly collected data from minors.

## 8. Changes
Material changes notified via email + in-app banner 30 days prior.
```

### 1.2 Host Publicly (Free Options)

**Option A: GitHub Pages (Recommended)**
```bash
# 1. Create legal site
mkdir -p docs/legal
# Copy privacy-policy.md, terms-of-service.md, account-deletion.md to docs/legal/

# 2. Add mkdocs.yml
cat > mkdocs.yml <<'EOF'
site_name: AXIOM Legal
theme:
  name: material
nav:
  - Privacy Policy: legal/privacy-policy.md
  - Terms of Service: legal/terms-of-service.md
  - Account Deletion: legal/account-deletion.md
EOF

# 3. Deploy
pip install mkdocs-material
mkdocs gh-deploy
```
**Result:** `https://parmodk2310.github.io/AXIOM-Portfolio-Intelligence/legal/privacy-policy/`

**Option B: Netlify/Vercel (Static HTML)**
```bash
# Convert .md to HTML
pip install markdown
for f in docs/legal/*.md; do
  markdown "$f" > "${f%.md}.html"
done
# Push to GitHub → Connect to Netlify → Auto-deploy
```

**Option C: Your own domain**
- Point `legal.axiom.example.com` to GitHub Pages/Netlify
- Update `AppConfig.webBaseUrl` in Flutter

### 1.3 Verify URLs Work
```bash
curl -I https://your-domain.com/legal/privacy-policy/
# Must return 200 OK, not 404
```

---

## 2. Play Console Data Safety Form

### 2.1 Open the Form
1. Play Console → **Your App** → **App Content** → **Data Safety**
2. Click **Start** / **Next**

### 2.2 Section-by-Section Answers

#### **Data Collection: YES**
| Data Type | Collected? | Purpose | Shared? | Ephemeral? |
|-----------|------------|---------|---------|------------|
| **Personal Info** | | | | |
| Name (username) | Yes | Account management | No | No |
| Email address | Yes | Account recovery, notifications | No | No |
| **Financial Info** | | | | |
| Portfolio holdings (tickers, quantities, prices) | Yes | Analytics, optimization | No* | No |
| *Groq receives tickers + weights for AI commentary (disclosed) | | | **Yes** | No |
| **App Activity** | | | | |
| In-app actions (analysis runs, portfolio changes) | Yes | Analytics, debugging | No | No |
| **Device/Network** | | | | |
| IP address, device model, OS version | Yes (logs) | Security, fraud prevention | No | Yes (180-day auto-delete) |
| Crash logs | Yes | Stability | No | Yes (90-day) |

#### **Security Practices**
- ✅ Data encrypted in transit (TLS 1.3)
- ✅ Data encrypted at rest (AES-256, bcrypt)
- ✅ User can request deletion (in-app + web)
- ✅ Independent security audit (OWASP MASVS)

#### **Data Sharing**
- **No** sale of data
- **Yes** shared with: Groq (LLM commentary), NewsAPI (news fetch)
- **No** shared for advertising/marketing

### 2.3 Submit
- Review → **Save** → **Publish**

---

## 3. Financial Features Declaration

### 3.1 Open the Form
Play Console → **App Content** → **Financial Features** → **Declare**

### 3.2 Select Categories
```
☑ Stock trading and portfolio management
   └ "Portfolio tracking, analytics, risk metrics, AI commentary — no trade execution"

☐ Financial advice
☐ Payments / Money transfer
☐ Lending / Credit
☐ Insurance
☐ Cryptocurrency
☐ Other financial services
```

### 3.3 Additional Questions
| Question | Answer |
|----------|--------|
| Does your app execute trades? | **No** |
| Does your app hold user funds? | **No** |
| Does your app provide personalized investment advice? | **No** — algorithmic portfolio optimization only |
| Is your app registered with SEBI/RBI? | **Not required** (educational/research tool) |
| Target audience | **Adults (18+)** |
| Countries | India + others |

### 3.4 Save & Verify
- Status should show **"Declared"**

---

## 4. Closed Testing: 12 Testers × 14 Days

### 4.1 Prerequisites
- Play Console account with **Production access** (personal accounts after Nov 2023 require this)
- App Bundle (.aab) uploaded to **Internal Testing** first

### 4.2 Step-by-Step

**Step 1: Upload to Internal Testing**
```bash
cd AXIOM-Portfolio-Intelligence/mobile
flutter build appbundle --release
# Output: build/app/outputs/bundle/release/app-release.aab
```
1. Play Console → **Testing** → **Internal Testing**
2. **Create new release** → Upload `app-release.aab`
3. Add **up to 100 internal testers** (emails)
4. **Save & Roll out**

**Step 2: Promote to Closed Testing**
1. Play Console → **Testing** → **Closed Testing** → **Create track** (name: "closed-testing")
2. **Create release** → Select same AAB from Internal Testing (or re-upload)
3. **Testers:** Add **12+ testers** (Google accounts)
   - Use **"Create email list"** → Add 12 emails
   - Or share **opt-in link** with testers
4. **Save & Roll out to 100%**

**Step 3: Meet 14-Day Requirement**
- Testers must **opt-in and install** via Play Store link
- **14 continuous days** with ≥12 active testers
- Monitor: **Testing** → **Closed Testing** → **Statistics**

**Step 4: Apply for Production Access**
Once 14-day requirement met:
1. Play Console → **Testing** → **Closed Testing** → **Apply for production access**
2. Fill declaration form
3. Wait for Google review (1-3 days)

### 4.3 Recruiting Testers (India)
- Post in Indian dev communities: r/IndiaDev, r/FlutterDev, Discord servers
- Offer: "Early access to AXIOM Portfolio Intelligence — portfolio analytics app"
- Provide: Test Google account emails, clear instructions

---

## 5. 180-Day Log Retention (CloudWatch → S3 Glacier)

### 5.1 Architecture
```
EC2 / ECS / EKS (AXIOM containers)
    │ CloudWatch Agent
    ▼
CloudWatch Log Groups (/axiom/frontend, /axiom/api)
    │ Subscription Filter (Lambda or Kinesis Firehose)
    ▼
S3 Bucket (axiom-logs-prod)
    │ Lifecycle Policy
    ▼
S3 Glacier Instant Retrieval (Day 30) → Glacier Deep Archive (Day 180)
```

### 5.2 Terraform / CloudFormation (Recommended)

**CloudFormation Snippet:**
```yaml
Resources:
  AxiomLogBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: axiom-logs-prod-ap-south-1
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: TransitionToGlacierIR
            Status: Enabled
            Transitions:
              - StorageClass: GLACIER_IR
                TransitionInDays: 30
          - Id: TransitionToDeepArchive
            Status: Enabled
            Transitions:
              - StorageClass: DEEP_ARCHIVE
                TransitionInDays: 180
          - Id: ExpireOldLogs
            Status: Enabled
            ExpirationInDays: 5475  # 15 years max
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256

  CloudWatchLogGroupFrontend:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /axiom/frontend
      RetentionInDays: 180  # CloudWatch retains 180 days hot

  CloudWatchLogGroupApi:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: /axiom/api
      RetentionInDays: 180

  SubscriptionFilterFrontend:
    Type: AWS::Logs::SubscriptionFilter
    Properties:
      LogGroupName: !Ref CloudWatchLogGroupFrontend
      FilterPattern: ""  # All logs
      DestinationArn: !GetAtt FirehoseDeliveryStream.Arn

  FirehoseDeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamName: axiom-logs-to-s3
      DeliveryStreamType: DirectPut
      S3DestinationConfiguration:
        BucketARN: !GetAtt AxiomLogBucket.Arn
        BufferingHints:
          IntervalInSeconds: 300
          SizeInMBs: 50
        CompressionFormat: GZIP
        Prefix: frontend/
        RoleARN: !GetAtt FirehoseRole.Arn
```

### 5.3 Deploy via AWS Console (No IaC)
1. **S3 Console** → Create bucket `axiom-logs-prod-ap-south-1`
2. **Lifecycle Rules** → Add transitions (Glacier IR at 30d, Deep Archive at 180d)
3. **CloudWatch Logs** → Log Groups → `/axiom/frontend`, `/axiom/api`
4. **Subscription Filters** → Create → Destination: **Kinesis Firehose**
5. **Kinesis Firehose** → Create delivery stream → S3 destination → `axiom-logs-prod-ap-south-1`

### 5.4 Verify
```bash
# Check logs flowing
aws s3 ls s3://axiom-logs-prod-ap-south-1/frontend/ --recursive | head -5

# Test query via Athena (optional)
# CREATE EXTERNAL TABLE axiom_logs (...) LOCATION 's3://axiom-logs-prod-ap-south-1/'
```

---

## 6. Incident Response Runbook (6-Hour CERT-In Reporting)

### 6.1 Runbook Document
**File:** `docs/security/incident-response-runbook.md`

```markdown
# AXIOM Incident Response Runbook (CERT-In Compliant)
Version: 1.0 | Owner: Security Lead | Review: Quarterly

## 1. Classification & SLA
| Severity | Definition | CERT-In Report | Resolution SLA |
|----------|------------|----------------|----------------|
| **SEV-1** (Critical) | Data breach, unauthorized access to PII/financial data, service compromise | **Within 6 hours** | 4 hours |
| **SEV-2** (High) | Vulnerability exploit attempt, DoS, authentication bypass | Within 6 hours if data exposed | 24 hours |
| **SEV-3** (Medium) | Failed auth spikes, config drift, non-critical vuln | Internal only | 72 hours |

## 2. Detection Sources
- CloudWatch Alarms (auth failures > 10/min, 5xx > 5%)
- GitHub Dependabot / Trivy alerts
- User reports (in-app, email)
- AWS GuardDuty / Security Hub findings

## 3. 6-Hour Reporting Checklist (SEV-1/2)
**T+0** — Detection
- [ ] Acknowledge alert (Slack #security-alerts)
- [ ] Assign Incident Commander (IC)
- [ ] Create incident channel: `#incident-YYYYMMDD-XXX`

**T+15min** — Triage
- [ ] Confirm scope: Which data? How many users?
- [ ] Contain: Revoke tokens, rotate keys, block IPs
- [ ] Preserve evidence: Snapshot logs, DB, containers

**T+1hr** — CERT-In Notification
- [ ] Email: `incident@cert-in.org.in`
- [ ] Format (per CERT-In template):
  ```
  Subject: [CERT-In] Security Incident - AXIOM Portfolio Intelligence - SEV-1
  Body:
  1. Organization: Parmod Kumar (Individual Developer)
  2. Date/Time of Detection: YYYY-MM-DD HH:MM IST
  3. Type of Incident: [Unauthorized Access / Data Breach / Malware / DoS]
  4. Affected Systems: [EC2 i-xxx, RDS db-xxx, S3 bucket]
  5. Data Categories Affected: [Email, Portfolio Holdings, Auth Tokens]
  6. Number of Users Affected: [Count or "Under investigation"]
  7. Root Cause (preliminary): [e.g., Exposed JWT secret in logs]
  8. Containment Actions Taken: [Key rotation, IP block, token revocation]
  9. Remediation Plan: [Timeline, owner]
  10. Contact: [Name, Phone, Email of IC]
  ```

**T+2hr** — User Notification (if PII exposed)
- [ ] Email affected users (template in `/docs/templates/breach-notification.md`)
- [ ] In-app banner notification

**T+6hr** — CERT-In Follow-up
- [ ] Submit detailed incident report via CERT-In portal
- [ ] Attach forensic artifacts (log exports, memory dumps)

## 4. Key Contacts
| Role | Name | Phone | Email | Slack |
|------|------|-------|-------|-------|
| Incident Commander (Primary) | Parmod Kumar | +91-XXXXX-XXXXX | security@axiom.example.com | @parmod |
| Incident Commander (Backup) | [Backup] | +91-XXXXX-XXXXX | backup@axiom.example.com | @backup |
| AWS Support | Enterprise | - | - | Case in AWS Console |
| Legal Counsel | [Firm] | +91-XXXXX-XXXXX | legal@axiom.example.com | - |

## 5. Evidence Preservation
```bash
# Export CloudWatch logs for time range
aws logs filter-log-events \
  --log-group-name /axiom/api \
  --start-time $(date -d '2 hours ago' +%s)000 \
  --end-time $(date +%s)000 \
  > incident-logs.json

# Export RDS snapshot
aws rds create-db-snapshot \
  --db-instance-identifier axiom-prod \
  --db-snapshot-identifier axiom-incident-$(date +%Y%m%d-%H%M)

# Export ECS task metadata
aws ecs describe-tasks --cluster axiom-prod --tasks $(aws ecs list-tasks --cluster axiom-prod --query 'taskArns[]' --output text)
```

## 6. Post-Incident (Within 30 Days)
- [ ] Root Cause Analysis (5 Whys)
- [ ] Remediation tickets in GitHub
- [ ] Update runbook
- [ ] Tabletop exercise
```

### 6.2 Deploy Alerting
```bash
# CloudWatch Alarm for auth failures
aws cloudwatch put-metric-alarm \
  --alarm-name "AXIOM-AuthFailures-High" \
  --metric-name "AuthFailures" \
  --namespace "AXIOM/Security" \
  --statistic Sum \
  --period 60 \
  --evaluation-periods 5 \
  --threshold 50 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:ap-south-1:123456789012:security-alerts

# SNS Topic for alerts
aws sns create-topic --name security-alerts
aws sns subscribe --topic-arn arn:aws:sns:... --protocol email --notification-endpoint security@axiom.example.com
```

---

## 7. Groq DPA / SCCs Documentation

### 7.1 Obtain Documents
1. **Log into Groq Console** → Settings → Legal / Compliance
2. **Download:**
   - Data Processing Addendum (DPA)
   - Standard Contractual Clauses (SCCs) — 2021 EU SCCs (valid for India transfer)
   - SOC 2 Type II Report (if available)

### 7.2 Document in Repo
**File:** `docs/security/groq-compliance.md`

```markdown
# Groq Cross-Border Transfer Compliance

## 1. Processor Details
- **Processor:** Groq Inc.
- **Address:** 251 Littlefield Drive, Mountain View, CA 94043, USA
- **Service:** GroqCloud LLM API (Llama 3 models)
- **Data Categories:** Portfolio tickers, weights, news headlines (no PII)

## 2. Legal Basis
- **DPA Signed:** Yes (Date: 2026-09-XX)
- **SCCs:** 2021 EU SCCs (Module 2: Controller → Processor)
- **Supplementary Measures:** TLS 1.3, API key rotation, no PII sent

## 3. DPA Key Terms
| Clause | Status |
|--------|--------|
| Purpose limitation | ✅ AI commentary only |
| Security measures | ✅ AES-256, SOC 2 |
| Sub-processor disclosure | ✅ Listed in DPA Annex |
| Data subject rights support | ✅ API for deletion |
| Breach notification | ✅ 72-hour |
| Audit rights | ✅ Annual SOC 2 |

## 4. SCCs (Module 2) — Key Clauses
| Clause | Implementation |
|--------|----------------|
| Cl 7: Security | Groq SOC 2 Type II + AES-256 |
| Cl 8: Sub-processors | Listed in DPA; prior written notice |
| Cl 9: Data subject rights | Groq API supports deletion |
| Cl 10: Liability | Standard contractual |
| Cl 11: Termination | 30-day notice; data return/delete |
| Cl 17: Governing law | California law (per SCCs) |

## 5. Transfer Impact Assessment (TIA)
- **Risk:** US surveillance laws (FISA 702, EO 12333)
- **Mitigation:** No PII transferred; only tickers/weights/headlines
- **Conclusion:** Low risk; supplementary measures sufficient

## 6. Records
- DPA PDF: `docs/security/groq-dpa-2026.pdf`
- SCCs PDF: `docs/security/groq-sccs-2026.pdf`
- SOC 2 Report: `docs/security/groq-soc2-2026.pdf`
```

### 7.3 Update Privacy Policy
Add to **Section 3** of privacy policy:
> **Groq (LLM Provider):** Portfolio tickers, allocation weights, and news headlines are sent to Groq Inc. (USA) for AI-generated commentary. Groq is bound by a Data Processing Addendum and EU Standard Contractual Clauses (2021). No personal identifiers (name, email, IP) are shared. See [Groq Compliance Summary](/legal/groq-compliance) for details.

### 7.4 Annual Review Checklist
- [ ] DPA still valid (check expiry)
- [ ] SCCs updated (2021 version current)
- [ ] SOC 2 report < 12 months old
- [ ] Sub-processor list unchanged
- [ ] TIA re-evaluated

---

## Quick Reference: All URLs to Configure

| Setting | Value |
|---------|-------|
| `AppConfig.webBaseUrl` (Flutter) | `https://axiom.example.com` |
| Privacy Policy | `https://axiom.example.com/legal/privacy-policy/` |
| Terms of Service | `https://axiom.example.com/legal/terms-of-service/` |
| Account Deletion | `https://axiom.example.com/legal/account-deletion/` |
| Grievance Officer | `grievance@axiom.example.com` |
| Play Console Data Safety | App Content → Data Safety |
| Play Console Financial Features | App Content → Financial Features |
| Closed Testing Track | Testing → Closed Testing |
| CloudWatch Log Groups | `/axiom/frontend`, `/axiom/api` |
| S3 Log Bucket | `axiom-logs-prod-ap-south-1` |
| CERT-In Email | `incident@cert-in.org.in` |
| Groq DPA/SCCs | `docs/security/groq-compliance.md` |