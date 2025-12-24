"""
Email Service for sending OTP verification codes
Uses FastAPI-Mail with Gmail SMTP
"""

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()


# Email configuration from environment variables
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", "your_email@gmail.com"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", "your_app_password"),
    MAIL_FROM=os.getenv("MAIL_FROM", "your_email@gmail.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.gmail.com"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "CipherDocs"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "true").lower() == "true",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "false").lower() == "true",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Initialize FastMail
fm = FastMail(conf)


async def send_verification_email(email: EmailStr, otp_code: str, user_name: str = "User") -> bool:
    """
    Send OTP verification email to user
    
    Args:
        email: User's email address
        otp_code: 6-digit OTP code
        user_name: User's name (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #4F46E5;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .otp-box {{
                    background-color: #f0f0f0;
                    border: 2px dashed #4F46E5;
                    padding: 20px;
                    text-align: center;
                    font-size: 32px;
                    font-weight: bold;
                    letter-spacing: 8px;
                    margin: 20px 0;
                    color: #4F46E5;
                }}
                .footer {{
                    text-align: center;
                    color: #666;
                    font-size: 12px;
                    margin-top: 20px;
                }}
                .warning {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 10px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 Email Verification</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>Thank you for signing up with <strong>CipherDocs</strong>!</p>
                    
                    <p>To complete your registration, please verify your email address by entering the following verification code:</p>
                    
                    <div class="otp-box">
                        {otp_code}
                    </div>
                    
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    
                    <div class="warning">
                        <strong>⚠️ Security Notice:</strong> Never share this code with anyone. CipherDocs will never ask for your verification code via email or phone.
                    </div>
                    
                    <p>If you didn't create an account with CipherDocs, please ignore this email.</p>
                    
                    <p>Best regards,<br>
                    <strong>The CipherDocs Team</strong></p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                    <p>&copy; 2025 CipherDocs. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version for email clients that don't support HTML
        text_content = f"""
        Hello {user_name},
        
        Thank you for signing up with CipherDocs!
        
        To complete your registration, please verify your email address by entering the following verification code:
        
        {otp_code}
        
        This code will expire in 10 minutes.
        
        SECURITY NOTICE: Never share this code with anyone. CipherDocs will never ask for your verification code via email or phone.
        
        If you didn't create an account with CipherDocs, please ignore this email.
        
        Best regards,
        The CipherDocs Team
        """
        
        message = MessageSchema(
            subject="Verify Your Email - CipherDocs",
            recipients=[email],
            body=text_content,
            html=html_content,
            subtype=MessageType.html
        )
        
        await fm.send_message(message)
        return True
        
    except Exception as e:
        print(f"Error sending email to {email}: {str(e)}")
        return False


async def send_password_reset_email(email: EmailStr, reset_token: str, user_name: str = "User") -> bool:
    """
    Send password reset email (for future implementation)
    
    Args:
        email: User's email address
        reset_token: Password reset token
        user_name: User's name (optional)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f9f9f9;
                }}
                .header {{
                    background-color: #EF4444;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: white;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #EF4444;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔑 Password Reset</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>We received a request to reset your password. Click the button below to reset it:</p>
                    
                    <p style="text-align: center;">
                        <a href="http://localhost:3000/reset-password?token={reset_token}" class="button">Reset Password</a>
                    </p>
                    
                    <p>This link will expire in 1 hour.</p>
                    
                    <p>If you didn't request a password reset, please ignore this email.</p>
                    
                    <p>Best regards,<br>
                    <strong>The CipherDocs Team</strong></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        message = MessageSchema(
            subject="Reset Your Password - CipherDocs",
            recipients=[email],
            body=f"Reset your password: http://localhost:3000/reset-password?token={reset_token}",
            html=html_content,
            subtype=MessageType.html
        )
        
        await fm.send_message(message)
        return True
        
    except Exception as e:
        print(f"Error sending password reset email to {email}: {str(e)}")
        return False
