# Security model for VedyaAI (auth + data)

## What we protect
- User accounts (email + password)
- Conversation history (follow-up clinical questions)
- Recommendation traces linked to a user (when logged in)

## Tools used
| Layer | Tool | Purpose |
|-------|------|---------|
| Password hashing | **bcrypt** via **passlib** | Never store plaintext passwords |
| Session / API auth | **JWT (PyJWT, HS256)** | Bearer token after login/signup |
| Transport identity | `Authorization: Bearer <token>` | Frontend sends token on API calls |
| Route guards | FastAPI `Depends(require_user)` | Conversations require login |
| Optional auth | `Depends(get_optional_user)` | Guests can still rank without account |
| Ownership checks | `assert_conversation_owner` | User A cannot read User B conversations |
| Audit | `recommendation_traces.user_id` | Links ranking runs to users when authenticated |
| CORS | Restricted origins (localhost:3000) | Browsers cannot call API from random sites (dev) |

## Data stored
- `users`: email, bcrypt `password_hash`, display_name, preferred_locale (en/hi/gu)
- `conversations` + `conversation_messages`: case continuity
- Passwords are **hashed**; JWT secret is env `JWT_SECRET`

## How login works
1. Signup/Login → server verifies/hashes password → returns JWT + user profile
2. Frontend stores token in `localStorage` (`vedya_token`)
3. `api.ts` attaches `Authorization` header automatically
4. Follow-up questions require login and reuse `conversation_id`

## Production checklist
- Rotate `JWT_SECRET` to a long random value
- Use HTTPS only
- Consider shorter JWT expiry + refresh tokens
- Add rate limiting on `/auth/login` and `/auth/signup`
- Do not commit `.env` or real secrets
- Prefer httpOnly cookies over localStorage for high-security deployments
