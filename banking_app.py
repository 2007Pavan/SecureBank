
from flask import (
    Flask, request, redirect, url_for,
    session, flash, render_template_string, get_flashed_messages
)
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import Error, IntegrityError
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps
from markupsafe import Markup
from database import get_connection, create_tables
import secrets
import uuid
import os
import re


app = Flask(__name__)
app.secret_key = os.getenv("BANK_SECRET_KEY", secrets.token_hex(32))

# Educational demonstration only. No real OTP is sent.
DEMO_OTP = "123456"


# ==========================================================
# DESIGN
# ==========================================================

BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SecureBank | Banking Management System</title>

<style>
* {
    box-sizing: border-box;
}

body {
    margin: 0;
    font-family: Inter, Arial, sans-serif;
    background: #f4f7fb;
    color: #17243a;
}

nav {
    background: #10243e;
    color: white;
    padding: 17px 6%;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 15px;
    box-shadow: 0 3px 15px #10243e20;
}

.brand {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: .3px;
}

.brand span {
    color: #48a5ff;
}

.nav-links {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 18px;
}

nav a {
    color: #e4edf8;
    text-decoration: none;
    font-size: 14px;
    font-weight: 600;
}

nav a:hover {
    color: #65b5ff;
}

.container {
    max-width: 1150px;
    margin: 32px auto;
    padding: 0 20px;
    min-height: 70vh;
}

h1 {
    color: #10243e;
    margin-top: 0;
}

h2 {
    color: #183653;
}

p {
    line-height: 1.6;
}

.muted {
    color: #718096;
    font-size: 14px;
}

.card {
    background: white;
    padding: 26px;
    border-radius: 15px;
    box-shadow: 0 5px 22px #17243a0c;
    margin-bottom: 22px;
    border: 1px solid #edf1f6;
}

.auth {
    max-width: 490px;
    margin: 45px auto;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 18px;
    margin: 22px 0;
}

.stat {
    padding: 23px;
    border-radius: 15px;
    background: white;
    border: 1px solid #e8eef5;
    box-shadow: 0 4px 18px #17243a08;
}

.stat-label {
    color: #718096;
    font-size: 13px;
    font-weight: 600;
}

.amount {
    font-size: 27px;
    font-weight: 800;
    margin-top: 10px;
    color: #10243e;
    overflow-wrap: anywhere;
}

