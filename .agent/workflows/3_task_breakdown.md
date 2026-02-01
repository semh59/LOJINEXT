---
description: Guide for breaking features into atomic tasks.
---

# Step 3: TASK BREAKDOWN (Görev Parçalama)

Break big problems into small, solveable pieces.

## Workflow
1.  **Identify Features**: List high-level features (e.g., "User Authentication").
2.  **Decompose to Atomic Tasks**: Break each feature into tasks that take ~1-4 hours.
3.  **Define Dependencies**: What needs to handle first? (DB -> API -> UI).

## Example Breakdown
**Feature: User Login**

1.  **Database Schema**
    - [ ] Create `users` table migration.
    - [ ] Add indexes on `email`.

2.  **Backend API**
    - [ ] Implement `POST /auth/login`.
    - [ ] Add JWT generation logic.
    - [ ] Add Rate Limiting middleware.

3.  **Frontend Logic**
    - [ ] Create `useAuth` hook.
    - [ ] Create `LoginForm` component.
    - [ ] Handle 401/403 errors globally.

4.  **Testing**
    - [ ] Unit tests for JWT logic.
    - [ ] E2E test for login flow.

## Criteria for Good Tasks
- **Atomic**: Can be completed in one sitting.
- **Clear**: Has a defined "Done" state.
- **Independent**: Minimizes blocking other tasks where possible.
