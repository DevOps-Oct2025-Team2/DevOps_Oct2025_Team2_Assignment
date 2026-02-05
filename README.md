# DevOps_Oct2025_Team2_Assignment
# File Portal

A Flask-based file portal with:
- Authentication & Authorization (Admin / User)
- Admin Dashboard: create/delete users
- User Dashboard: upload/download/delete own files (data isolation)
- Containerized with Docker
- CI/CD with GitHub Actions using branches: `deploy → staging → main`

---

## 1. Project Setup (Clone & Run)

### 1.1 Prerequisites

Install:
- **Git**
- **Docker Desktop** (recommended for running the app)

---

### 1.2 Clone the Repository
```bash
git clone https://github.com/DevOps-Oct2025-Team2/DevOps_Oct2025_Team2_Assignment.git
cd DevOpsFilePortal
```

---

### 1.3 Environment Variables

This project includes a `.env` file in the repository for convenience.

> **Important**: The GitHub token field is kept empty by default for security.

To demo the **"Login Failure Alert"** feature, each tester should create their own token and paste it into `.env` locally.

> **Do not commit tokens**. After testing, remove the token before pushing.

**Example `.env` (token stays empty unless testing):**
```env
FLASK_SECRET_KEY=DevOpsSecretKey
SHOW_STARTUP_BANNER=1

SQLITE_PATH=./db/data/app.db
UPLOAD_DIR=./uploads
MAX_CONTENT_LENGTH=10485760

ENABLE_GH_LOGIN_ALERTS=1
GITHUB_OWNER=DevOps-Oct2025-Team2
GITHUB_REPO=DevOps_Oct2025_Team2_Assignment
GITHUB_PAT=
LOGIN_ALERT_COOLDOWN=30
```

---

### 1.4 Create a GitHub Token (PAT)

1. Go to **GitHub** → **Settings** → **Developer settings** → **Personal access tokens**
2. Create a token with access to this repository (classic token with `repo` scope works)

---

### 1.5 Enable Alert Demo (Local Only)

1. Open `.env`
2. Paste your token:
```env
GITHUB_PAT=ghp_yourtokenhere
```

---

### 1.6 Run with Docker
```bash
docker compose up --build
```

**Open in browser:**
```
http://127.0.0.1:5000/login
```

**Stop the application:**
```bash
CTRL+C
docker compose down
```

---

### 1.7 Default Admin Account

On first run:

| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `admin123` |

---