.balance-card {
    background: linear-gradient(125deg, #10243e, #174c7d);
    color: white;
    padding: 32px;
    border-radius: 18px;
    margin-bottom: 23px;
    box-shadow: 0 10px 25px #10243e25;
}

.balance-card h1,
.balance-card h2,
.balance-card .amount {
    color: white;
}

.balance-card .muted {
    color: #c5d8ed;
}

.balance-card .amount {
    font-size: 36px;
}

label {
    display: block;
    margin: 17px 0 7px;
    font-weight: 700;
    font-size: 14px;
    color: #263b53;
}

input,
select {
    width: 100%;
    padding: 13px 14px;
    border: 1px solid #d7e0eb;
    border-radius: 9px;
    font-size: 15px;
    outline: none;
    background: #fff;
    color: #17243a;
}

input:focus,
select:focus {
    border-color: #2785df;
    box-shadow: 0 0 0 3px #2785df18;
}

button,
.btn {
    display: inline-block;
    border: 0;
    background: #1769c2;
    color: white;
    padding: 12px 19px;
    border-radius: 9px;
    text-decoration: none;
    cursor: pointer;
    font-size: 14px;
    font-weight: 700;
    margin-top: 17px;
    transition: .2s;
}

button:hover,
.btn:hover {
    background: #0e4f99;
    transform: translateY(-1px);
}

.btn-secondary {
    background: #eaf2fb;
    color: #145a9e;
}

.btn-secondary:hover {
    background: #d9e9fa;
    color: #104b84;
}

.btn-danger {
    background: #dc4545;
}

.btn-danger:hover {
    background: #b72c2c;
}

.actions {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
}

.message {
    padding: 14px 16px;
    border-radius: 9px;
    margin-bottom: 15px;
    font-size: 14px;
    font-weight: 600;
}

.success {
    background: #dcfce7;
    color: #166534;
}

.error {
    background: #fee2e2;
    color: #991b1b;
}

.info {
    background: #e0f2fe;
    color: #075985;
}

table {
    width: 100%;
    border-collapse: collapse;
}

th,
td {
    text-align: left;
    padding: 14px 11px;
    border-bottom: 1px solid #e8edf3;
    font-size: 14px;
}

th {
    background: #f4f7fb;
    color: #455a72;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: .4px;
}

.positive {
    color: #15803d;
    font-weight: 700;
}

.negative {
    color: #dc2626;
    font-weight: 700;
}

.badge {
    display: inline-block;
    padding: 5px 10px;
    background: #dcfce7;
    color: #166534;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 800;
}

.profile-row {
    padding: 15px 0;
    border-bottom: 1px solid #edf1f5;
}

.profile-label {
    color: #718096;
    font-size: 12px;
    margin-bottom: 5px;
}

.profile-value {
    font-size: 16px;
    font-weight: 700;
    overflow-wrap: anywhere;
}

.otp-box {
    background: #f1f7ff;
    border: 1px solid #d9eaff;
    border-radius: 13px;
    padding: 20px;
    margin-top: 22px;
}

.otp-input {
    text-align: center;
    letter-spacing: 12px;
    font-size: 25px;
    font-weight: 800;
    max-width: 230px;
}

.receipt {
    max-width: 650px;
    margin: auto;
}

.receipt-header {
    text-align: center;
    border-bottom: 2px dashed #d9e1ea;
    padding-bottom: 20px;
    margin-bottom: 20px;
}

.receipt-row {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    padding: 13px 0;
    border-bottom: 1px solid #edf1f5;
    font-size: 14px;
}

.receipt-row span:last-child {
    font-weight: 700;
    text-align: right;
    overflow-wrap: anywhere;
}

footer {
    text-align: center;
    padding: 28px;
    color: #8290a2;
    font-size: 13px;
}

@media(max-width: 650px) {
    nav {
        padding: 16px;
    }

    .nav-links {
        gap: 12px;
    }

    nav a {
        font-size: 12px;
    }

    .container {
        margin: 22px auto;
        padding: 0 13px;
    }

    .card {
        padding: 19px;
    }

    .balance-card {
        padding: 24px;
    }

    .balance-card .amount {
        font-size: 29px;
    }

    th,
    td {
        padding: 10px 7px;
        font-size: 12px;
    }

    .receipt-row {
        font-size: 12px;
    }
}

@media print {
    nav,
    footer,
    .no-print {
        display: none !important;
    }

    body {
        background: white;
    }

    .container {
        margin: 0;
        max-width: 100%;
    }

    .card {
        box-shadow: none;
        border: 1px solid #ddd;
    }
}
</style>
</head>

<body>

<nav>
    <div class="brand">Secure<span>Bank</span></div>

    <div class="nav-links">
    {% if username %}
        <a href="{{ url_for('dashboard') }}">Dashboard</a>
        <a href="{{ url_for('deposit') }}">Deposit</a>
        <a href="{{ url_for('withdraw') }}">Withdraw</a>
        <a href="{{ url_for('beneficiaries') }}">Beneficiaries</a>
        <a href="{{ url_for('transfer') }}">Transfer</a>
        <a href="{{ url_for('history') }}">History</a>
        <a href="{{ url_for('profile') }}">Profile</a>
        <a href="{{ url_for('logout') }}">Logout</a>
    {% else %}
        <a href="{{ url_for('login') }}">Login</a>
        <a href="{{ url_for('register') }}">Register</a>
    {% endif %}
    </div>
</nav>

<div class="container">
    {% for category, message in messages %}
        <div class="message {{ category }}">{{ message }}</div>
    {% endfor %}
    {{ body }}
</div>

<footer>
    SecureBank | Banking Management System | College Mini Project
    <br>Educational Demonstration Only — Not a Real Banking Service
</footer>

</body>
</html>
"""


def render_page(content, **context):
    rendered_body = render_template_string(content, **context)

    return render_template_string(
        BASE_HTML,
        body=Markup(rendered_body),
        username=session.get("username"),
        messages=get_flashed_messages(with_categories=True)
    )


# ==========================================================
# COMMON FUNCTIONS
# ==========================================================

def login_required(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("login"))
        return function(*args, **kwargs)
    return wrapper


def get_user_account(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                u.user_id,
                u.full_name,
                u.email,
                u.phone,
                u.username,
                u.created_at AS user_created_at,
                a.account_number,
                a.balance,
                a.account_type,
                a.created_at AS account_created_at
            FROM users u
            JOIN accounts a ON u.user_id = a.user_id
            WHERE u.user_id = %s
        """, (user_id,))

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def parse_amount(value):
    try:
        amount = Decimal(value)
        amount = amount.quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

        if not amount.is_finite() or amount <= 0:
            return None

        if amount > Decimal("9999999999999.99"):
            return None

        return amount

    except (InvalidOperation, TypeError, ValueError):
        return None


def new_reference():
    return "TXN" + uuid.uuid4().hex[:12].upper()


