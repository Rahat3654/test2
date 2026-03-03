import random
import smtplib
import os
import time
from email.message import EmailMessage
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse

load_dotenv()

app = FastAPI()

# In-memory OTP storage
otp_storage = {}

# --- Helper Functions ---

def generate_otp():
    return str(random.randint(100000, 999999))

def send_otp_email(to_email, otp):
    # Railway variables: Add these in the 'Variables' tab of your Railway project
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS")
    EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

    msg = EmailMessage()
    msg["Subject"] = "PentaRideX - OTP Verification Code"
    msg["From"] = f"PentaRideX <{EMAIL_ADDRESS}>"
    msg["To"] = to_email

    msg.set_content(f"""
Welcome to PentaRideX 🚴

Your One-Time Password (OTP) is: {otp}

This code is valid for 5 minutes.
Do not share this code with anyone.

— Team PentaRideX
""")

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

# --- CSS Styles (Reused in all pages) ---

HTML_STYLE = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f4f7f6; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
    .container { max-width: 400px; width: 90%; background: #fff; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }
    h1 { color: #2d3436; margin-bottom: 20px; font-size: 24px; }
    p { color: #636e72; font-size: 14px; }
    input { width: 100%; padding: 12px; margin: 15px 0; border-radius: 8px; border: 1px solid #dfe6e9; box-sizing: border-box; font-size: 16px; }
    button { width: 100%; padding: 12px; background: #00b894; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: 600; transition: background 0.3s; }
    button:hover { background: #00a887; }
    .status { margin: 15px 0; padding: 10px; border-radius: 6px; font-weight: 500; }
    .success { background: #e8f8f5; color: #00b894; }
    .error { background: #feeef0; color: #d63031; }
    .link { display: block; margin-top: 20px; color: #0984e3; text-decoration: none; font-size: 13px; }
</style>
"""

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def home():
    return f"""
    <html>
    <head><title>PentaRideX | Register</title>{HTML_STYLE}</head>
    <body>
        <div class="container">
            <h1>PentaRideX 🚴</h1>
            <p>Enter your email to receive an OTP</p>
            <form action="/register" method="post">
                <input type="email" name="email" placeholder="email@example.com" required>
                <button type="submit">Send Verification Code</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/register", response_class=HTMLResponse)
async def register(email: str = Form(...)):
    otp = generate_otp()
    otp_storage[email] = {
        "otp": otp,
        "expiry": time.time() + 300,
        "attempts": 0
    }
    
    try:
        send_otp_email(email, otp)
        status_msg = f'<div class="status success">Code sent to {email}</div>'
    except Exception as e:
        status_msg = f'<div class="status error">Failed to send email. Check your credentials.</div>'

    return f"""
    <html>
    <head><title>Verify OTP</title>{HTML_STYLE}</head>
    <body>
        <div class="container">
            <h1>Verification</h1>
            {status_msg}
            <form action="/verify" method="post">
                <input type="hidden" name="email" value="{email}">
                <input type="text" name="otp" placeholder="Enter 6-digit code" required>
                <button type="submit">Verify Account</button>
            </form>
            <a href="/" class="link">Change Email</a>
        </div>
    </body>
    </html>
    """

@app.post("/verify", response_class=HTMLResponse)
async def verify(email: str = Form(...), otp: str = Form(...)):
    if email not in otp_storage:
        result, css_class = "No active session. Please try again.", "error"
    else:
        data = otp_storage[email]
        if time.time() > data["expiry"]:
            result, css_class = "OTP expired. Request a new one.", "error"
            del otp_storage[email]
        elif otp == data["otp"]:
            result, css_class = "Verification Successful! ✅", "success"
            del otp_storage[email]
        else:
            data["attempts"] += 1
            remaining = 3 - data["attempts"]
            if remaining <= 0:
                result, css_class = "Too many failed attempts. Try again later.", "error"
                del otp_storage[email]
            else:
                result, css_class = f"Invalid OTP. {remaining} attempts left.", "error"

    return f"""
    <html>
    <head><title>Result</title>{HTML_STYLE}</head>
    <body>
        <div class="container">
            <h1>Status</h1>
            <div class="status {css_class}">{result}</div>
            <a href="/" class="link">Return to Home</a>
        </div>
    </body>
    </html>
    """
