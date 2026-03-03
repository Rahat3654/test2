# app.py
import random
import smtplib
import os
import time
from email.message import EmailMessage
from dotenv import load_dotenv
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse

# Load .env only in development (optional)
if os.getenv("ENVIRONMENT") != "production":
    load_dotenv()

app = FastAPI()

# In-memory OTP storage
otp_storage = {}

def generate_otp():
    return random.randint(100000, 999999)

def send_otp_email(to_email, otp):
    EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "pentaridex@gmail.com")  # CHANGE 1: Use env var
    EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")
    
    # CHANGE 2: Add error handling
    if not EMAIL_PASSWORD:
        print("ERROR: EMAIL_APP_PASSWORD not set in environment variables")
        raise ValueError("EMAIL_APP_PASSWORD environment variable is required")

    msg = EmailMessage()
    msg["Subject"] = "PentaRideX - OTP Verification Code"
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = to_email

    msg.set_content(f"""
Welcome to PentaRideX 🚴

Your One-Time Password (OTP) is: {otp}

This code is valid for 5 minutes.
Do not share this code with anyone.

— Team PentaRideX
""")

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
    except smtplib.SMTPAuthenticationError:
        print("ERROR: Gmail authentication failed. Check EMAIL_APP_PASSWORD")
        raise
    except Exception as e:
        print(f"ERROR: Failed to send email: {str(e)}")
        raise

def store_otp(email, otp):
    otp_storage[email] = {
        "otp": str(otp),
        "expiry": time.time() + 300,  # 5 min expiry
        "attempts": 0
    }

def verify_otp(email, user_input):
    if email not in otp_storage:
        return "No OTP found. Please request again."
    data = otp_storage[email]
    if time.time() > data["expiry"]:
        del otp_storage[email]
        return "OTP expired. Please request new one."
    if data["attempts"] >= 3:
        del otp_storage[email]
        return "Too many failed attempts. Request new OTP."
    if user_input == data["otp"]:
        del otp_storage[email]
        return "Verification successful ✅"
    else:
        data["attempts"] += 1
        return f"Invalid OTP ❌ ({3 - data['attempts']} attempts left)"

# ==================== ROUTES ====================

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>PentaRideX Registration</title>
    <style>
        body { font-family: Arial; background: #f0f0f0; }
        .container { max-width: 400px; margin: 100px auto; background: #fff; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2);}
        input, button { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc;}
        button { background: #28a745; color: white; border: none; cursor: pointer;}
        button:hover { background: #218838;}
    </style>
</head>
<body>
    <div class="container">
        <h1>PentaRideX Registration</h1>
        <form action="/register" method="post">
            <input type="email" name="email" placeholder="Enter your email" required>
            <button type="submit">Send OTP</button>
        </form>
    </div>
</body>
</html>
"""

@app.post("/register", response_class=HTMLResponse)
async def register(email: str = Form(...)):
    try:
        otp = generate_otp()
        send_otp_email(email, otp)
        store_otp(email, otp)
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>OTP Verification</title>
    <style>
        body {{ font-family: Arial; background: #f0f0f0; }}
        .container {{ max-width: 400px; margin: 100px auto; background: #fff; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2);}}
        input, button {{ width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc;}}
        button {{ background: #28a745; color: white; border: none; cursor: pointer;}}
        button:hover {{ background: #218838;}}
    </style>
</head>
<body>
    <div class="container">
        <h1>OTP Verification</h1>
        <p>OTP sent to your email: {email}</p>
        <form action="/verify" method="post">
            <input type="hidden" name="email" value="{email}">
            <input type="text" name="otp" placeholder="Enter OTP" required>
            <button type="submit">Verify</button>
        </form>
    </div>
</body>
</html>
"""
    except Exception as e:
        return f"""
<!DOCTYPE html>
<html>
<head>
    <title>Error</title>
    <style>
        body {{ font-family: Arial; background: #f0f0f0; }}
        .container {{ max-width: 400px; margin: 100px auto; background: #fff; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2);}}
        button {{ background: #dc3545; color: white; border: none; cursor: pointer; padding: 10px; border-radius: 5px;}}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Error</h1>
        <p>Failed to send OTP. Please try again.</p>
        <button onclick="window.history.back()">Go Back</button>
    </div>
</body>
</html>
"""

@app.post("/verify", response_class=HTMLResponse)
async def otp_verify(email: str = Form(...), otp: str = Form(...)):
    result = verify_otp(email, otp)
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>OTP Verification</title>
    <style>
        body {{ font-family: Arial; background: #f0f0f0; }}
        .container {{ max-width: 400px; margin: 100px auto; background: #fff; padding: 30px; border-radius: 10px; text-align: center; box-shadow: 0 2px 10px rgba(0,0,0,0.2);}}
        input, button {{ width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #ccc;}}
        button {{ background: #28a745; color: white; border: none; cursor: pointer;}}
        button:hover {{ background: #218838;}}
    </style>
</head>
<body>
    <div class="container">
        <h1>OTP Verification</h1>
        <p>{result}</p>
        <form action="/verify" method="post">
            <input type="hidden" name="email" value="{email}">
            <input type="text" name="otp" placeholder="Enter OTP" required>
            <button type="submit">Verify</button>
        </form>
    </div>
</body>
</html>
"""