def save_account_transaction(
    account_number,
    amount,
    transaction_type,
    description
):
    """
    Used for deposits and withdrawals.
    The sender and receiver are the same account because
    the existing database schema requires both fields.
    """

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT balance
            FROM accounts
            WHERE account_number = %s
            FOR UPDATE
        """, (account_number,))

        account = cursor.fetchone()

        if not account:
            connection.rollback()
            return None, "Account not found."

        current_balance = account["balance"]

        if transaction_type == "Deposit":
            cursor.execute("""
                UPDATE accounts
                SET balance = balance + %s
                WHERE account_number = %s
            """, (amount, account_number))

        elif transaction_type == "Withdrawal":
            if current_balance < amount:
                connection.rollback()
                return None, "Insufficient balance for this withdrawal."

            cursor.execute("""
                UPDATE accounts
                SET balance = balance - %s
                WHERE account_number = %s
            """, (amount, account_number))

        reference = new_reference()

        cursor.execute("""
            INSERT INTO transactions (
                reference_number,
                sender_account,
                receiver_account,
                amount,
                transaction_type,
                description,
                status
            )
            VALUES (%s, %s, %s, %s, %s, %s, 'SUCCESS')
        """, (
            reference,
            account_number,
            account_number,
            amount,
            transaction_type,
            description
        ))

        connection.commit()
        return reference, None

    except Error as error:
        connection.rollback()
        print("Account transaction error:", error)
        return None, "Transaction failed. Please try again."

    finally:
        cursor.close()
        connection.close()


# ==========================================================
# HOME
# ==========================================================

@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# ==========================================================
# REGISTRATION
# ==========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        full_name = request.form.get("full_name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not all([full_name, email, phone, username, password]):
            flash("Please complete all registration fields.", "error")
            return redirect(url_for("register"))

        if len(full_name) > 100 or len(email) > 120:
            flash("One or more fields exceed the allowed length.", "error")
            return redirect(url_for("register"))

        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            flash("Please enter a valid email address.", "error")
            return redirect(url_for("register"))

        if not re.fullmatch(r"[0-9]{10,15}", phone):
            flash("Phone number must contain 10 to 15 digits.", "error")
            return redirect(url_for("register"))

        if len(username) < 3 or len(username) > 50:
            flash("Username must contain 3 to 50 characters.", "error")
            return redirect(url_for("register"))

        if len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
            return redirect(url_for("register"))

        connection = get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute("""
                INSERT INTO users
                (full_name, email, phone, username, password_hash)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                full_name,
                email,
                phone,
                username,
                generate_password_hash(password)
            ))

            user_id = cursor.lastrowid

            account_number = "10" + str(
                secrets.randbelow(10**8)
            ).zfill(8)

            cursor.execute("""
                INSERT INTO accounts
                (user_id, account_number, balance, account_type)
                VALUES (%s, %s, %s, %s)
            """, (
                user_id,
                account_number,
                Decimal("10000.00"),
                "Savings"
            ))

            connection.commit()

            flash(
                "Account created successfully! Account Number: "
                + account_number,
                "success"
            )

            return redirect(url_for("login"))

        except IntegrityError:
            connection.rollback()
            flash("Username, email or account number already exists.", "error")

        except Error as error:
            connection.rollback()
            print("Registration error:", error)
            flash("Registration failed. Please check the database.", "error")

        finally:
            cursor.close()
            connection.close()

    content = """
    <div class="card auth">
        <h1>Create Your Account</h1>
        <p class="muted">Join SecureBank and manage your demo account.</p>

        <form method="POST">
            <label>Full Name</label>
            <input name="full_name" maxlength="100" required>

            <label>Email Address</label>
            <input type="email" name="email" maxlength="120" required>

            <label>Phone Number</label>
            <input name="phone" maxlength="15"
                   inputmode="numeric" required>

            <label>Username</label>
            <input name="username" minlength="3"
                   maxlength="50" required>

            <label>Password</label>
            <input type="password" name="password"
                   minlength="8" required>

            <button type="submit">Create Account</button>
        </form>

        <p class="muted">
            Already registered?
            <a href="{{ url_for('login') }}">Login here</a>
        </p>
        <p class="muted">
            Demo opening balance: ₹10,000.00
        </p>
    </div>
    """

    return render_page(content)


