# AXIOM Portfolio Intelligence — Privacy Policy
Effective: 2026-09-29 | Version 1.0

## 1. Data Fiduciary
**Entity:** Parmod Kumar (Individual Developer)  
**Contact:** privacy@axiom.example.com  
**Grievance Officer:** grievance@axiom.example.com

## 2. Personal Data Collected
| Category | Data Points | Purpose | Legal Basis |
|----------|-------------|---------|-------------|
| Account | Username, email, bcrypt password hash | Authentication | Consent |
| Portfolio | Portfolio names, stock tickers, quantities, buy prices, currency | Analytics | Consent + Legitimate Interest |
| Usage | API request logs (IP, request ID, timestamps), device info | Security, debugging | Legitimate Interest |
| AI Commentary | Portfolio tickers, weights, news headlines (sent to Groq) | LLM commentary | Explicit consent |

## 3. Data Processing
- No automated decision-making affecting legal rights
- Third-party processors: AWS (hosting), Groq (LLM), NewsAPI (news)
- Cross-border transfers: Groq (US) → SCCs in place

## 4. Retention
| Data | Retention | Deletion Trigger |
|------|-----------|------------------|
| Account credentials | Until account deletion | User request |
| Portfolio data | Until account deletion | User request |
| API logs | 180 days | Auto-expiry (CERT-In) |
| AI commentary cache | 30 days | Auto-expiry |

## 5. User Rights (DPDP Act)
- **Access:** Export via Settings → Export My Data
- **Correction:** Edit profile in Settings
- **Erasure:** Settings → Delete Account (in-app) or https://axiom.example.com/account-deletion
- **Grievance:** grievance@axiom.example.com (24h ack, 30-day resolution)

## 6. Security
- bcrypt password hashing
- JWT (30min access, 30-day refresh, rotation)
- TLS 1.3 in transit, AES-256 at rest

## 7. Children
App not directed to children under 18.

## 8. Changes
Material changes notified via email + in-app banner 30 days prior.
