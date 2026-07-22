from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.secret_key = "preppath-secret-key-2024"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

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
        CREATE TABLE IF NOT EXISTS user_activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            activity_type TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()

def log_activity(user_id, activity_type):
    conn = get_db()
    conn.execute("INSERT INTO user_activity (user_id, activity_type) VALUES (?, ?)", (user_id, activity_type))
    conn.commit()
    conn.close()

def get_readiness_score(user_id):
    conn = get_db()
    activities = conn.execute("SELECT DISTINCT activity_type FROM user_activity WHERE user_id = ?", (user_id,)).fetchall()
    activity_list = [a["activity_type"] for a in activities]
    score = 0
    if "guide_confidence" in activity_list: score += 15
    if "guide_dressing" in activity_list: score += 15
    if "guide_bodylanguage" in activity_list: score += 15
    if "guide_howtoanswer" in activity_list: score += 15
    if "star_builder" in activity_list: score += 40
    conn.close()
    return min(score, 100)

@app.route("/")
@login_required
def home():
    score = get_readiness_score(current_user.id)
    return render_template("index.html", score=score)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
            conn.commit()
            conn.close()
            flash("Account created!", "success")
            return redirect(url_for("login"))
        except:
            flash("Registration Failed.", "danger")
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
        flash("Invalid Credentials", "danger")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

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

# Fixed: Star builder will now retain page scope to render variables safely
@app.route("/star-builder", methods=["GET", "POST"])
@login_required
def star_builder():
    built_answer = None
    if request.method == "POST":
        question = request.form.get("question") or "Behavioral Performance Question"
        situation = request.form.get("situation", "")
        task = request.form.get("task", "")
        action = request.form.get("action", "")
        result = request.form.get("result", "")
        
        built_answer = f"Situation: {situation} Task required: {task}. I took action by {action} which resulted in {result}."
        
        conn = get_db()
        conn.execute(
            "INSERT INTO star_answers (user_id, question, situation, task, action, result, full_answer) VALUES (?,?,?,?,?,?,?)",
            (current_user.id, question, situation, task, action, result, built_answer)
        )
        conn.commit()
        conn.close()
        log_activity(current_user.id, "star_builder")
        flash("STAR response successfully compiled and saved!", "success")
    return render_template("star_builder.html", answer=built_answer)

@app.route("/star-saved")
@login_required
def star_saved():
    conn = get_db()
    answers = conn.execute("SELECT * FROM star_answers WHERE user_id = ? ORDER BY id DESC", (current_user.id,)).fetchall()
    conn.close()
    return render_template("star_saved.html", answers=answers)

@app.route("/interview")
@login_required
def interview_setup():
    return "<h3>Mock Interview System Active</h3><a href='/'>Back Home</a>"

if __name__ == "__main__":
    init_db()
    app.run(debug=True)