# ==========================================================
# LOGIN
# ==========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT user_id, username, password_hash
                FROM users
                WHERE username = %s
            """, (username,))

            user = cursor.fetchone()

            if user and check_password_hash(
                user["password_hash"], password
            ):
                session.clear()
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]

                flash("Welcome back to SecureBank!", "success")
                return redirect(url_for("dashboard"))

            flash("Incorrect username or password.", "error")

        except Error as error:
            print("Login error:", error)
            flash("Unable to log in. Check the database connection.", "error")

        finally:
            cursor.close()
            connection.close()

    content = """
    <div class="card auth">
        <h1>Welcome Back</h1>
        <p class="muted">Sign in to your SecureBank account.</p>

        <form method="POST">
            <label>Username</label>
            <input name="username" autocomplete="username" required>

            <label>Password</label>
            <input type="password" name="password"
                   autocomplete="current-password" required>

            <button type="submit">Secure Login</button>
        </form>

        <p class="muted">
            New to SecureBank?
            <a href="{{ url_for('register') }}">Create an account</a>
        </p>
    </div>
    """

    return render_page(content)


# ==========================================================
# LOGOUT
# ==========================================================

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out successfully.", "success")
    return redirect(url_for("login"))


# ==========================================================
# DASHBOARD
# ==========================================================

@app.route("/dashboard")
@login_required
def dashboard():

    account = get_user_account(session["user_id"])

    if not account:
        session.clear()
        flash("Account details could not be found.", "error")
        return redirect(url_for("login"))

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE sender_account = %s OR receiver_account = %s
        """, (
            account["account_number"],
            account["account_number"]
        ))

        total_transactions = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT reference_number, sender_account,
                   receiver_account, amount, transaction_type,
                   description, transaction_date
            FROM transactions
            WHERE sender_account = %s OR receiver_account = %s
            ORDER BY transaction_date DESC
            LIMIT 5
        """, (
            account["account_number"],
            account["account_number"]
        ))

        recent_transactions = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    content = """
    <h1>Welcome, {{ account.full_name }}!</h1>
    <p class="muted">
        Here's an overview of your SecureBank account.
    </p>

    <div class="balance-card">
        <p class="muted">TOTAL AVAILABLE BALANCE</p>
        <div class="amount">
            ₹{{ "%.2f"|format(account.balance|float) }}
        </div>
        <p class="muted">
            {{ account.account_type }} Account
            &nbsp; | &nbsp; {{ account.account_number }}
        </p>
    </div>

    <div class="grid">
        <div class="stat">
            <div class="stat-label">Account Number</div>
            <div class="amount" style="font-size:21px">
                {{ account.account_number }}
            </div>
        </div>

        <div class="stat">
            <div class="stat-label">Account Type</div>
            <div class="amount" style="font-size:21px">
                {{ account.account_type }}
            </div>
        </div>

        <div class="stat">
            <div class="stat-label">Total Transactions</div>
            <div class="amount">{{ total_transactions }}</div>
        </div>
    </div>

    <div class="card">
        <h2>Quick Banking Actions</h2>
        <div class="actions">
            <a class="btn" href="{{ url_for('deposit') }}">＋ Deposit</a>
            <a class="btn" href="{{ url_for('withdraw') }}">− Withdraw</a>
            <a class="btn" href="{{ url_for('transfer') }}">Transfer Money</a>
            <a class="btn btn-secondary"
               href="{{ url_for('beneficiaries') }}">Beneficiaries</a>
            <a class="btn btn-secondary"
               href="{{ url_for('profile') }}">My Profile</a>
        </div>
    </div>

    <div class="card">
        <h2>Recent Transactions</h2>

        {% if recent_transactions %}
        <div style="overflow-x:auto">
        <table>
            <tr>
                <th>Reference</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Date</th>
            </tr>

            {% for item in recent_transactions %}
            <tr>
                <td>
                    <a href="{{ url_for('receipt',
                       reference=item.reference_number) }}">
                       {{ item.reference_number }}
                    </a>
                </td>
                <td>{{ item.transaction_type }}</td>
                <td>₹{{ "%.2f"|format(item.amount|float) }}</td>
                <td>{{ item.transaction_date }}</td>
            </tr>
            {% endfor %}
        </table>
        </div>
        {% else %}
        <p class="muted">No transactions available yet.</p>
        {% endif %}

        <a class="btn btn-secondary"
           href="{{ url_for('history') }}">View All Transactions</a>
    </div>
    """

    return render_page(
        content,
        account=account,
        total_transactions=total_transactions,
        recent_transactions=recent_transactions
    )


# ==========================================================
# DEPOSIT
# ==========================================================

@app.route("/deposit", methods=["GET", "POST"])
@login_required
def deposit():

    account = get_user_account(session["user_id"])

    if request.method == "POST":

        amount = parse_amount(request.form.get("amount", ""))
        description = request.form.get("description", "").strip()

        if not amount:
            flash("Enter a valid deposit amount greater than zero.", "error")
            return redirect(url_for("deposit"))

        if len(description) > 255:
            flash("Description must not exceed 255 characters.", "error")
            return redirect(url_for("deposit"))

        reference, error = save_account_transaction(
            account["account_number"],
            amount,
            "Deposit",
            description or "Cash deposit"
        )

        if error:
            flash(error, "error")
            return redirect(url_for("deposit"))

        flash("Deposit completed successfully!", "success")
        return redirect(url_for("receipt", reference=reference))

    content = """
    <div class="card auth">
        <h1>Deposit Money</h1>
        <p class="muted">
            Add money to your SecureBank demo account.
        </p>

        <div class="stat">
            <div class="stat-label">Current Balance</div>
            <div class="amount">
                ₹{{ "%.2f"|format(account.balance|float) }}
            </div>
        </div>

        <form method="POST">
            <label>Deposit Amount (₹)</label>
            <input type="number" name="amount"
                   min="0.01" max="9999999999999.99"
                   step="0.01" required>

            <label>Description</label>
            <input name="description" maxlength="255"
                   placeholder="Example: Cash deposit">

            <button type="submit">Confirm Deposit</button>
        </form>
    </div>
    """

    return render_page(content, account=account)


# ==========================================================
# WITHDRAWAL
# ==========================================================

@app.route("/withdraw", methods=["GET", "POST"])
@login_required
def withdraw():

    account = get_user_account(session["user_id"])

    if request.method == "POST":

        amount = parse_amount(request.form.get("amount", ""))
        description = request.form.get("description", "").strip()

        if not amount:
            flash("Enter a valid withdrawal amount greater than zero.", "error")
            return redirect(url_for("withdraw"))

        if len(description) > 255:
            flash("Description must not exceed 255 characters.", "error")
            return redirect(url_for("withdraw"))

        reference, error = save_account_transaction(
            account["account_number"],
            amount,
            "Withdrawal",
            description or "Cash withdrawal"
        )

        if error:
            flash(error, "error")
            return redirect(url_for("withdraw"))

        flash("Withdrawal completed successfully!", "success")
        return redirect(url_for("receipt", reference=reference))

    content = """
    <div class="card auth">
        <h1>Withdraw Money</h1>
        <p class="muted">
            Withdraw money from your SecureBank demo account.
        </p>

        <div class="stat">
            <div class="stat-label">Available Balance</div>
            <div class="amount">
                ₹{{ "%.2f"|format(account.balance|float) }}
            </div>
        </div>

        <form method="POST">
            <label>Withdrawal Amount (₹)</label>
            <input type="number" name="amount"
                   min="0.01" max="9999999999999.99"
                   step="0.01" required>

            <label>Description</label>
            <input name="description" maxlength="255"
                   placeholder="Example: ATM withdrawal">

            <button type="submit" class="btn-danger">
                Confirm Withdrawal
            </button>
        </form>
    </div>
    """

    return render_page(content, account=account)


# ==========================================================
# BENEFICIARY MANAGEMENT
# ==========================================================

@app.route("/beneficiaries", methods=["GET", "POST"])
@login_required
def beneficiaries():

    user_id = session["user_id"]

    if request.method == "POST":

        account_number = request.form.get(
            "account_number", ""
        ).strip()

        nickname = request.form.get("nickname", "").strip()

        if not account_number:
            flash("Enter the beneficiary account number.", "error")
            return redirect(url_for("beneficiaries"))

        if len(nickname) > 60:
            flash("Nickname must not exceed 60 characters.", "error")
            return redirect(url_for("beneficiaries"))

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT account_number
                FROM accounts
                WHERE account_number = %s
            """, (account_number,))

            recipient = cursor.fetchone()

            cursor.execute("""
                SELECT account_number
                FROM accounts
                WHERE user_id = %s
            """, (user_id,))

            own_account = cursor.fetchone()

            if not recipient:
                flash("This bank account does not exist.", "error")

            elif own_account["account_number"] == account_number:
                flash("You cannot add your own account.", "error")

            else:
                cursor.execute("""
                    INSERT INTO beneficiaries
                    (user_id, beneficiary_account, nickname)
                    VALUES (%s, %s, %s)
                """, (
                    user_id,
                    account_number,
                    nickname or "Beneficiary"
                ))

                connection.commit()
                flash("Beneficiary added successfully!", "success")

        except IntegrityError:
            connection.rollback()
            flash("This beneficiary has already been added.", "error")

        except Error as error:
            connection.rollback()
            print("Beneficiary error:", error)
            flash("Could not add beneficiary.", "error")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("beneficiaries"))

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT beneficiary_id, beneficiary_account, nickname
            FROM beneficiaries
            WHERE user_id = %s
            ORDER BY beneficiary_id DESC
        """, (user_id,))

        beneficiary_list = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    content = """
    <div class="card">
        <h1>Beneficiary Management</h1>
        <p class="muted">
            Add another registered SecureBank account.
        </p>

        <form method="POST">
            <label>Beneficiary Account Number</label>
            <input name="account_number"
                   maxlength="20" required>

            <label>Beneficiary Nickname</label>
            <input name="nickname" maxlength="60"
                   placeholder="Example: Friend">

            <button type="submit">＋ Add Beneficiary</button>
        </form>
    </div>

    <div class="card">
        <h2>Saved Beneficiaries</h2>

        {% if beneficiary_list %}
        <div style="overflow-x:auto">
        <table>
            <tr>
                <th>Nickname</th>
                <th>Account Number</th>
            </tr>

            {% for item in beneficiary_list %}
            <tr>
                <td>{{ item.nickname }}</td>
                <td>{{ item.beneficiary_account }}</td>
            </tr>
            {% endfor %}
        </table>
        </div>
        {% else %}
        <p class="muted">No beneficiaries added yet.</p>
        {% endif %}
    </div>
    """

    return render_page(content, beneficiary_list=beneficiary_list)


# ==========================================================
# MONEY TRANSFER WITH DEMO OTP
# ==========================================================

@app.route("/transfer", methods=["GET", "POST"])
@login_required
def transfer():

    account = get_user_account(session["user_id"])

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT beneficiary_account, nickname
            FROM beneficiaries
            WHERE user_id = %s
            ORDER BY nickname
        """, (session["user_id"],))

        beneficiary_list = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    if request.method == "POST":

        receiver_account = request.form.get(
            "receiver_account", ""
        ).strip()

        amount = parse_amount(request.form.get("amount", ""))

        otp = request.form.get("otp", "").strip()
        description = request.form.get("description", "").strip()

        if not receiver_account:
            flash("Please select a beneficiary.", "error")
            return redirect(url_for("transfer"))

        if not amount:
            flash("Enter a valid transfer amount.", "error")
            return redirect(url_for("transfer"))

        if len(description) > 255:
            flash("Description must not exceed 255 characters.", "error")
            return redirect(url_for("transfer"))

        if receiver_account == account["account_number"]:
            flash("You cannot transfer money to yourself.", "error")
            return redirect(url_for("transfer"))

        if not re.fullmatch(r"[0-9]{6}", otp):
            flash("OTP must contain exactly 6 digits.", "error")
            return redirect(url_for("transfer"))

        if otp != DEMO_OTP:
            flash("Invalid OTP. Use the demonstration OTP 123456.", "error")
            return redirect(url_for("transfer"))

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute("""
                SELECT beneficiary_account
                FROM beneficiaries
                WHERE user_id = %s
                  AND beneficiary_account = %s
            """, (session["user_id"], receiver_account))

            if not cursor.fetchone():
                connection.rollback()
                flash("Please add this beneficiary first.", "error")
                return redirect(url_for("transfer"))

            cursor.execute("""
                SELECT account_number, balance
                FROM accounts
                WHERE account_number IN (%s, %s)
                ORDER BY account_number
                FOR UPDATE
            """, (
                account["account_number"],
                receiver_account
            ))

            locked_accounts = {
                row["account_number"]: row["balance"]
                for row in cursor.fetchall()
            }

            if len(locked_accounts) != 2:
                connection.rollback()
                flash("Sender or receiver account was not found.", "error")
                return redirect(url_for("transfer"))

            sender_balance = locked_accounts[
                account["account_number"]
            ]

            if sender_balance < amount:
                connection.rollback()
                flash("Insufficient account balance.", "error")
                return redirect(url_for("transfer"))

            cursor.execute("""
                UPDATE accounts
                SET balance = balance - %s
                WHERE account_number = %s
            """, (
                amount,
                account["account_number"]
            ))

            cursor.execute("""
                UPDATE accounts
                SET balance = balance + %s
                WHERE account_number = %s
            """, (
                amount,
                receiver_account
            ))

            reference = new_reference()

            cursor.execute("""
                INSERT INTO transactions (
                    reference_number,
                    sender_account,
                    receiver_account,
                    amount,
                    transaction_type,
                    description,
                    status
                )
                VALUES (%s, %s, %s, %s, %s, %s, 'SUCCESS')
            """, (
                reference,
                account["account_number"],
                receiver_account,
                amount,
                "Transfer",
                description or "Money transfer"
            ))

            connection.commit()

            flash("Money transferred successfully!", "success")
            return redirect(url_for(
                "receipt",
                reference=reference
            ))

        except Error as error:
            connection.rollback()
            print("Transfer error:", error)
            flash("Transfer failed. Please try again.", "error")

        finally:
            cursor.close()
            connection.close()

        return redirect(url_for("transfer"))

    content = """
    <div class="card auth">
        <h1>Transfer Money</h1>
        <p class="muted">
            Send money to one of your saved beneficiaries.
        </p>

        <div class="stat">
            <div class="stat-label">Available Balance</div>
            <div class="amount">
                ₹{{ "%.2f"|format(account.balance|float) }}
            </div>
        </div>

        {% if beneficiary_list %}
        <form method="POST">

            <label>Recipient Account</label>
            <select name="receiver_account" required>
                <option value="">Select beneficiary</option>

                {% for item in beneficiary_list %}
                <option value="{{ item.beneficiary_account }}">
                    {{ item.nickname }} —
                    {{ item.beneficiary_account }}
                </option>
                {% endfor %}
            </select>

            <label>Transfer Amount (₹)</label>
            <input type="number" name="amount"
                   min="0.01" max="9999999999999.99"
                   step="0.01" required>

            <label>Description</label>
            <input name="description" maxlength="255"
                   placeholder="Payment purpose">

            <div class="otp-box">
                <h2>Security Verification</h2>
                <p class="muted">
                    Enter the 6-digit demonstration OTP
                    to authorize this transaction.
                </p>

                <label>One-Time Password</label>
                <input class="otp-input"
                       type="password"
                       name="otp"
                       inputmode="numeric"
                       pattern="[0-9]{6}"
                       maxlength="6"
                       placeholder="••••••"
                       autocomplete="one-time-code"
                       required>

                <p class="muted">
                    Demo OTP: <strong>123456</strong>
                    <br>This project does not send real OTP messages.
                </p>
            </div>

            <button type="submit">Verify OTP & Transfer</button>
        </form>

        {% else %}
        <p class="muted">
            You haven't added any beneficiaries yet.
        </p>

        <a class="btn" href="{{ url_for('beneficiaries') }}">
            Add Beneficiary
        </a>
        {% endif %}
    </div>
    """

    return render_page(
        content,
        account=account,
        beneficiary_list=beneficiary_list
    )


