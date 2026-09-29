# AXIOM Portfolio Intelligence — India Compliance & Policy Guide

This document maps the app's current security posture to Indian regulatory requirements for a public Play Store release targeting Indian users.

---

## 1. Financial Regulatory Classification (India)

| Regulation | Status | Notes |
|------------|--------|-------|
| **SEBI (Investment Advisers) Regulations, 2013** | **Not Applicable** | App provides **quantitative research & risk analytics**, not personalized investment advice. No "buy/sell/hold" recommendations for specific users. |
| **SEBI (Research Analysts) Regulations, 2014** | **Not Applicable** | Output is algorithmic portfolio optimization + sentiment analysis, not a "research report" distributed to clients. |
| **SEBI (Portfolio Managers) Regulations, 2020** | **Not Applicable** | No discretionary portfolio management, no custody, no trade execution. |
| **RBI Guidelines on Digital Lending / Fintech** | **Not Applicable** | No lending, no payments, no KYC/AML obligations. |
| **Companies Act, 2013 / IT Act, 2000** | **Applicable** | Standard corporate compliance for the operating entity. |

**Play Store Financial Features Declaration** → Select:
- ✅ **"Stock trading and portfolio management"** (portfolio tracking/analytics only)
- ❌ **"Financial advice"** (app does not provide personalized advice)

**App Store Description Must State:**
> "AXIOM Portfolio Intelligence is a portfolio research application combining quantitative allocation analysis, risk analytics, financial-news sentiment and evidence-grounded AI commentary. It is designed for educational and research use and does not execute trades, provide brokerage services, or offer personalized financial advice."

---

## 2. Data Protection & Privacy (India)

| Law | Requirement | AXIOM Implementation |
|-----|-------------|---------------------|
| **DPDP Act, 2023** (Digital Personal Data Protection) | Lawful basis, consent, purpose limitation, data minimization, retention limits, user rights (access, correction, erasure) | ✅ Explicit consent at registration; ✅ Purpose: portfolio analytics only; ✅ Minimal data (username, email, portfolio holdings); ✅ Account deletion API (`DELETE /api/v1/auth/account`) + web deletion path; ✅ No third-party data sharing except LLM providers (Groq) — disclosed in privacy policy |
| **IT Act, 2000 / SPDI Rules, 2011** | Sensitive personal data (financial info) protection | ✅ Portfolio holdings classified as financial data; ✅ Encrypted at rest (bcrypt for passwords, AES for tokens); ✅ TLS 1.3 in transit; ✅ No sensitive data in logs |
| **CERT-In Directions (2022)** | 180-day log retention, incident reporting within 6 hours | ✅ Structured audit logs with request IDs; ⚠️ **Action needed**: Configure 180-day retention in CloudWatch/ELK; ⚠️ **Action needed**: Incident response runbook |

**Privacy Policy Must Include (DPDP Act):**
- Data fiduciary identity & contact
- Categories of personal data collected (username, email, portfolio holdings, device info)
- Purpose of processing (analytics, auth, notifications)
- Legal basis (consent + legitimate interest)
- Data retention periods
- User rights: access, correction, erasure, grievance redressal
- Data processor disclosures (AWS, Groq, NewsAPI)
- Cross-border transfer safeguards (Standard Contractual Clauses)

---

## 3. Google Play Store Requirements (India)

| Requirement | Status | Evidence |
|-------------|--------|----------|
| **Target API Level 36 (Android 16)** | ✅ | `compileSdk = 36`, `targetSdk = 36` |
| **App Bundle (.aab)** | ✅ | `flutter build appbundle --release` |
| **Play App Signing** | ✅ | Enabled in Play Console |
| **Privacy Policy URL** | ⚠️ **Required** | Host at `https://axiom.example.com/privacy` |
| **Data Safety Form** | ⚠️ **Required** | Complete in Play Console → App Content |
| **Financial Features Declaration** | ⚠️ **Required** | "Stock trading and portfolio management" |
| **Account Deletion** | ✅ | In-app (`/settings/delete-account`) + web (`/account-deletion`) |
| **Target Audience** | ⚠️ **Required** | Adults (18+) |
| **Content Rating** | ⚠️ **Required** | IARC questionnaire (Finance → Low maturity) |
| **Testers (12 for 14 days)** | ⚠️ **Required** | Internal → Closed testing track |

