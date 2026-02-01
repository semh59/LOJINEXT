---
description: Guide for technology selection and architecture design.
---

# Step 2: SOLUTION ARCHITECTURE (Çözüm Mimarisi)

Design the system before building it. Consider trade-offs.

## 1. Technology Stack Selection (Teknoloji Yığını)
Select the right tool for the job.

### Frontend
- **Framework**: React (standard), Vue (simple), Svelte (performance) or Next.js (SSR/SEO).
- **State Management**: React Context (simple), Zustand (medium), Redux (complex).
- **Styling**: Tailwind CSS (utility-first), CSS Modules (scoped), Styled Components (CSS-in-JS).

### Backend
- **Runtime**: Node.js (JS fullstack), Python (AI/Data), Go (Concurrency).
- **Database**:
    - *Relational*: PostgreSQL (Default choice, ACID).
    - *NoSQL*: MongoDB (Flexible schema), Redis (Caching/Queues).
- **Auth**: JWT (Stateless), Session (Stateful), OAuth (Social).

## 2. Architectural Decisions (Mimari Kararlar)
- **Monolith vs Microservices**: Start with Monolith unless scaling issues are guaranteed.
- **REST vs GraphQL**: REST for simple resources, GraphQL for complex relational data.
- **SSR vs CSR**: SSR for SEO/Performance, CSR for Rich Apps.

## 3. Third-Party Services (3. Parti Servisler)
Think about "Buy vs Build".
- **Payments**: Stripe / Iyzico.
- **Email**: Resend / SendGrid / AWS SES.
- **Storage**: AWS S3 / Cloudinary.
- **Analytics**: PostHog / Plausible / GA4.

## 4. Output Format
Present the architecture clearly:
```markdown
## Önerilen Teknoloji Yığını

**Frontend:**
- React 18 + Vite
- Zustand
- Tailwind

**Backend:**
- Node.js + Express
- PostgreSQL + Prisma

**Maliyet Tahmini:** ~$X/ay
```
