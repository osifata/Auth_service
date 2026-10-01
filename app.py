from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import secrets
import random
import re
import hashlib
import hmac
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "users.db"

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Безопасные настройки стандартной Flask-сессии.
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False  # Для локальной разработки в PyCharm/localhost.

USERNAME_RE = re.compile(r"^[A-Za-z0-9]{3,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{6,}$")


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def hash_password(password):
    """PBKDF2-HMAC-SHA256: встроенный алгоритм hashlib."""
    salt = secrets.token_bytes(16)
    iterations = 310_000
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${derived_key.hex()}"


def verify_password(password, stored_hash):
    try:
        algorithm, iterations, salt_hex, key_hex = stored_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)
        salt = bytes.fromhex(salt_hex)
        expected_key = bytes.fromhex(key_hex)

        actual_key = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )
        return hmac.compare_digest(actual_key, expected_key)
    except (ValueError, TypeError):
        return False


def generate_captcha():
    """Создает новую математическую CAPTCHA и сохраняет ответ в серверной сессии."""
    number1 = random.randint(1, 20)
    number2 = random.randint(1, 20)

    session["captcha_answer"] = number1 + number2
    return f"Сколько будет {number1} + {number2}?"


def rotate_captcha():
    session.pop("captcha_answer", None)
    return generate_captcha()


def check_captcha(user_answer):
    """Проверяет CAPTCHA и после каждой проверки сразу меняет ее."""
    saved_answer = session.get("captcha_answer")

    try:
        correct = saved_answer is not None and int(user_answer) == int(saved_answer)
    except (TypeError, ValueError):
        correct = False

    # CAPTCHA одноразовая: повторно использовать тот же ответ нельзя.
    rotate_captcha()
    return correct


def validation_error(message):
    return jsonify({"success": False, "message": message}), 400


@app.route("/")
def index():
    if session.get("user_id"):
        return redirect(url_for("profile_page"))
    return redirect(url_for("login_page"))


@app.route("/login.html")
@app.route("/login")
def login_page():
    captcha_question = generate_captcha()
    success_message = request.args.get("success")
    return render_template(
        "login.html",
        captcha_question=captcha_question,
        success_message=success_message
    )


@app.route("/register.html")
@app.route("/register")
def register_page():
    captcha_question = generate_captcha()
    return render_template("register.html", captcha_question=captcha_question)


@app.route("/profile.html")
@app.route("/profile")
def profile_page():
    # Защита страницы на сервере.
    if not session.get("user_id"):
        return redirect(url_for("login_page"))

    return render_template("profile.html")


@app.post("/api/register")
def register():
    data = request.get_json(silent=True) or {}

    username = str(data.get("username", "")).strip()
    email = str(data.get("email", "")).strip().lower()
    password = str(data.get("password", ""))
    password_confirm = str(data.get("password_confirm", ""))
    captcha = str(data.get("captcha", "")).strip()

    # Вторичная серверная валидация.
    if not USERNAME_RE.fullmatch(username):
        return validation_error(
            "Имя пользователя: только латиница и цифры, от 3 до 20 символов."
        )

    if not EMAIL_RE.fullmatch(email):
        return validation_error("Введите корректный email.")

    if not PASSWORD_RE.fullmatch(password):
        return validation_error(
            "Пароль должен содержать минимум 6 символов, буквы и цифры."
        )

    if password != password_confirm:
        return validation_error("Пароли не совпадают")

    if not captcha:
        return validation_error("Введите ответ капчи")

    if not check_captcha(captcha):
        return validation_error("Неверный ответ капчи")

    conn = get_db()
    try:
        existing_username = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (username,)
        ).fetchone()

        if existing_username:
            return validation_error("Пользователь с таким именем уже существует")

        existing_email = conn.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if existing_email:
            return validation_error(
                "Пользователь с таким email уже зарегистрирован"
            )

        password_hash = hash_password(password)

        conn.execute(
            """
            INSERT INTO users (username, email, password_hash)
            VALUES (?, ?, ?)
            """,
            (username, email, password_hash)
        )
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Регистрация успешна!"
        })

    except sqlite3.IntegrityError:
        return validation_error("Пользователь с таким именем или email уже существует")
    finally:
        conn.close()


@app.post("/api/login")
def login():
    data = request.get_json(silent=True) or {}

    login_value = str(data.get("login", "")).strip()
    password = str(data.get("password", ""))
    captcha = str(data.get("captcha", "")).strip()

    if not login_value or not password:
        # CAPTCHA тоже одноразовая при попытке входа.
        if captcha:
            check_captcha(captcha)
        else:
            rotate_captcha()
        return validation_error("Неверный логин или пароль")

    if not captcha:
        rotate_captcha()
        return validation_error("Неверный логин или пароль")

    captcha_correct = check_captcha(captcha)

    # Даже при неверной CAPTCHA не сообщаем, существует ли пользователь.
    if not captcha_correct:
        return validation_error("Неверный логин или пароль")

    conn = get_db()
    try:
        user = conn.execute(
            """
            SELECT id, username, email, password_hash, created_at
            FROM users
            WHERE username = ? OR email = ?
            """,
            (login_value, login_value.lower())
        ).fetchone()
    finally:
        conn.close()

    if not user or not verify_password(password, user["password_hash"]):
        return validation_error("Неверный логин или пароль")

    # Стандартная серверная Flask-сессия, без JWT.
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]

    return jsonify({
        "success": True,
        "message": "Вход выполнен успешно"
    })


@app.get("/api/profile")
def get_profile():
    if not session.get("user_id"):
        return jsonify({"success": False, "message": "Не авторизован"}), 401

    conn = get_db()
    try:
        user = conn.execute(
            """
            SELECT id, username, email, created_at
            FROM users
            WHERE id = ?
            """,
            (session["user_id"],)
        ).fetchone()
    finally:
        conn.close()

    if not user:
        session.clear()
        return jsonify({"success": False, "message": "Не авторизован"}), 401

    return jsonify({
        "success": True,
        "user": {
            "username": user["username"],
            "email": user["email"],
            "created_at": user["created_at"],
            "role": "Пользователь"
        }
    })


@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"success": True})


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
