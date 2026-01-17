# Data Privacy Policy

## 1. Overview

The Crime Detector System is committed to protecting personal data and ensuring compliance with international data protection regulations including GDPR, CCPA, and relevant law enforcement data handling standards.

## 2. Data Classification

### Personal Data Categories
- **Identification Data**: Names, addresses, identification numbers
- **Behavioral Data**: Criminal history, investigation records, suspect information
- **Contact Data**: Phone numbers, email addresses, communication records
- **Metadata**: Timestamps, user actions, system interactions

### Sensitive Data Categories
- Biometric Data (fingerprints, facial recognition)
- Medical/Health Information
- Financial Records
- Immigration Status
- Religious/Political Affiliations

## 3. Data Collection Principles

### Lawful Basis
- **Law Enforcement**: Data collection authorized by law enforcement agencies
- **Legitimate Interest**: Investigation and crime prevention
- **Consent**: Explicit consent for biometric and sensitive data processing
- **Legal Obligation**: Compliance with applicable statutes

### Minimal Data Collection
- Collect only data necessary for investigation purposes
- Implement data minimization practices
- Regular review and purging of unnecessary data
- Retention limits based on investigation status and legal requirements

## 4. No Real-Time Tracking

### Restrictions
- ❌ No continuous GPS or location tracking of individuals
- ❌ No real-time surveillance without judicial authorization
- ❌ No monitoring of communications without warrant
- ❌ No behavioral profiling without explicit approval

### Permitted Activities
- ✅ Analysis of past investigation records
- ✅ Pattern detection from historical data
- ✅ Geolocation data analysis from crime scenes (with authorization)
- ✅ Timeline reconstruction for investigative purposes

## 5. Biometric Data Protection

### Storage Requirements
- **No storage without explicit consent** from data subject or judicial order
- Encrypted storage using AES-256 or equivalent
- Separate storage from non-biometric data
- Limited access to authorized personnel only

### Biometric Use Cases
- Facial recognition for suspect matching (with warrant)
- Fingerprint analysis for crime scene investigations
- Voice identification for secure authentication only

### Data Retention
- Delete biometric data upon investigation closure
- Maximum retention: 7 years for closed cases
- Annual review for retention necessity
- Immediate deletion upon data subject request (where legally permitted)

### Purpose Limitation
- Use biometric data **only for** investigative purposes
- Prohibition on:
  - Commercial use
  - Third-party sharing (except law enforcement partners with agreement)
  - Secondary purposes without authorization

## 6. Role-Based Access Control (RBAC)

### Role Hierarchy

**1. System Administrator**
- Full system access
- User management
- Configuration
- Audit log access
- No investigative data access

**2. Investigation Lead**
- Create and manage investigations
- Assign cases to team members
- Access all linked investigation data
- Approve biometric data usage
- Limited audit log access

**3. Investigator**
- View assigned investigations
- Add evidence and findings
- Create entity matches
- Access investigation summaries
- No biometric data access without approval

**4. Analyst**
- Read-only access to assigned cases
- Generate reports
- View entity relationships
- No data modification
- No biometric data access

**5. Auditor**
- Full audit log access
- Compliance report generation
- No investigative data access
- Read-only access to metadata

### Access Control Implementation
```
- Authentication via OAuth 2.0 + MFA
- Token-based authorization (JWT)
- Session timeouts: 30 minutes inactive
- IP whitelisting for sensitive operations
- Regular access reviews (quarterly)
```

## 7. Encryption Standards

### Data at Rest
- **Algorithm**: AES-256
- **Key Management**: Hardware Security Module (HSM) or AWS KMS
- **Database Encryption**: Native encryption (PostgreSQL pgcrypto)
- **Field-Level Encryption**: Sensitive PII fields

### Data in Transit
- **Protocol**: TLS 1.3
- **Certificate Management**: Auto-renewal with monitoring
- **API Security**: HTTPS only, no HTTP allowed
- **Internal Communication**: Encrypted inter-service communication

## 8. Full Audit Logging

### Audit Log Requirements

