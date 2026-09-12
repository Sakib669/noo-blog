# NooBlog Frontend

Modern Next.js 16 + React 19 frontend for NooBlog with Tailwind CSS v4, shadcn/ui, and Google Gemini AI summarization integration.

---

## Features

- **Authentication**: JWT login, registration, and persistent sessions via `AuthContext`.
- **Blog Feed**: Latest articles, keyword search, tag filtering, responsive cards.
- **Article Reader**: Full reader view with author info, read stats, formatted content.
- **Gemini AI Summary**: Highlighted AI summary box with instant generate/regenerate capability for post authors.
- **Comments**: Full interactive comment threads with author details and deletion for owners.
- **Post Lifecycle**: Write new posts (`/posts/new`) and edit existing posts (`/posts/[slug]/edit`).
- **User Profile**: Profile settings, bio, avatar, and password change (`/profile`).

---

## Getting Started

### 1. Install Dependencies
```bash
pnpm install
```

### 2. Environment Variables
Create `.env.local` if custom backend URL is required (defaults to `http://127.0.0.1:8000/api/v1`):
```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api/v1
```

### 3. Run Development Server
```bash
pnpm dev
```
Open [http://localhost:3000](http://localhost:3000) to view the application.

### 4. Production Build
```bash
pnpm build
pnpm start
```
