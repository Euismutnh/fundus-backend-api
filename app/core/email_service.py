import smtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, timezone
from typing import Optional
from jinja2 import Template
import os
from app.core.config import settings

class EmailService:
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.SENDER_EMAIL

    def generate_otp(self) -> str:
        """Generate 6-digit OTP"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))

    def get_otp_expiry(self) -> datetime:
        """Get OTP expiry time (5 minutes from now)"""
        return datetime.now(timezone.utc) + timedelta(minutes=5)

    async def send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """Send email with HTML content"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.sender_email
            msg['To'] = to_email

            # Create HTML part
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False

    def render_otp_template(self, user_name: str, otp: str, purpose: str = "verification") -> str:
        """Render OTP email template"""
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>OTP Verification - DR Detection App</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }
                .container {
                    background-color: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .logo {
                    font-size: 24px;
                    font-weight: bold;
                    color: #2563eb;
                    margin-bottom: 10px;
                }
                .title {
                    font-size: 20px;
                    color: #1f2937;
                    margin-bottom: 20px;
                }
                .otp-box {
                    background-color: #f8fafc;
                    border: 2px dashed #2563eb;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                }
                .otp-code {
                    font-size: 32px;
                    font-weight: bold;
                    color: #2563eb;
                    letter-spacing: 8px;
                    margin: 10px 0;
                }
                .warning {
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔬 DR Detection App</div>
                    <h1 class="title">OTP {{ purpose.title() }}</h1>
                </div>
                
                <p>Hello <strong>{{ user_name }}</strong>,</p>
                
                <p>You have requested an OTP for {{ purpose }}. Please use the following code to complete your request:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #6b7280;">Your OTP Code:</p>
                    <div class="otp-code">{{ otp }}</div>
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">Valid for 5 minutes</p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Security Notice:</strong>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>This OTP is valid for 5 minutes only</li>
                        <li>Do not share this code with anyone</li>
                        <li>If you didn't request this, please ignore this email</li>
                    </ul>
                </div>
                
                <p>If you have any questions or need assistance, please contact our support team.</p>
                
                <div class="footer">
                    <p>Best regards,<br>DR Detection App Team</p>
                    <p style="margin-top: 15px;">
                        This is an automated email. Please do not reply to this message.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(user_name=user_name, otp=otp, purpose=purpose)

    def render_forgot_password_template(self, user_name: str, otp: str) -> str:
        """Render forgot password email template"""
        template_str = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - DR Detection App</title>
            <style>
                body {
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }
                .container {
                    background-color: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                .logo {
                    font-size: 24px;
                    font-weight: bold;
                    color: #dc2626;
                    margin-bottom: 10px;
                }
                .title {
                    font-size: 20px;
                    color: #1f2937;
                    margin-bottom: 20px;
                }
                .otp-box {
                    background-color: #fef2f2;
                    border: 2px dashed #dc2626;
                    border-radius: 8px;
                    padding: 20px;
                    text-align: center;
                    margin: 30px 0;
                }
                .otp-code {
                    font-size: 32px;
                    font-weight: bold;
                    color: #dc2626;
                    letter-spacing: 8px;
                    margin: 10px 0;
                }
                .steps {
                    background-color: #f0f9ff;
                    border-left: 4px solid #0ea5e9;
                    padding: 20px;
                    margin: 20px 0;
                    border-radius: 4px;
                }
                .warning {
                    background-color: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 4px;
                }
                .footer {
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #e5e7eb;
                    color: #6b7280;
                    font-size: 14px;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🔒 DR Detection App</div>
                    <h1 class="title">Password Reset Request</h1>
                </div>
                
                <p>Hello <strong>{{ user_name }}</strong>,</p>
                
                <p>We received a request to reset your password for your DR Detection App account. Use the OTP code below to proceed with resetting your password:</p>
                
                <div class="otp-box">
                    <p style="margin: 0; color: #6b7280;">Password Reset OTP:</p>
                    <div class="otp-code">{{ otp }}</div>
                    <p style="margin: 0; color: #6b7280; font-size: 14px;">Valid for 5 minutes</p>
                </div>
                
                <div class="steps">
                    <strong>📋 Next Steps:</strong>
                    <ol style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>Enter this OTP code in the app</li>
                        <li>Create your new password</li>
                        <li>Confirm your new password</li>
                        <li>Login with your new credentials</li>
                    </ol>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Important Security Information:</strong>
                    <ul style="margin: 10px 0 0 0; padding-left: 20px;">
                        <li>This OTP expires in 5 minutes</li>
                        <li>Never share this code with anyone</li>
                        <li>If you didn't request this reset, please secure your account immediately</li>
                        <li>Contact support if you suspect unauthorized access</li>
                    </ul>
                </div>
                
                <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
                
                <div class="footer">
                    <p>Best regards,<br>DR Detection App Security Team</p>
                    <p style="margin-top: 15px;">
                        This is an automated security email. Please do not reply to this message.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        template = Template(template_str)
        return template.render(user_name=user_name, otp=otp)

    async def send_otp_email(self, to_email: str, user_name: str, otp: str, purpose: str = "account verification") -> bool:
        """Send OTP verification email"""
        subject = f"DR Detection App - OTP {purpose.title()}"
        html_content = self.render_otp_template(user_name, otp, purpose)
        return await self.send_email(to_email, subject, html_content)

    async def send_forgot_password_email(self, to_email: str, user_name: str, otp: str) -> bool:
        """Send forgot password email"""
        subject = "DR Detection App - Password Reset Request"
        html_content = self.render_forgot_password_template(user_name, otp)
        return await self.send_email(to_email, subject, html_content)

# Create global email service instance
email_service = EmailService()