# ==========================================================
# ACCOUNT PROFILE
# ==========================================================

@app.route("/profile")
@login_required
def profile():

    account = get_user_account(session["user_id"])

    if not account:
        flash("Account profile not found.", "error")
        return redirect(url_for("dashboard"))

    content = """
    <div class="card">
        <h1>Account Profile</h1>
        <p class="muted">
            Your personal and banking information.
        </p>

        <div class="grid">
            <div class="stat">
                <div class="stat-label">Account Balance</div>
                <div class="amount">
                    ₹{{ "%.2f"|format(account.balance|float) }}
                </div>
            </div>

            <div class="stat">
                <div class="stat-label">Account Type</div>
                <div class="amount" style="font-size:22px">
                    {{ account.account_type }}
                </div>
            </div>
        </div>

        <h2>Personal Information</h2>

        <div class="profile-row">
            <div class="profile-label">Full Name</div>
            <div class="profile-value">{{ account.full_name }}</div>
        </div>

        <div class="profile-row">
            <div class="profile-label">Username</div>
            <div class="profile-value">{{ account.username }}</div>
        </div>

        <div class="profile-row">
            <div class="profile-label">Email Address</div>
            <div class="profile-value">{{ account.email }}</div>
        </div>

        <div class="profile-row">
            <div class="profile-label">Phone Number</div>
            <div class="profile-value">{{ account.phone }}</div>
        </div>

        <h2 style="margin-top:30px">Bank Account Information</h2>

        <div class="profile-row">
            <div class="profile-label">Account Number</div>
            <div class="profile-value">{{ account.account_number }}</div>
        </div>

        <div class="profile-row">
            <div class="profile-label">Account Type</div>
            <div class="profile-value">{{ account.account_type }}</div>
        </div>

        <div class="profile-row">
            <div class="profile-label">Account Created</div>
            <div class="profile-value">{{ account.account_created_at }}</div>
        </div>

        <div class="profile-row">
            <div class="profile-label">Account Status</div>
            <div class="profile-value">
                <span class="badge">ACTIVE</span>
            </div>
        </div>
    </div>
    """

    return render_page(content, account=account)


