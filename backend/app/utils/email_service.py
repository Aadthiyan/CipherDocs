"""
Email Service for sending OTP verification codes
Uses Brevo (Sendinblue) API for reliable email delivery
"""

import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from pydantic import EmailStr
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)

# Configure Brevo API
configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = os.getenv("BREVO_API_KEY", "")

# Create API instance
api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))


async def send_verification_email(email: EmailStr, otp_code: str, user_name: str = "User") -> bool:
    """
    Send OTP verification email to user using Brevo API
    
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
                    <h1>🔒 Email Verification</h1>
                </div>
                <div class="content">
                    <p>Hello {user_name},</p>
                    
                    <p>Thank you for signing up with CipherDocs!</p>
                    
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
        
        # Create email using Brevo API
        sender = {"name": os.getenv("MAIL_FROM_NAME", "CipherDocs"), "email": os.getenv("MAIL_FROM", "aadhiks9595@gmail.com")}
        to = [{"email": email, "name": user_name}]
        
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            sender=sender,
            subject="Verify Your Email - CipherDocs",
            html_content=html_content
        )
        
        # Send the email
        api_instance.send_transac_email(send_smtp_email)
        logger.info(f"Verification email sent successfully to {email}")
        return True
        
    except ApiException as e:
        logger.error(f"Brevo API error sending email to {email}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error sending email to {email}: {str(e)}")
        return False
