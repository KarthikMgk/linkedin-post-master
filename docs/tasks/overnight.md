# Overnight Run Task Queue — LinkedIn Post Master

## Context

- **Project**: LinkedIn Post Generator (React SPA + FastAPI + Claude AI + Redis)
- **Goal**: 75-task overnight run across 7 tracks
- **Execution order**: B → A → C+D → E → F → G

## Pre-Flight (do once before starting)

```bash
cd ~/Documents/linkedin-post-master
git checkout -b overnight/run-1
npm install
cd backend && pip install -r requirements.txt
```

---

## Track B: Bug Fixes (8 tasks)

- [ ] **B1** `bug-stale-todo-postresult` — PostResult.js line 21: `handleDownload` is already implemented. Remove the stale `// TODO: implement handleDownload` comment.
- [ ] **B2** `bug-stale-todo-variantcard` — VariantCard.js line 19: `extractElements` is already implemented. Remove the stale `// TODO: implement this function` comment.
- [ ] **B3** `bug-redis-silent-failure` — Quota service: if Redis is unavailable at startup, `get_remaining()` should return a safe default (unlimited quota), not raise an unhandled `RedisError`. Add graceful degradation.
- [ ] **B4** `bug-tesseract-missing` — Add Tesseract dependency check in image processing. If the binary is missing, log a clear error and return OCR failure gracefully — don't crash.
- [ ] **B5** `bug-proxy-mismatch` — Frontend `package.json` proxy is `http://localhost:8001` but `.env.example` shows a remote URL. Align so local dev works out-of-the-box.
- [ ] **B6** `bug-input-temp-files` — Input processor creates PDF/image temp files but never cleans them up. Add `tempfile` cleanup in a `finally` block after processing.
- [ ] **B7** `bug-quota-exhausted-ux` — PostGenerator: quota=0 disables the generate button but there's no in-form notice. Add a visible warning message inside the form when quota is exhausted.
- [ ] **B8** `bug-image-alt-overflow` — PostResult: long `image_alt_text` overflows its container. Add `word-wrap: break-word` / `overflow-wrap: break-word` CSS to the alt text element.

---

## Track A: Frontend Design Consistency (15 tasks)

**Goal**: One design system (Tailwind) everywhere, cohesive product feel.

### A1 | `a1-tailwind-preflight`
Enable Tailwind preflight by removing `corePlugins: { preflight: false }` from `frontend/tailwind.config.js`. Audit all components for style conflicts. Extend `theme` in `tailwind.config.js` with all current design tokens (colors, spacing, borderRadius, boxShadow, fontFamily).

### A2 | `a2-migrate-intelligence-sidebar`
`IntelligenceSidebar.js`: Replace all inline styles and mix of Tailwind/CSS variables with pure Tailwind utilities. Move personality dot colors into Tailwind config. Create a reusable `Badge` component for `ratingBadgeColor` / `statusBadgeColor` patterns. Ensure loading skeletons use `animate-pulse`.

### A3 | `a3-migrate-variant-card`
`VariantCard.js` + `VariantCard.css`: Move `PERSONALITY_COLORS` hardcoded hex values (`#FF6B6B`, `#4ECDC4`, `#9B59B6`) into Tailwind config tokens. Replace all BEM CSS classes with Tailwind utility equivalents on JSX elements. Delete `VariantCard.css` when complete.

### A4 | `a4-migrate-post-generator`
`PostGenerator.js` + `PostGenerator.css`: Replace `.generator-card`, `.input-group`, `.label-text`, `.btn-primary`, `.btn-secondary` CSS rules with Tailwind utilities on JSX elements. Delete `PostGenerator.css` when complete.

### A5 | `a5-migrate-post-result`
`PostResult.js` + `PostResult.css`: Replace `.result-card`, `.metrics-panel`, `.post-text`, `.hashtags-section`, `.suggestions-section`, `.refinement-section` CSS with Tailwind. Consolidate `getScoreColor()` / `getHookColor()` into a Tailwind color mapping object. Delete `PostResult.css` when complete.