# ==========================================================
# TRANSACTION HISTORY
# ==========================================================

@app.route("/history")
@login_required
def history():

    account = get_user_account(session["user_id"])

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                reference_number,
                sender_account,
                receiver_account,
                amount,
                transaction_type,
                description,
                transaction_date,
                status
            FROM transactions
            WHERE sender_account = %s OR receiver_account = %s
            ORDER BY transaction_date DESC
        """, (
            account["account_number"],
            account["account_number"]
        ))

        transactions = cursor.fetchall()

    finally:
        cursor.close()
        connection.close()

    content = """
    <div class="card">
        <h1>Transaction History</h1>
        <p class="muted">
            View your deposits, withdrawals and money transfers.
        </p>

        {% if transactions %}
        <div style="overflow-x:auto">
        <table>
            <tr>
                <th>Reference</th>
                <th>Type</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Status</th>
                <th>Receipt</th>
            </tr>

            {% for item in transactions %}
            <tr>
                <td>{{ item.reference_number }}</td>

                <td>
                    {% if item.transaction_type == 'Deposit' %}
                        Deposit
                    {% elif item.transaction_type == 'Withdrawal' %}
                        Withdrawal
                    {% elif item.transaction_type == 'Transfer' %}
                        {% if item.sender_account == account_number %}
                            Sent
                        {% else %}
                            Received
                        {% endif %}
                    {% else %}
                        {{ item.transaction_type }}
                    {% endif %}
                </td>

                <td>
                    ₹{{ "%.2f"|format(item.amount|float) }}
                </td>

                <td>{{ item.transaction_date }}</td>

                <td>
                    <span class="badge">{{ item.status }}</span>
                </td>

                <td>
                    <a href="{{ url_for('receipt',
                       reference=item.reference_number) }}">
                       View
                    </a>
                </td>
            </tr>
            {% endfor %}
        </table>
        </div>
        {% else %}
        <p class="muted">No transactions found.</p>
        {% endif %}
    </div>
    """

    return render_page(
        content,
        transactions=transactions,
        account_number=account["account_number"]
    )


# ==========================================================
# TRANSACTION RECEIPT
# ==========================================================

@app.route("/receipt/<reference>")
@login_required
def receipt(reference):

    account = get_user_account(session["user_id"])

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT
                reference_number,
                sender_account,
                receiver_account,
                amount,
                transaction_type,
                description,
                transaction_date,
                status
            FROM transactions
            WHERE reference_number = %s
              AND (
                    sender_account = %s
                    OR receiver_account = %s
              )
        """, (
            reference,
            account["account_number"],
            account["account_number"]
        ))

        transaction = cursor.fetchone()

    finally:
        cursor.close()
        connection.close()

    if not transaction:
        flash("Transaction receipt not found.", "error")
        return redirect(url_for("history"))

    content = """
    <div class="card receipt">

        <div class="receipt-header">
            <h1>SecureBank</h1>
            <p class="muted">Transaction Receipt</p>
            <span class="badge">{{ transaction.status }}</span>
        </div>

        <div style="text-align:center; margin-bottom:25px">
            <div class="muted">Transaction Amount</div>
            <div class="amount">
                ₹{{ "%.2f"|format(transaction.amount|float) }}
            </div>
        </div>

        <div class="receipt-row">
            <span>Reference Number</span>
            <span>{{ transaction.reference_number }}</span>
        </div>

        <div class="receipt-row">
            <span>Transaction Type</span>
            <span>{{ transaction.transaction_type }}</span>
        </div>

        <div class="receipt-row">
            <span>From Account</span>
            <span>{{ transaction.sender_account }}</span>
        </div>

        <div class="receipt-row">
            <span>To Account</span>
            <span>{{ transaction.receiver_account }}</span>
        </div>

        <div class="receipt-row">
            <span>Description</span>
            <span>{{ transaction.description }}</span>
        </div>

        <div class="receipt-row">
            <span>Date & Time</span>
            <span>{{ transaction.transaction_date }}</span>
        </div>

        <div class="receipt-row">
            <span>Transaction Status</span>
            <span class="positive">{{ transaction.status }}</span>
        </div>

        <div class="receipt-row">
            <span>Account Holder</span>
            <span>{{ account.full_name }}</span>
        </div>

        <div class="receipt-row">
            <span>Your Account</span>
            <span>{{ account.account_number }}</span>
        </div>

        <div class="no-print actions" style="margin-top:25px">
            <button onclick="window.print()">Print Receipt</button>

            <a class="btn btn-secondary"
               href="{{ url_for('history') }}">
               Back to History
            </a>
        </div>

        <p class="muted" style="text-align:center; margin-top:25px">
            Thank you for using SecureBank.
            <br>Computer-generated educational demo receipt.
        </p>
    </div>
    """

    return render_page(
        content,
        transaction=transaction,
        account=account
    )


# ==========================================================
# START APPLICATION
# ==========================================================

if __name__ == "__main__":
    create_tables()

    print("\n====================================")
    print("Starting SecureBank Banking System")
    print("====================================")
    print("Open: http://127.0.0.1:5000")
    print("Demo OTP: 123456")
    print("Educational demonstration only.")

    app.run(debug=True)