**Logged Events**
- User login/logout with timestamp and IP
- Data access (read, write, delete, export)
- Privilege escalation
- Configuration changes
- Failed access attempts
- Biometric data access
- Report generation
- API calls (non-sensitive endpoints)

**Audit Log Contents**
```json
{
  "timestamp": "2026-01-17T10:30:45Z",
  "user_id": "INV_12345",
  "action": "DATA_ACCESS",
  "resource": "investigation_id_xyz",
  "result": "SUCCESS|FAILURE",
  "ip_address": "192.168.1.100",
  "changes": {
    "field": "old_value → new_value"
  },
  "reason": "Investigation follow-up",
  "classification": "SENSITIVE"
}
```

### Audit Log Storage
- **Immutable storage**: Write-once logs
- **Encryption**: AES-256 at rest, TLS in transit
- **Retention**: Minimum 7 years
- **Access**: Restricted to auditors and compliance officers
- **Redundancy**: Replicated across geographic regions

### Audit Log Monitoring
- Real-time alerts for suspicious activities
- Automated reports (weekly, monthly)
- External audit reviews (quarterly)
- Tamper detection systems

## 9. Data Subject Rights

### Right to Access
- Subjects can request their personal data
- Response within 30 days
- Free of charge
- In machine-readable format

### Right to Erasure
- Delete data when no longer necessary
- Exception: Legal hold or ongoing investigation
- Verified request required
- Documented deletion with audit trail

### Right to Rectification
- Correct inaccurate data
- Update outdated information
- Documented changes with audit trail

### Right to Restrict Processing
- Suspend data processing temporarily
- Documented with reason
- Resumption authorization required

## 10. Data Sharing Restrictions

### Internal Sharing
- Only with authorized personnel (RBAC)
- Documented access with business justification
- Audit logged

### External Sharing
- **Law Enforcement Partners**: With data sharing agreements (DSA)
- **Government Agencies**: With legal authorization
- **Third Parties**: Prohibited without explicit judicial order

### Data Sharing Agreement Components
- Purpose and scope
- Data protection obligations
- Retention periods
- Sub-processing restrictions
- Audit rights
- Termination clauses

## 11. Data Retention Schedule

| Data Type | Retention Period | Condition |
|-----------|------------------|-----------|
| Active Investigations | Duration + 3 years | Case closure + review |
| Closed Cases | 7 years | Statute of limitations |
| Biometric Data | Case closure | Immediate review for deletion |
| Audit Logs | 7 years | Immutable storage |
| User Access Logs | 1 year | Regular purge |
| System Logs | 90 days | Archived quarterly |

## 12. Breach Response Protocol

### Detection & Assessment (24 hours)
1. Identify breach scope and affected data
2. Assess risk level and impact
3. Document initial findings

### Notification (72 hours)
- Notify supervisory authority
- Notify affected individuals (if required)
- Document notification

### Remediation (7 days)
- Contain breach
- Identify root cause
- Implement corrective measures
- Communicate resolution

### Documentation
- Incident report
- Breach register entry
- Corrective action plan
- Audit trail preservation

## 13. Training & Compliance

### User Training
- Annual data privacy training (mandatory)
- Role-specific training for investigators
- Biometric data handling certification
- Audit trail interpretation

### Compliance Monitoring
- Monthly audit log reviews
- Quarterly access reviews
- Annual compliance assessment
- External audits (annually)

### Policy Review
- Annual policy updates
- Regulatory change monitoring
- Incident-driven policy updates
- Stakeholder feedback incorporation

## 14. Contact & Escalation

**Data Protection Officer (DPO)**
- Email: dpo@crimedetector.local
- Phone: +1-XXX-XXX-XXXX
- Office: Compliance Department

**Privacy Complaints**
- Submit to: privacy@crimedetector.local
- Response SLA: 14 days

**Regulatory Inquiries**
- Direct to: legal@crimedetector.local

---

**Last Updated**: January 17, 2026  
**Next Review**: January 17, 2027  
**Classification**: INTERNAL - CONFIDENTIAL