### A6 | `a6-migrate-app-shell`
`App.js` + `App.css`: Convert header, nav, logo, footer, spinner, toast, loading-container, and login page styles to Tailwind utilities. Delete `App.css` when complete. Also migrate `PostGenerator.css` and `VariantCard.css` if not already done in A3/A4.

### A7 | `a7-login-page-refresh`
`LoginPage.js` + `LoginPage.css` (or inline Tailwind): Add subtle radial gradient background in LinkedIn blue family. Give logo SVG a subtle drop shadow. Tighten card shadow to match app shadow scale (`shadow-xl`). Add tagline: `"AI-powered content that actually gets engagement"`. Ensure mobile responsiveness — card should not feel cramped on small screens.

### A8 | `a8-surface-hierarchy`
`App.css` `.App-main`: Replace the barely-visible radial gradient with a subtle two-stop linear gradient or faint dot grid texture to give the surface some depth and visual interest.

### A9 | `a9-result-card-elevation`
`PostResult.css` `.result-card` (or Tailwind equivalent): Give the result card more visual separation — either lift with a stronger shadow (`shadow-xl`) or give it a slight off-white tint (`bg-gray-50`) against the page surface (`bg-gray-100`).

### A10 | `a10-focus-visible`
`index.css`: Add global `*:focus-visible { outline: 2px solid var(--primary); outline-offset: 2px; }`. Ensure all interactive elements (buttons, inputs, nav items) have appropriate `:focus-visible` overrides.

### A11 | `a11-section-label-typography`
`PostResult.css` + `PostGenerator.css`: Remove `text-transform: uppercase` from primary section headings (e.g., "Post Text" not "POST TEXT"). Keep it only for dense metadata labels (metrics, hashtag count annotation).

### A12 | `a12-engagement-metrics-bar`
`PostResult.css` `.metric-value`: Add a small progress-fill bar behind or beside the engagement score number, mirroring the `DimensionRow` fill-bar pattern already in `IntelligenceSidebar`.

### A13 | `a13-suggestion-bullet`
`PostResult.css` line 223: Replace the `💡` emoji bullet with a small inline SVG icon or a styled `::before` pseudo-element using a geometric shape.

### A14 | `a14-hashtag-hover`
`PostResult.css` `.hashtag`: Add hover state — `background: var(--primary-dark)` or `transform: scale(1.02)` to communicate interactivity.

### A15 | `a15-undo-banner-hint`
`PostResult.css` `.blend-undo-banner`: Add `⌘Z` shortcut hint in the banner text: `"Element blended. ↩ Undo (⌘Z)"`.

---

## Track C: Backend Features (12 tasks)

### C1 | `c1-url-extraction`
`backend/services/input_processor.py`: Replace the `"URL provided: {url} (URL extraction coming in Phase 2)"` placeholder with actual URL content extraction using `httpx` with SSRF protection (block private IP ranges, 10s timeout, redirect-following limits).

### C2 | `c2-dev-login-production`
`backend/main.py`: `POST /api/auth/dev-login` must be a no-op or `404` when `DEBUG=False` in production. Add an explicit guard.

### C3 | `c3-logout-blacklist`
Add `POST /api/auth/logout` endpoint that adds the user's JWT to a Redis blacklist with TTL equal to remaining token lifetime. Update `require_auth` middleware to check the blacklist before allowing access.

### C4 | `c4-quota-check-endpoint`
Add `GET /api/quota` endpoint returning `{ "remaining": N, "limit": 10, "resets_at": "YYYY-MM-DD"T00:00:00Z" }`. Frontend can poll this without triggering generation.

### C5 | `c5-rate-limit-headers`
All quota-gated endpoints should return `X-RateLimit-Remaining: N` and `X-RateLimit-Reset: <unix_ts>` response headers.

