import smtplib
from email.message import EmailMessage
from fpdf import FPDF
from dotenv import load_dotenv
import datetime
import os

# --- SECURE CONFIGURATION ---
# Credentials are loaded from the .env file — NEVER hardcoded.
load_dotenv()

SENDER_EMAIL = os.getenv("EMAIL_USER")
RECEIVER_EMAIL = os.getenv("EMAIL_USER")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
APP_PASSWORD = os.getenv("EMAIL_PASS")

def _send_email(subject, body, to_email=RECEIVER_EMAIL):
    """
    PRIVATE HELPER: Handles the technical handshake with the Gmail server.
    Uses TLS (Transport Layer Security) to encrypt the connection.
    """
    try:
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = SENDER_EMAIL
        msg['To'] = to_email
        msg.set_content(body)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls() # Secure the connection
            server.login(SENDER_EMAIL, APP_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

# --- EMAIL TEMPLATES ---

def send_otp(email, otp):
    """
    AUTH LOGIC: Sends a 4-digit code for account verification.
    This ensures the user owns the email address they registered with.
    """
    subject = "Crypto Portfolio Manager - Registration OTP"
    body = f"""
Dear User,

Welcome to the Crypto Portfolio Manager! 
Your registration OTP is: {otp}

Please enter this code in the application to complete your registration.

Best regards,
Crypto Admin Team
"""
    return _send_email(subject, body, to_email=email)

def send_risk_alert(email, coin, current_price, drop_pct):
    """
    AUTOMATED MONITORING: Triggered when an asset price drops below 
    the user's custom threshold set in 'Settings'.
    """
    subject = f"URGENT: Risk Alert for {coin.upper()}"
    body = f"""
Dear Investor,

Our automated risk engine has detected a significant volatility event in your portfolio.

Asset: {coin.upper()}
Current Price: ${current_price:.2f}
Observed Drop: {drop_pct:.2f}%

This exceeds your configured risk threshold. Please review your dashboard immediately.

Best regards,
Crypto Portfolio Manager Automated Risk Engine
"""
    return _send_email(subject, body, to_email=email)

# --- REPORT GENERATION ---

def generate_pdf_report(user_email, portfolio_data, pl_summary, ai_outlook, filepath):
    """
    DOCUMENT ENGINE: Uses the FPDF library to build a 'High-Grade' PDF report.
    This demonstrates the ability to export structured data into professional formats.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # 1. SETTING THE BRANDING
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Crypto Portfolio Manager', ln=True, align='C')
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, 'Investment Audit Report', ln=True, align='C')
    pdf.ln(5)
    
    # 2. AUDIT METADATA
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Investor: {user_email}", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Horizontal line for separation
    pdf.ln(5)
    
    # 3. FINANCIAL SUMMARY (Profit/Loss Analysis)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Financial Summary', ln=True)
    pdf.set_font('Arial', '', 11)
    for key, value in pl_summary.items():
        pdf.cell(0, 8, f"- {key}: {value}", ln=True)
    pdf.ln(5)
    
    # 4. TABULAR DATA (Current Holdings)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Current Holdings', ln=True)
    
    # Render Table Headers
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(45, 8, 'Asset', border=1, align='C')
    pdf.cell(45, 8, 'Quantity', border=1, align='C')
    pdf.cell(45, 8, 'Purchase Price', border=1, align='C')
    pdf.cell(45, 8, 'Live Price', border=1, align='C')
    pdf.ln()
    
    # Render Table Content dynamically from the portfolio database
    pdf.set_font('Arial', '', 10)
    for item in portfolio_data:
        name = str(item.get('name', item.get('coin_id'))).upper()
        qty = f"{item.get('quantity', 0):.4f}"
        purch = f"${item.get('purchase_price', 0):.2f}"
        live = f"${item.get('current_price', 0):.2f}"
        
        pdf.cell(45, 8, name, border=1)
        pdf.cell(45, 8, qty, border=1, align='R')
        pdf.cell(45, 8, purch, border=1, align='R')
        pdf.cell(45, 8, live, border=1, align='R')
        pdf.ln()
    pdf.ln(5)
    
    # 5. ML INSIGHTS (AI Strategy Section)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'AI Strategy Outlook (7-Day)', ln=True)
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 6, ai_outlook) # multi_cell handles long text wrapping
    
    # Final step: Save the file to the provided path
    try:
        pdf.output(filepath, 'F')
        return True
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False