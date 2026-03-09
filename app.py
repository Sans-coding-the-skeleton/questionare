import json
import hmac
import hashlib
import os
import subprocess
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


# ── Security headers ──────────────────────────────────────────────────────────

@app.after_request
def set_security_headers(response):
    """Add security headers to every response."""
    # Prevent the app from being embedded in a frame/iframe.
    # CSP frame-ancestors is the modern replacement for X-Frame-Options;
    # we send both for maximum browser compatibility.
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "frame-ancestors 'none'"

    # HTTP Strict Transport Security (HSTS)
    # Rollout schedule per https://hstspreload.org/:
    #   Step 1 – 300 s   (5 min)   ← current, safe to test
    #   Step 2 – 86 400 s (1 day)  once step 1 is confirmed working
    #   Step 3 – 2 592 000 s (30 days)
    #   Step 4 – 31 536 000 s (1 year) + includeSubDomains + preload
    response.headers["Strict-Transport-Security"] = (
        "max-age=300"
    )
    return response


# ── Vote storage helpers ──────────────────────────────────────────────────────

def _load_votes() -> dict:
    """Return vote dict from JSON file, creating it fresh if it doesn't exist.

    Always re-syncs the stored keys against config.ANSWERS so that changing
    the answer list in config never causes stale keys to break voting or the
    results page.
    """
    if not config.VOTES_FILE.exists():
        return _reset_votes()
    with open(config.VOTES_FILE, "r", encoding="utf-8") as f:
        stored = json.load(f)

    # Build a clean dict that matches config.ANSWERS exactly.
    # Unknown keys are dropped; missing keys start at 0.
    synced = {answer: stored.get(answer, 0) for answer in config.ANSWERS}
    if synced != stored:
        _save_votes(synced)
    return synced


def _save_votes(votes: dict) -> None:
    with open(config.VOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(votes, f, ensure_ascii=False, indent=2)


def _reset_votes() -> dict:
    votes = {answer: 0 for answer in config.ANSWERS}
    _save_votes(votes)
    return votes


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Show the voting page. If the user already voted, show the page in read-only mode."""
    already_voted = bool(session.get("voted"))
    return render_template(
        "index.html",
        question=config.QUESTION,
        answers=config.ANSWERS,
        already_voted=already_voted,
    )


@app.route("/vote", methods=["POST"])
def vote():
    """Record the user's vote."""
    # Anti-double-vote: server-side session flag
    if session.get("voted"):
        flash("You have already voted!", "warning")
        return redirect(url_for("results"))

    chosen = request.form.get("answer")
    votes = _load_votes()

    if chosen not in votes:
        flash("Invalid answer. Please select one of the options.", "danger")
        return redirect(url_for("index"))

    votes[chosen] += 1
    _save_votes(votes)

    # Mark this browser session as having voted
    session["voted"] = True
    flash("Your vote has been recorded!", "success")
    return redirect(url_for("results"))


@app.route("/results")
def results():
    """Show current vote counts."""
    votes = _load_votes()
    total = sum(votes.values())
    # Build list of (answer, count, percentage) for the template
    results_data = []
    for answer, count in votes.items():
        pct = round(count / total * 100) if total > 0 else 0
        results_data.append((answer, count, pct))

    already_voted = session.get("voted", False)
    return render_template(
        "results.html",
        question=config.QUESTION,
        results=results_data,
        total=total,
        already_voted=already_voted,
    )


@app.route("/reset", methods=["POST"])
def reset():
    """Reset votes if the supplied token matches the server-side token."""
    token = request.form.get("token", "").strip()
    if token == config.RESET_TOKEN:
        _reset_votes()
        # Also clear everyone's voted flag isn't feasible with plain sessions,
        # but we clear the current user's flag so they can vote again.
        session.pop("voted", None)
        flash("Votes have been reset successfully.", "success")
    else:
        flash("Incorrect token – reset was not performed.", "danger")
    return redirect(url_for("results"))


@app.route("/about")
def about():
    """Show the About / O anketě page."""
    return render_template("about.html")


@app.route("/update_server", methods=["POST"])
def update_server():
    """Webhook endpoint to automatically pull from GitHub and reload PythonAnywhere."""
    if not config.WEBHOOK_SECRET:
        return "Webhook secret not configured.", 500

    # Verify GitHub signature
    signature = request.headers.get("X-Hub-Signature-256")
    if not signature:
        return "Missing signature", 403

    mac = hmac.new(config.WEBHOOK_SECRET.encode(), msg=request.data, digestmod=hashlib.sha256)
    expected_signature = "sha256=" + mac.hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        return "Invalid signature", 403

    # On push event, pull code and reload WSGI
    if request.headers.get("X-GitHub-Event") == "push":
        try:
            # Pull new code
            subprocess.run(["git", "pull", "origin", "main"], check=True, cwd=config.BASE_DIR)

            # Reload PythonAnywhere web app
            if config.PYTHONANYWHERE_DOMAIN:
                wsgi_file = f"/var/www/{config.PYTHONANYWHERE_DOMAIN.replace('.', '_')}_wsgi.py"
            elif config.PYTHONANYWHERE_USERNAME:
                wsgi_file = f"/var/www/{config.PYTHONANYWHERE_USERNAME}_pythonanywhere_com_wsgi.py"
            else:
                wsgi_file = None

            if wsgi_file and os.path.exists(wsgi_file):
                os.utime(wsgi_file, None)

            return "Updated PythonAnywhere successfully", 200
        except subprocess.CalledProcessError as e:
            return f"Git pull failed: {str(e)}", 500

    return "Ignored event", 200


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
