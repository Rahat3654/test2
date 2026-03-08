import os
import random
import resend
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse

# Initialize Resend API from environment variable
# Railway will provide this via your Dashboard settings
resend.api_key = os.getenv("RESEND_API_KEY")

app = FastAPI()

html_form = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>PentaRideX Registration</title>
    <style>
        body {{ font-family: Arial; display:flex; justify-content:center; align-items:center; height:100vh; background:#f4f4f4; margin:0; }}
        .container {{ background:white; padding:30px; border-radius:10px; box-shadow:0 0 10px rgba(0,0,0,0.1); width:300px; text-align:center; }}
        input[type="email"] {{ width:90%; padding:10px; margin:10px 0; border-radius:5px; border:1px solid #ccc; }}
        button {{ width:100%; padding:10px; background:#2980b9; color:white; border:none; border-radius:5px; cursor:pointer; }}
        button:hover {{ background:#3498db; }}
        .otp-sent {{ color:green; margin-top:10px; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>PentaRideX</h2>
        <form method="post">
            <input type="email" name="email" placeholder="Enter your email" required>
            <button type="submit">Send OTP</button>
        </form>
        {otp_message}
    </div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_form():
    return HTMLResponse(html_form.format(otp_message=""))

@app.post("/", response_class=HTMLResponse)
async def send_otp(email: str = Form(...)):
    otp = random.randint(100000, 999999)

    try:
        resend.Emails.send({
            "from": "verify@pentaridex.xyz",
            "to": email,
            "subject": "Your PentaRideX OTP",
            "html": f"<p>Your OTP is: <strong>{otp}</strong></p>"
        })
        message = f'<div class="otp-sent">OTP sent successfully to {email}</div>'
    except Exception as e:
        message = f'<div style="color:red; margin-top:10px;">Error: {str(e)}</div>'

    return HTMLResponse(html_form.format(otp_message=message))

if __name__ == "__main__":
    import uvicorn
    # Railway sets the PORT environment variable automatically
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