### C6 | `c6-pdf-error-handling`
`backend/services/input_processor.py` PDF path: If PDF is password-protected or corrupt, return a structured `400` with `{ "error": "PDF_ERROR", "detail": "File is password-protected or corrupted" }`. Not a generic 500.

### C7 | `c7-image-fallback`
`backend/services/image_service.py`: If `fal` provider fails, auto-fallback to `huggingface`. If both fail, return `null` image with `image_suggestion` text. Ensure this chain actually works end-to-end.

### C8 | `c8-input-size-limits`
Add enforcement in `input_processor.py` / route handlers: max PDF size (10MB), max image count (5), max text length (50K chars). Return `413 Payload Too Large` or `400 Bad Request` with a specific message per violation.

### C9 | `c9-concurrent-generation-lock`
Prevent same user from triggering multiple simultaneous generations. Use a Redis `SETNX` lock with key `generating:{user_id}` and 60s TTL. Return `409 Conflict` if lock is already held.

### C10 | `c10-api-compression`
Enable gzip compression on FastAPI responses via `GZipMiddleware` from `fastapi.middleware.gzip`. Verify large JSON responses are compressed.

### C11 | `c11-cors-allowlist`
`backend/main.py`: Validate `FRONTEND_URL` strictly — CORS should only allow the configured frontend origin, not `*`. Raise an error on startup if `FRONTEND_URL` is `*` or empty in production mode.

### C12 | `c12-health-check-enhancement`
`GET /api/health`: Extend to check Redis connectivity and Claude API reachability. Return `{ "status": "ok", "components": { "api": "ok", "redis": "ok", "claude": "ok" } }`.

---

## Track D: Missing Feature Implementation (10 tasks)

### D1 | `d1-history-page`
Nav "History" button is non-functional. Implement localStorage-based history: store each generated post with timestamp, variant selected, and metadata. Render as a scrollable list under `/history` route.

### D2 | `d2-templates-page`
Nav "Templates" button is non-functional. Implement saved templates: user can save a prompt template (text + options) and reload it. Persist in localStorage.

### D3 | `d3-variant-per-image`
PostResult currently shows one image for the selected variant. Each variant card displays its own `variant.image.url`. Ensure the image preview and the image section below reflect the currently selected variant's image (not a fixed variant's image).

### D4 | `d4-variant-level-refine`
Refinement currently operates on a flat post string. Refine should operate on the `selectedVariant` specifically, updating only that variant's data in state.

### D5 | `d5-pdf-multi-page`
`input_processor.py`: PDF text extraction should iterate over all pages (`pdf_reader.pages`) and concatenate with `\n\n` between pages.

### D6 | `d6-hashtag-analytics-stub`
Add a basic analytics stub: when a post is copied, record the hashtag set and variant used in localStorage. Show a "top hashtags" summary on the history page.

### D7 | `d7-char-limit-inline-warning`
PostResult: Add inline amber warning at 2500+ characters (not just red at 3000). The character counter should use amber coloring from 2500 to 2999, red at 3000+.

### D8 | `d8-share-to-linkedin`
Add "Share" button that opens `https://www.linkedin.com/sharing/shareOffsite/?url=<encoded>` in a new tab with post text copied to clipboard and a prompt to paste in LinkedIn.

### D9 | `d9-dark-mode`
Add `prefers-color-scheme` detection and a manual toggle. Introduce a `dark` color mode via CSS variables swapped on `[data-theme="dark"]` on `<html>`. Define `--bg-surface`, `--text-primary`, `--text-secondary`, `--bg-card` for each mode.

