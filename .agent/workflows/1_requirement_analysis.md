---
description: Comprehensive workflow for analyzing user requirements before planning.
---

# Step 1: REQUIREMENT ANALYSIS (Gereksinim Analizi)

Search and understand the user's strict needs before moving to architecture.

## 1. Scope Definition (Kapsam Belirleme)
Determine the boundaries of the request:
- **Type**: Frontend, Backend, Full-stack, Mobile, DevOps?
- **Context**: New project (Greenfield) or existing codebase (Brownfield)?
- **Scale**: MVP (Minimum Viable Product), Prototype, or Production-ready?

## 2. Critical Questions (Kritik Sorular)
Ask these if not provided:
- ❓ "Estimated user load?" (Traffic expectations for scaling)
- ❓ "Deployment target?" (Cloud, On-prem, Edge?)
- ❓ "Budget constraints?" (Free tier services vs. Enterprise)
- ❓ "Timeline?" (Speed vs. Quality trade-off)

## 3. Assumption Validation (Varsayım Doğrulama)
- Rephrase the request: "Anladığım kadarıyla [X] yapmak istiyorsunuz, doğru mu?"
- Clarify priorities: "X özelliği kritik mi yoksa 'nice-to-have' mi?"

## 4. Output Generation (Çıktı)
Produce a clear summary:
- ✅ **Problem Statement**: What are we solving?
- ✅ **Feature List**: Prioritized list of deliverables.
- ✅ **Technical Constraints**: Any specific technologies forced by the user.

## Example Trigger that requires this workflow:
> "Bana bir e-ticaret sitesi yap."
> "Login sistemi çalışmıyor, düzelt." (Requires analysis of *why* before fixing)
