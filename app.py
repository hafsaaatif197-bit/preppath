from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf.csrf import CSRFProtect
import sqlite3
import anthropic
import pdfplumber
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-key-change-me")
csrf = CSRFProtect(app)

# ─── LOGIN MANAGER SETUP ────────────────────────────────────────────
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# ─── USER CLASS ─────────────────────────────────────────────────────
class User(UserMixin):
    def __init__(self, id, name, email):
        self.id = id
        self.name = name
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    if user:
        return User(user["id"], user["name"], user["email"])
    return None

# ─── DATABASE ───────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect("preppath.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS star_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            question TEXT,
            situation TEXT,
            task TEXT,
            action TEXT,
            result TEXT,
            full_answer TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            job_role TEXT,
            interview_type TEXT,
            question TEXT,
            answer TEXT,
            feedback TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS interview_planner (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            interview_date TEXT,
            job_role TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def log_activity(user_id, activity_type):
    conn = get_db()
    conn.execute("INSERT INTO user_activity (user_id, activity_type) VALUES (?, ?)",
                 (user_id, activity_type))
    conn.commit()
    conn.close()

def get_readiness_score(user_id):
    conn = get_db()
    score = 0
    activities = conn.execute(
        "SELECT DISTINCT activity_type FROM user_activity WHERE user_id = ?",
        (user_id,)
    ).fetchall()
    activity_list = [a["activity_type"] for a in activities]

    if "guide_confidence" in activity_list:   score += 10
    if "guide_dressing" in activity_list:     score += 10
    if "guide_bodylanguage" in activity_list: score += 10
    if "guide_howtoanswer" in activity_list:  score += 10
    if "star_builder" in activity_list:       score += 20

    sessions = conn.execute(
        "SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    interview_count = sessions["count"]
    if interview_count >= 1: score += 20
    if interview_count >= 3: score += 10
    if interview_count >= 5: score += 10

    conn.close()
    return min(score, 100)

# ─── AUTH ROUTES ────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "danger")
            return render_template("register.html")

        hashed_password = generate_password_hash(password)
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                         (name, email, hashed_password))
            conn.commit()
            conn.close()
            flash("Account created! Please log in.", "success")
            return redirect(url_for("login"))
        except:
            flash("Email already exists. Try logging in.", "danger")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password"], password):
            login_user(User(user["id"], user["name"], user["email"]))
            return redirect(url_for("home"))
        flash("Incorrect email or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# ─── MAIN ROUTES ────────────────────────────────────────────────────
@app.route("/")
@login_required
def home():
    score = get_readiness_score(current_user.id)
    conn = get_db()
    sessions = conn.execute(
        "SELECT COUNT(*) as count FROM interview_sessions WHERE user_id = ?",
        (current_user.id,)
    ).fetchone()
    conn.close()
    return render_template("index.html", score=score, session_count=sessions["count"])

# ─── GUIDE ROUTES ───────────────────────────────────────────────────
@app.route("/guides")
@login_required
def guides():
    return render_template("guides.html")

@app.route("/guides/confidence")
@login_required
def guide_confidence():
    log_activity(current_user.id, "guide_confidence")
    return render_template("guide_confidence.html")

@app.route("/guides/dressing")
@login_required
def guide_dressing():
    log_activity(current_user.id, "guide_dressing")
    return render_template("guide_dressing.html")

@app.route("/guides/bodylanguage")
@login_required
def guide_bodylanguage():
    log_activity(current_user.id, "guide_bodylanguage")
    return render_template("guide_bodylanguage.html")

@app.route("/guides/howtoanswer")
@login_required
def guide_howtoanswer():
    log_activity(current_user.id, "guide_howtoanswer")
    return render_template("guide_howtoanswer.html")

# ─── STAR BUILDER ───────────────────────────────────────────────────
@app.route("/star-builder", methods=["GET", "POST"])
@login_required
def star_builder():
    built_answer = None
    if request.method == "POST":
        question = request.form.get("question", "")
        situation = request.form["situation"]
        task = request.form["task"]
        action = request.form["action"]
        result = request.form["result"]
        built_answer = f"{situation}. {task}, so {action}. As a result, {result}."
        conn = get_db()
        conn.execute(
            "INSERT INTO star_answers (user_id, question, situation, task, action, result, full_answer) VALUES (?,?,?,?,?,?,?)",
            (current_user.id, question, situation, task, action, result, built_answer)
        )
        conn.commit()
        conn.close()
        log_activity(current_user.id, "star_builder")
    return render_template("star_builder.html", answer=built_answer)

@app.route("/star-saved")
@login_required
def star_saved():
    conn = get_db()
    answers = conn.execute(
        "SELECT * FROM star_answers WHERE user_id = ? ORDER BY created_at DESC",
        (current_user.id,)
    ).fetchall()
    conn.close()
    return render_template("star_saved.html", answers=answers)

# ─── INTERVIEW ROUTES ───────────────────────────────────────────────
TOTAL_INTERVIEW_QUESTIONS = 5  # how many questions make up one mock interview session

@app.route("/interview", methods=["GET", "POST"])
@login_required
def interview_setup():
    if request.method == "POST":
        session["job_role"] = request.form["job_role"]
        session["interview_type"] = request.form["interview_type"]
        session["skills"] = request.form.get("skills", "")
        session["interview_q_num"] = 0
        cv_text = ""
        if "cv" in request.files and request.files["cv"].filename != "":
            cv_file = request.files["cv"]
            with pdfplumber.open(cv_file) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        cv_text += text
        session["cv_text"] = cv_text[:1500]
        return redirect(url_for("interview_question"))
    return render_template("interview_setup.html")

@app.route("/interview/question")
@login_required
def interview_question():
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    job_role = session.get("job_role", "general role")
    interview_type = session.get("interview_type", "behavioural")
    skills = session.get("skills", "")
    cv_text = session.get("cv_text", "")

    prompt = f"""Generate one {interview_type} interview question for a candidate applying for a {job_role} position.
Their skills: {skills}
CV summary: {cv_text}
Return only the question itself, nothing else."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    question = message.content[0].text
    session["current_question"] = question
    session["interview_q_num"] = session.get("interview_q_num", 0) + 1
    return render_template(
        "interview.html",
        question=question,
        q_num=session["interview_q_num"],
        q_total=TOTAL_INTERVIEW_QUESTIONS
    )

@app.route("/interview/submit", methods=["POST"])
@login_required
def interview_submit():
    answer = request.form["answer"]
    question = session.get("current_question", "")
    job_role = session.get("job_role", "")

    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    prompt = f"""You are an interview coach. Evaluate this interview answer.

Question: {question}
Answer: {answer}

Provide feedback in exactly this format:
Clarity: [score out of 10] - [one sentence]
Relevance: [score out of 10] - [one sentence]
Completeness: [score out of 10] - [one sentence]
Overall Tip: [one specific, actionable improvement tip]"""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    feedback = message.content[0].text

    conn = get_db()
    conn.execute(
        "INSERT INTO interview_sessions (user_id, job_role, interview_type, question, answer, feedback) VALUES (?,?,?,?,?,?)",
        (current_user.id, job_role, session.get("interview_type"), question, answer, feedback)
    )
    conn.commit()
    conn.close()
    log_activity(current_user.id, "mock_interview")

    session_complete = session.get("interview_q_num", 0) >= TOTAL_INTERVIEW_QUESTIONS
    return render_template(
        "feedback.html",
        question=question,
        answer=answer,
        feedback=feedback,
        q_num=session.get("interview_q_num", 0),
        q_total=TOTAL_INTERVIEW_QUESTIONS,
        session_complete=session_complete
    )

# ─── INTERVIEW PLANNER (dedicated page) ─────────────────────────────
@app.route("/planner", methods=["GET", "POST"])
@login_required
def planner():
    if request.method == "POST":
        interview_date = request.form["interview_date"]
        job_role = request.form["job_role"]
        conn = get_db()
        conn.execute("DELETE FROM interview_planner WHERE user_id = ?", (current_user.id,))
        conn.execute(
            "INSERT INTO interview_planner (user_id, interview_date, job_role) VALUES (?,?,?)",
            (current_user.id, interview_date, job_role)
        )
        conn.commit()
        conn.close()
        return redirect(url_for("planner"))

    conn = get_db()
    plan_row = conn.execute(
        "SELECT * FROM interview_planner WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (current_user.id,)
    ).fetchone()
    conn.close()

    daily_plan = None
    if plan_row:
        interview_date = datetime.strptime(plan_row["interview_date"], "%Y-%m-%d")
        today = datetime.today()
        days_left = (interview_date - today).days
        daily_plan = generate_plan(days_left, plan_row["job_role"])

    return render_template("planner.html", planner=plan_row, daily_plan=daily_plan)

def generate_plan(days_left, job_role):
    if days_left <= 0:
        return [{"day": "Today", "task": "Good luck in your interview!"}]
    tasks = [
        "Read the Confidence & Mindset guide",
        "Read the Dressing & Presentation guide",
        "Read the Body Language guide",
        "Read the How to Answer Questions guide",
        "Build 2 STAR method answers",
        "Complete your first mock interview",
        "Review your feedback and do another mock interview",
    ]
    plan = []
    for i in range(min(days_left, len(tasks))):
        day_label = f"Day {i+1}" if i > 0 else "Today"
        plan.append({"day": day_label, "task": tasks[i]})
    return plan

# ─── DASHBOARD ──────────────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    conn = get_db()
    sessions = conn.execute(
        "SELECT * FROM interview_sessions WHERE user_id = ? ORDER BY created_at DESC",
        (current_user.id,)
    ).fetchall()
    conn.close()
    score = get_readiness_score(current_user.id)
    return render_template("dashboard.html", sessions=sessions, score=score)

# ─── RUN ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)