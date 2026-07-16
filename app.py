from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = "preppath-secret-key"

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
    # Hum pehle hi users database setup kar chuke hain
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );
    """)
    conn.commit()
    conn.close()

# ─── AUTH ROUTES ────────────────────────────────────────────────────
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        try:
            conn = get_db()
            conn.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                         (name, email, password))
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
    return render_template("index.html")

# ─── ACTIVE GUIDES ROUTES ───────────────────────────────────────────
@app.route("/guides")
@login_required
def guides():
    return render_template("guides.html")

@app.route("/guides/confidence")
@login_required
def guide_confidence():
    return render_template("guide_confidence.html")

@app.route("/guides/dressing")
@login_required
def guide_dressing():
    return render_template("guide_dressing.html")

@app.route("/guides/bodylanguage")
@login_required
def guide_bodylanguage():
    return render_template("guide_bodylanguage.html")

@app.route("/guides/howtoanswer")
@login_required
def guide_howtoanswer():
    return render_template("guide_howtoanswer.html")

# ─── RUN ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    init_db()
    app.run(debug=True)