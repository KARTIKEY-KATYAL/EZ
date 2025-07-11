import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from decouple import config
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)

EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USER = config('EMAIL_USER')
EMAIL_PASSWORD = config('EMAIL_PASSWORD')
EMAIL_FROM = config('EMAIL_FROM')

async def send_verification_email(email: str, username: str, verification_token: str):
    """Send verification email to user"""
    try:
        # Create verification URL
        verification_url = f"http://localhost:8000/verify-email?token={verification_token}"
        
        # Email template
        email_template = """
        <html>
        <body>
            <h2>Welcome to Secure File Sharing System</h2>
            <p>Hello {{ username }},</p>
            <p>Thank you for signing up! Please click the link below to verify your email address:</p>
            <p><a href="{{ verification_url }}">Verify Email</a></p>
            <p>If you didn't sign up for this account, please ignore this email.</p>
            <p>Best regards,<br>File Sharing Team</p>
        </body>
        </html>
        """
        
        template = Template(email_template)
        html_content = template.render(username=username, verification_url=verification_url)
        
        # Create message
        message = MIMEMultipart("alternative")
        message["Subject"] = "Verify Your Email - Secure File Sharing"
        message["From"] = EMAIL_FROM
        message["To"] = email
        
        # Add HTML content
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # Send email
        await aiosmtplib.send(
            message,
            hostname=EMAIL_HOST,
            port=EMAIL_PORT,
            start_tls=True,
            username=EMAIL_USER,
            password=EMAIL_PASSWORD,
        )
        
        logger.info(f"Verification email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        return False