### D10 | `d10-quota-email-notification`
Backend: At 80% quota usage, send a warning email via SMTP (or log if SMTP not configured). At 0%, send exhaustion email. Requires SMTP env vars (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`, `FROM_EMAIL`).

---

## Track E: Test Coverage Gaps (10 tasks)

### E1 | `e1-auth-e2e-tests`
`backend/tests/test_auth_flow.py`: Write integration tests covering full Google OAuth → JWT → API call flow. Mock Google token verification.

### E2 | `e2-input-processor-tests`
`backend/tests/test_input_processor.py`: Tests for PDF extraction (single-page, multi-page, password-protected, corrupt), image OCR, URL extraction, text truncation at 50K chars.

### E3 | `e3-sanitizer-tests`
`backend/tests/test_sanitizer.py`: Test `sanitizer.py` with injection attempts (prompt-leaking attempts, XSS payloads, oversized inputs).

### E4 | `e4-jwt-edge-cases`
`backend/tests/test_jwt_handler.py`: Test expired tokens, malformed tokens, tokens with wrong algorithm, tokens missing required fields.

### E5 | `e5-google-auth-failures`
`backend/tests/test_google_auth.py`: Test invalid tokens, revoked tokens, expired tokens, audience mismatch. Verify appropriate error responses.

### E6 | `e6-rate-limit-enforcement`
`backend/tests/test_rate_limits.py`: Send burst requests to quota-gated endpoints and verify `429` response. Verify the quota endpoint itself is also rate-limited.

### E7 | `e7-redis-failure-modes`
`backend/tests/test_quota_redis_failure.py`: Test what happens when Redis is unavailable mid-request — quota should degrade gracefully (allow request, don't block).

### E8 | `e8-image-fallback-tests`
`backend/tests/test_image_service.py`: Test fal.ai failure → huggingface fallback chain. Test both providers failing → null image with `image_suggestion` text.

### E9 | `e9-frontend-interceptor-tests`
`frontend/src/services/__tests__/quotaInterceptor.test.js`: Test that the quota interceptor fires on `429`, auth header is attached to requests, and quota display updates correctly.

### E10 | `e10-variant-blend-undo-tests`
`frontend/src/components/__tests__/PostResult.test.js`: Test blend undo via `handleUndo`, `preBlendState` restoration, and Ctrl+Z keyboard shortcut handling.

---

## Track F: Documentation + DevOps (5 tasks)

### F1 | `f1-readme-completion`
README: Phase 2/3/4 sections are "upcoming" — fill in actual roadmap with specific features or mark as `## Roadmap (see GitHub Issues)`. Add local dev setup instructions ( Prerequisites, `.env` setup, how to run frontend + backend).

### F2 | `f2-contributing-guide`
Create `CONTRIBUTING.md`: branch conventions (`feature/`, `bugfix/`, `hotfix/`), commit message format (Conventional Commits), how to run tests (`pytest`, `npm test`), PR checklist.

### F3 | `f3-docker-compose`
Create `docker-compose.yml` with services: `redis` (with password), `backend` (FastAPI on 8001), `frontend` (React dev server on 3000). Add `Dockerfile` for backend. Add a `Makefile` with `make up`, `make down`, `make test`.

### F4 | `f4-github-actions`
Create `.github/workflows/ci.yml`: run `pytest` (backend) + `npm test` (frontend) + lint + `pip-audit` + `npm audit` on every PR. Fail CI if critical CVEs are found or any test suite fails.

### F5 | `f5-build-verification`
Add `scripts/verify-build.sh`: runs `cd frontend && npm run build`, checks that bundle size is under 2MB, no large unexpected assets, and the built `index.html` loads without console errors.

---

## Track G: Comprehensive Security Review (15 tasks)

**Run this track LAST — after all other tracks are complete. Review the final state of the application.**

### G1 | `g1-dependency-cve-audit`
Run `pip-audit` and `npm audit`. For each CVE found: patch, suppress with justification, or document as accepted risk. Fail CI (G4) if critical/high CVEs are unpatched.

### G2 | `g2-jwt-security`
Audit `auth/jwt_handler.py`: verify JWT secret is read from a strong env var, alg is `HS256` (not `none`), exp is enforced on every protected route, token refresh rotation is implemented.

### G3 | `g3-google-oauth-validation`
Audit `auth/google_auth.py`: verify Google token `aud` matches `GOOGLE_CLIENT_ID`, token expiry is checked, no user PII is reflected in logs.

### G4 | `g4-file-type-validation`
Add magic-byte / content-type validation for PDF and image uploads — not just file extension. Reject files with a mismatched declared type (e.g., a `.pdf` that is actually an image).

### G5 | `g5-upload-size-enforcement`
Verify backend enforces max PDF (10MB), max image count (5), max text (50K chars). Test with oversized payloads to confirm `413`/`400` responses are returned.

### G6 | `g6-ssrf-prevention`
With URL extraction implemented (C1): verify it blocks private IP ranges (`10.x`, `172.16.x`, `192.168.x`, `127.0.0.1`), has a 10s timeout, and follows redirects only up to 3 hops.

### G7 | `g7-prompt-injection`
Audit prompt injection vectors: user text input is fed to Claude. Verify sanitization catches injection attempts (e.g., "ignore previous instructions", "system prompt leak"). Add a test suite for prompt injection attempt strings.

### G8 | `g8-secrets-exposure`
Scan the codebase for hardcoded secrets, API keys, or JWT secrets — none should exist outside `.env` files. Verify `.env.example` contains only placeholder names, no real values.

### G9 | `g9-log-sanitization`
Verify no PII (email, name, picture URLs, post content, API keys) is written to logs. Check `utils/logger.py` for redaction. Add a log sampling test that asserts no PII fields appear in log output.

### G10 | `g10-cors-headers`
Verify CORS only allows the configured `FRONTEND_URL` origin, not `*`. Add missing HTTP security headers: `X-Frame-Options: DENY`, `Content-Security-Policy`, `X-Content-Type-Options: nosniff`.

### G11 | `g11-rate-limit-bypass`
Verify `slowapi` rate limits are enforced: send burst requests and confirm `429` responses. Verify the quota check endpoint is also rate-limited.

### G12 | `g12-token-blacklist-verify`
With the logout/blacklist endpoint from C3 implemented, verify: (a) blacklisted tokens are rejected immediately, (b) Redis blacklist key TTL matches remaining token lifetime, (c) logout works end-to-end from frontend.

### G13 | `g13-redis-authentication`
Redis is currently unauthenticated. Verify `REDIS_URL` defaults to `localhost`. If production Redis is exposed externally, add `REDIS_PASSWORD` to `.env` and update `quota_service.py` to authenticate.

### G14 | `g14-api-error-leakage`
Send malformed requests to every endpoint. Verify 4xx/5xx responses do not leak stack traces, internal file paths, or third-party API keys. Add `test_error_information_leakage.py` covering all major endpoints.

### G15 | `g15-security-headers-middleware`
Add FastAPI middleware that injects on all responses: `Strict-Transport-Security: max-age=31536000; includeSubDomains`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`.

---

## Task File Format

```markdown
# Overnight Run Task Queue — LinkedIn Post Master
# Format: [ ] TaskID - Description

# Track B: Bug Fixes
[ ] B1 - bug-stale-todo-postresult
...

# Track A: Frontend Design
[ ] A1 - a1-tailwind-preflight
...

# Track C: Backend Features
[ ] C1 - c1-url-extraction
...

# Track D: Missing Features
[ ] D1 - d1-history-page
...

# Track E: Test Coverage
[ ] E1 - e1-auth-e2e-tests
...

# Track F: Docs + DevOps
[ ] F1 - f1-readme-completion
...

# Track G: Security Review
[ ] G1 - g1-dependency-cve-audit
...
```

---

## Summary

| Track | Tasks |
|---|---|
| B: Bug Fixes | 8 |
| A: Frontend Design | 15 |
| C: Backend Features | 12 |
| D: Missing Features | 10 |
| E: Test Coverage | 10 |
| F: Docs + DevOps | 5 |
| G: Security Review | 15 |
| **Total** | **75** |

**Execution**: B → A → C+D → E → F → G
**Blacklisting**: Redis-backed JWT blacklist on logout (C3 + G12)
**Design system**: Tailwind app-wide (A1–A6), CSS custom properties deprecated
**Security**: Full review at end (G1–G15)