# Use of Artificial Intelligence in this Project

In line with University of Hertfordshire guidance (ask.herts.ac.uk/ai-tools), this
project uses the Claude API (Anthropic) as a core, user-facing feature of the
application.

## How it is used

PrepPath uses the Claude API to:
- Generate tailored mock interview questions based on the user's job role,
  key skills, and (optionally) their CV
- Generate feedback on the user's submitted answers, scored on clarity,
  relevance, and completeness, with an actionable improvement tip

This is implemented in `app.py`, in the `interview_question()` and
`interview_submit()` routes, which call `client.messages.create()` from the
Anthropic Python SDK. To protect user privacy, personal identifiers (name,
email, phone number, links) are stripped from any uploaded CV text before it
is included in the API request (see `sanitize_cv_text()` in `app.py`).

This use of AI is described in full in the main report.