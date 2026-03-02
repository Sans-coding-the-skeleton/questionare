import json
from flask import (
    Flask, render_template, request,
    redirect, url_for, session, flash
)
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY


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
    """Show the voting page. Redirect to results if the user already voted."""
    if session.get("voted"):
        flash("You have already voted.", "info")
        return redirect(url_for("results"))
    return render_template(
        "index.html",
        question=config.QUESTION,
        answers=config.ANSWERS,
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


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app.run(debug=True)
