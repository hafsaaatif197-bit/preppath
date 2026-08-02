"""
Automated tests for PrepPath's core account and security features.

Run with:  python -m pytest tests/
"""


def register(client, name="Test User", email="test@example.com",
             password="password123", confirm=None):
    if confirm is None:
        confirm = password
    return client.post("/register", data={
        "name": name,
        "email": email,
        "password": password,
        "confirm_password": confirm,
    }, follow_redirects=True)


def login(client, email="test@example.com", password="password123"):
    return client.post("/login", data={
        "email": email,
        "password": password,
    }, follow_redirects=True)


# ─── REGISTRATION ────────────────────────────────────────────────────

def test_register_success(client):
    response = register(client)
    assert response.status_code == 200
    assert b"Account created" in response.data


def test_register_password_mismatch_is_rejected(client):
    response = register(client, password="password123", confirm="different123")
    assert b"Passwords do not match" in response.data


def test_register_short_password_is_rejected(client):
    response = register(client, password="short", confirm="short")
    assert b"at least 8 characters" in response.data


def test_register_duplicate_email_is_rejected(client):
    register(client, email="dupe@example.com")
    response = register(client, email="dupe@example.com")
    assert b"Email already exists" in response.data


# ─── LOGIN ───────────────────────────────────────────────────────────

def test_login_with_correct_credentials_succeeds(client):
    register(client)
    response = login(client)
    assert response.status_code == 200
    assert b"Hello" in response.data


def test_login_with_wrong_password_fails(client):
    register(client)
    response = login(client, password="wrongpassword")
    assert b"Incorrect email or password" in response.data


def test_protected_page_redirects_when_not_logged_in(client):
    response = client.get("/dashboard", follow_redirects=True)
    # Not logged in -> Flask-Login should bounce to the login page
    assert b"Sign In" in response.data or b"Login" in response.data


# ─── CSRF PROTECTION ─────────────────────────────────────────────────

def test_post_without_csrf_token_is_rejected(client):
    """
    With CSRF protection enabled, a POST request that doesn't include a
    valid csrf_token must be rejected (400 Bad Request), regardless of
    whether the user is logged in.
    """
    register(client)
    login(client)

    client.application.config["WTF_CSRF_ENABLED"] = True
    try:
        response = client.post("/account/update", data={
            "name": "New Name",
            "email": "test@example.com",
        })
        assert response.status_code == 400
    finally:
        client.application.config["WTF_CSRF_ENABLED"] = False


# ─── ACCOUNT DELETION ────────────────────────────────────────────────

def test_delete_account_removes_user(client):
    register(client)
    login(client)

    response = client.post("/account/delete", follow_redirects=True)
    assert b"permanently deleted" in response.data

    # The account should no longer exist - logging in again must fail
    response2 = login(client)
    assert b"Incorrect email or password" in response2.data