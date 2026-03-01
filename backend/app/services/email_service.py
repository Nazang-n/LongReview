"""
Email service for sending password reset emails
Uses Gmail SMTP with async support
"""
import aiosmtplib
import secrets
import string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional
from app.config.settings import settings


class EmailService:
    """Service for sending emails via Gmail SMTP"""
    
    @staticmethod
    def generate_reset_code() -> str:
        """Generate a 6-digit verification code"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    def generate_reset_token() -> str:
        """Generate a secure random token for password reset"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    async def send_password_reset_email(to_email: str, reset_code: str, username: str) -> bool:
        """
        Send password reset email with verification code
        
        Args:
            to_email: Recipient email address
            reset_code: 6-digit verification code
            username: User's username
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.GMAIL_USER}>"
            message["To"] = to_email
            message["Subject"] = "รหัสยืนยันการรีเซ็ตรหัสผ่าน - LongReview"
            
            # HTML email body
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: linear-gradient(135deg, #9333ea 0%, #7e22ce 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                    .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
                    .code-box {{ background: white; border: 2px solid #9333ea; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
                    .code {{ font-size: 32px; font-weight: bold; color: #7e22ce; letter-spacing: 8px; }}
                    .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
                    .warning {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎮 LongReview</h1>
                        <p>รีเซ็ตรหัสผ่านของคุณ</p>
                    </div>
                    <div class="content">
                        <p>สวัสดี <strong>{username}</strong>,</p>
                        <p>คุณได้ขอรีเซ็ตรหัสผ่านสำหรับบัญชี LongReview ของคุณ</p>
                        
                        <div class="code-box">
                            <p style="margin: 0; color: #666; font-size: 14px;">รหัสยืนยันของคุณคือ:</p>
                            <div class="code">{reset_code}</div>
                            <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">รหัสนี้จะหมดอายุใน {settings.RESET_CODE_EXPIRY_MINUTES} นาที</p>
                        </div>
                        
                        <p>กรุณากรอกรหัสนี้ในหน้ารีเซ็ตรหัสผ่านเพื่อดำเนินการต่อ</p>
                        
                        <div class="warning">
                            <strong>⚠️ คำเตือน:</strong> หากคุณไม่ได้ขอรีเซ็ตรหัสผ่าน กรุณาเพิกเฉยอีเมลนี้ บัญชีของคุณยังคงปลอดภัย
                        </div>
                        
                        <p>ขอบคุณที่ใช้บริการ LongReview!</p>
                    </div>
                    <div class="footer">
                        <p>© 2026 LongReview - Your Gaming Review Platform</p>
                        <p>อีเมลนี้ถูกส่งอัตโนมัติ กรุณาอย่าตอบกลับ</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML body
            html_part = MIMEText(html_body, "html", "utf-8")
            message.attach(html_part)
            
            # Remove spaces from app password
            app_password = settings.GMAIL_APP_PASSWORD.replace(" ", "") if settings.GMAIL_APP_PASSWORD else ""
            
            # Send email via Gmail SMTP
            await aiosmtplib.send(
                message,
                hostname="smtp.gmail.com",
                port=465,
                use_tls=True,
                username=settings.GMAIL_USER,
                password=app_password,
            )
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return False
    
    @staticmethod
    def get_expiry_time() -> datetime:
        """Get expiry time for reset code"""
        return datetime.utcnow() + timedelta(minutes=settings.RESET_CODE_EXPIRY_MINUTES)
