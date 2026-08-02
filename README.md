# PrepPath — Interview Coach

PrepPath is a web-based interview preparation platform that helps users build confidence and skill ahead of job interviews. It combines structured preparation guides, a STAR-method answer builder, and an AI-powered mock interview simulator that generates tailored questions and instant feedback.

This project was developed as a final-year dissertation project for the BSc Computer Science degree at the University of Hertfordshire.

## Features

- **User accounts** — registration, login, profile editing, password change, and self-service account deletion
- **Preparation Guides** — confidence & mindset, dressing & presentation, body language, and how to answer questions
- **STAR Method Builder** — structure behavioural answers into a clear, saved format
- **AI Mock Interview** — generates role-specific interview questions (via the Anthropic Claude API) based on job role, key skills, and an optional CV upload, then scores answers on clarity, relevance, and completeness with actionable feedback
- **Interview Planner** — generates a day-by-day preparation plan counting down to the user's interview date
- **Progress Dashboard** — a readiness score and history of past mock interview sessions

## Tech Stack

- **Backend:** Python, Flask, Flask-Login, Flask-WTF (CSRF protection)
- **Database:** SQLite
- **AI:** Anthropic Claude API
- **CV parsing:** pdfplumber
- **Frontend:** Jinja2 templates, CSS/JS

## Security & Privacy

- Passwords are hashed with Werkzeug's `generate_password_hash`
- All forms are protected against CSRF attacks
- Personal identifiers (name, email, phone number, links) are stripped from CV text before it is sent to the Claude API
- Users can permanently delete their account and all associated data at any time

## Setup

1. Clone the repository and move into the project folder.
2. Create and activate a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate      # Windows
   ```
3. Install dependencies:
   ```
   python -m pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with:
   ```
   ANTHROPIC_API_KEY=your-anthropic-api-key
   SECRET_KEY=your-own-random-secret-string
   ```
5. Run the app:
   ```
   python app.py
   ```
6. Open `http://127.0.0.1:5000` in your browser.

## Project Structure

```
PrepPath/
├── app.py                 # Flask application and routes
├── static/
│   ├── css/style.css
│   └── js/script.js
├── templates/              # Jinja2 HTML templates
├── requirements.txt
└── preppath.db              # SQLite database (created on first run)
```

## Author

Hafsa Aatif (25016438) — BSc Computer Science, University of Hertfordshire