**India-Specific Play Console Settings:**
- **Pricing**: Free (or INR pricing if monetized)
- **Distribution**: India + other countries
- **Tax**: GST registration if paid app/IAP

---

## 4. LLM / AI Provider Compliance

| Provider | Data Sent | DPDP Compliance |
|----------|-----------|-----------------|
| **Groq (Llama 3)** | Portfolio tickers, weights, news headlines | ⚠️ **Action**: Verify Groq DPA + SCCs; document in privacy policy |
| **NewsAPI** | Ticker symbols for news fetch | ✅ No PII sent |
| **yfinance** | Public market data | ✅ Public data |

**Risk Mitigation:**
- No PII (names, emails, phone) sent to LLMs
- Only portfolio composition + public news headlines
- User consent obtained at registration for "AI commentary"

---

## 5. Security Checklist for India Release

### Pre-Launch (Must Complete)
- [ ] Host privacy policy at `https://yourdomain.com/privacy`
- [ ] Host terms of service at `https://yourdomain.com/terms`
- [ ] Host account deletion page at `https://yourdomain.com/account-deletion`
- [ ] Complete Play Console Data Safety form (accurate mapping)
- [ ] Complete Financial Features declaration
- [ ] Configure 180-day log retention (CloudWatch → S3 Glacier)
- [ ] Create CERT-In incident response runbook (6-hour reporting)
- [ ] Verify Groq DPA + SCCs for cross-border transfer
- [ ] Penetration test (OWASP MASVS Level 2)
- [ ] MobSF scan of release AAB
- [ ] 12 testers × 14 days on Closed Testing track

### Post-Launch (Ongoing)
- [ ] Monthly dependency scans (Trivy/GitHub Dependabot)
- [ ] Quarterly secret rotation (JWT keys, API keys)
- [ ] Annual DPDP compliance audit
- [ ] User grievance redressal mechanism (email + in-app)

---

## 6. Recommended India-Specific App Config

```yaml
# android/app/src/main/res/values/strings.xml
<string name="app_name">AXIOM Portfolio Intelligence</string>
<string name="privacy_policy_url">https://axiom.example.com/privacy</string>
<string name="terms_url">https://axiom.example.com/terms</string>
<string name="account_deletion_url">https://axiom.example.com/account-deletion</string>
<string name="grievance_officer_email">grievance@axiom.example.com</string>

# android/app/src/main/AndroidManifest.xml
<application
    android:networkSecurityConfig="@xml/network_security_config"
    ...>
```

```xml
<!-- android/app/src/main/res/xml/network_security_config.xml -->
<network-security-config>
    <domain-config cleartextTrafficPermitted="false">
        <domain includeSubdomains="true">api.axiom.example.com</domain>
        <domain includeSubdomains="true">axiom.example.com</domain>
    </domain-config>
    <certificates>
        <certificates src="system"/>
        <certificates src="user"/>
    </certificates>
</network-security-config>
```

---

## 7. Grievance Redressal (DPDP Act Section 13)

| Requirement | Implementation |
|-------------|----------------|
| **Grievance Officer** | Designated email: `grievance@axiom.example.com` |
| **Response Timeline** | Acknowledge within 24h, resolve within 30 days |
| **Escalation** | Appellate Tribunal (if unresolved) |
| **In-App Access** | Settings → Help & Support → Contact Grievance Officer |

---

## 8. Summary: Go/No-Go for India Play Store

| Area | Ready? | Blockers |
|------|--------|----------|
| **Backend Security** | ✅ | — |
| **Mobile App Build** | ✅ | — |
| **Privacy Policy (DPDP)** | ⚠️ | Host public URLs |
| **Data Safety Form** | ⚠️ | Complete in Play Console |
| **Financial Declaration** | ⚠️ | Select correct category |
| **Account Deletion** | ✅ | In-app + web |
| **CERT-In Logging** | ⚠️ | Configure 180-day retention |
| **LLM Data Processing** | ⚠️ | Document Groq DPA/SCCs |
| **Closed Testing (12/14)** | ⚠️ | Recruit testers |

**Estimated Time to Launch-Ready**: 2-3 weeks (policy hosting + Play Console config + closed testing)

---

## 9. Legal Disclaimer

> This guide is for engineering reference only and does not constitute legal advice. Engage qualified counsel (Indian fintech/privacy lawyer) before Play Store submission. Regulations evolve — verify current SEBI/RBI/DPDP/CERT-In requirements at time of launch.