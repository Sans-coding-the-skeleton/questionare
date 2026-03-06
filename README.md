# Questionnaire App

A simple single-question polling web application built with **Python + Flask**, deployed on [PythonAnywhere](https://www.pythonanywhere.com/).

---

## Question

> **How many browser tabs open is still reasonable?**
>
> a) 1 – 5 (minimalist)  
> b) 6 – 15 (normal)  
> c) 16 – 30 (power user)  
> d) 30+ (send help)

---

## Features

| # | Feature | Description |
|---|---------|-------------|
| F1 | **Voting** | Choose one answer and submit. Result is saved server-side immediately. |
| F2 | **Results** | View live vote counts and percentages without voting. |
| F3 | **Reset** | Admin can reset all votes by supplying a secret token. |
| – | **Anti-double-vote** | Server-side Flask session prevents the same browser from voting twice. |

---

## File Structure

```
questionare/
├── app.py            # Flask routes and application logic
├── config.py         # Question, answers, reset token, secret key
├── votes.json        # Persistent vote storage (auto-created on first run)
├── requirements.txt  # Python dependencies
├── templates/
│   ├── index.html    # Voting page
│   ├── results.html  # Results + reset page
│   └── about.html   # O anketě – About page
├── static/
│   └── style.css     # Dark-theme styling
├── Wireframe.drawio  # UI wireframe
├── Flowchart.drawio  # User-flow diagram
└── README.md         # This file
```

---

## Endpoints / URLs

| Method | URL | Description |
|--------|-----|-------------|
| `GET`  | `/` | Voting page. Redirects to `/results` if user already voted. |
| `POST` | `/vote` | Submit a vote. Validates choice, saves to file, sets session flag. |
| `GET`  | `/results` | Results page with vote counts and reset form. |
| `POST` | `/reset` | Reset votes if the supplied token matches the server-side token. |
| `GET`  | `/about` | About page (O anketě) – info about the survey and bug reporting link. |

---

## Configuration

Edit `config.py` or set environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RESET_TOKEN` | `secret123` | Token required for resetting votes |
| `SECRET_KEY` | `changeme-...` | Flask session signing key |

> **On PythonAnywhere**: Go to *Web → Environment variables* and set `RESET_TOKEN` and `SECRET_KEY` to strong, random values.

---

## Running Locally

```bash
pip install flask
python app.py
# Open http://127.0.0.1:5000
```

---

## Deploying on PythonAnywhere

1. Upload all files to your PythonAnywhere home directory (e.g. `/home/<username>/questionare/`).
2. In the **Web** tab, create a new web app → choose **Flask** (Python 3.x).
3. Set the **Source code** path to `/home/<username>/questionare/`.
4. Set the **WSGI file** to point to `app` in `app.py`:
   ```python
   import sys
   sys.path.insert(0, '/home/<username>/questionare')
   from app import app as application
   ```
5. Set environment variables `RESET_TOKEN` and `SECRET_KEY` in the **Web** tab.
6. Reload the web app.

---

## Deploying Code Changes

After the first deployment, follow these steps every time you make a change to the code.

### Step 1 – Make and test changes locally

```bash
python app.py
# Open http://127.0.0.1:5000 and verify the change works correctly
```

### Step 2 – Stage the changed files

```bash
git add <file>          # add a specific file, e.g. git add templates/about.html
# OR
git add .               # add all changed files at once
```

### Step 3 – Create a commit with a short description

```bash
git commit -m "Short description of what changed"
# Example: git commit -m "Add O ankete About page and report-bug link"
```

> Use present-tense imperative messages: *Add …*, *Fix …*, *Update …*

### Step 4 – Push to GitHub

```bash
git push origin main
```

> If your default branch is called `master`, use `git push origin master`.

### Step 5 – Pull changes on PythonAnywhere

1. In the PythonAnywhere dashboard, open a **Bash console**.
2. Navigate to the project directory:
   ```bash
   cd ~/questionare
   ```
3. Pull the latest changes from GitHub:
   ```bash
   git pull origin main
   ```
4. If you added new Python packages, install them:
   ```bash
   pip install -r requirements.txt
   ```

### Step 6 – Reload the web app

1. Go to the **Web** tab in the PythonAnywhere dashboard.
2. Click the green **Reload** button.
3. Open your live URL and confirm the change is visible.

---

### Quick reference – full flow

```
Edit code  →  python app.py (test locally)  →  git add .  →
git commit -m "…"  →  git push  →  PythonAnywhere: git pull  →  Reload
```

---

## Anti-double-vote Design

Votes are stored in a **server-side signed session cookie** (Flask default). When a user submits a vote, `session['voted'] = True` is set. Subsequent visits to `/` redirect to `/results`, and direct `POST /vote` requests are rejected.

> *Note:* Clearing browser cookies allows the same person to vote again. This is the standard approach for simple apps without user login.

---

## Data Storage

Votes are stored in `votes.json` in the project root — a simple JSON object:

```json
{
  "1 – 5   (minimalist)": 3,
  "6 – 15  (normal)": 7,
  "16 – 30 (power user)": 2,
  "30+     (send help)": 5
}
```

The file is shared by all server processes and persists across restarts.
