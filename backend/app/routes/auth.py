from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, model_validator
from sqlalchemy.orm import Session
import bcrypt
from .. import models, schemas
from ..database import get_db
from typing import Optional, Any
import traceback
from datetime import datetime, timezone

router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)

# Password hashing



def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


class UserLogin(BaseModel):
    """Schema for login request"""
    email: str
    password: str
    
    @model_validator(mode='before')
    @classmethod
    def validate_email(cls, data: Any) -> Any:
        """Validate email format"""
        if not isinstance(data, dict):
            return data
        
        email = data.get('email', '')
        if not email or '@' not in email:
            raise ValueError('รูปแบบอีเมลไม่ถูกต้อง')
        
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError('รูปแบบอีเมลไม่ถูกต้อง')
        
        # Normalize email
        data['email'] = email.lower()
        
        return data


class UserResponse(schemas.User):
    """Schema for user response - includes user data"""
    pass


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    
    - **username**: Unique username (3-100 characters)
    - **email**: Valid email address
    - **password**: Password (minimum 6 characters)
    """
    from email_validator import validate_email, EmailNotValidError
    
    try:
        # Validate email format and domain
        try:
            validation = validate_email(user.email, check_deliverability=True)
            normalized_email = validation.normalized
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"อีเมลไม่ถูกต้อง: {str(e)}"
            )
        
        # Check if user already exists
        existing_user = db.query(models.User).filter(
            (models.User.username == user.username) | (models.User.email == normalized_email)
        ).first()
        
        if existing_user:
            if existing_user.email == normalized_email:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="อีเมลนี้ถูกใช้งานแล้ว"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ชื่อผู้ใช้นี้ถูกใช้งานแล้ว"
                )
        
        # Hash password
        hashed_password = hash_password(user.password)
        
        # Create new user
        db_user = models.User(
            username=user.username,
            email=normalized_email,
            password_hash=hashed_password,
            user_role="User",
            created_at=datetime.now(timezone.utc)
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error during registration: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=UserResponse)
def login(user_login: UserLogin, db: Session = Depends(get_db)):
    """
    Login a user with email and password.
    
    - **email**: User's email
    - **password**: User's password
    """
    # Find user by email
    db_user = db.query(models.User).filter(models.User.email == user_login.email).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="ไม่พบอีเมลของผู้ใช้งาน"
        )
    
    # Verify password
    if not verify_password(user_login.password, db_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="รหัสผ่านไม่ถูกต้อง"
        )
    
    return db_user


@router.get("/user/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get user by ID.
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    
    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return db_user


# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request"""
    email: EmailStr


class VerifyResetCodeRequest(BaseModel):
    """Schema for verify reset code request"""
    email: EmailStr
    code: str


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request"""
    token: str
    new_password: str


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request password reset - sends verification code to email
    
    - **email**: User's email address
    """
    from ..services.email_service import EmailService
    from email_validator import validate_email, EmailNotValidError
    
    try:
        # Validate email format and domain
        try:
            validation = validate_email(request.email, check_deliverability=True)
            email = validation.normalized
        except EmailNotValidError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid email: {str(e)}"
            )
        
        # Find user by email
        user = db.query(models.User).filter(models.User.email == email).first()
        
        # Don't reveal if email exists (security)
        if not user:
            # Still return success to prevent email enumeration
            return {
                "success": True,
                "message": "หากอีเมลนี้มีอยู่ในระบบ คุณจะได้รับรหัสยืนยันทางอีเมล"
            }
        
        # Generate reset code and token
        reset_code = EmailService.generate_reset_code()
        reset_token = EmailService.generate_reset_token()
        expires_at = EmailService.get_expiry_time()
        
        # Delete old unused tokens for this user
        db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.user_id == user.id,
            models.PasswordResetToken.used == False
        ).delete()
        
        # Create new reset token
        db_token = models.PasswordResetToken(
            user_id=user.id,
            token=reset_token,
            code=reset_code,
            expires_at=expires_at,
            used=False
        )
        db.add(db_token)
        db.commit()
        
        # Send email with reset code
        email_sent = await EmailService.send_password_reset_email(
            to_email=user.email,
            reset_code=reset_code,
            username=user.username
        )
        
        if not email_sent:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
        
        return {
            "success": True,
            "message": "รหัสยืนยันถูกส่งไปยังอีเมลของคุณแล้ว"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in forgot_password: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process request"
        )


@router.post("/verify-reset-code")
def verify_reset_code(request: VerifyResetCodeRequest, db: Session = Depends(get_db)):
    """
    Verify reset code and return token for password reset
    
    - **email**: User's email
    - **code**: 6-digit verification code
    """
    try:
        # Find user
        user = db.query(models.User).filter(models.User.email == request.email).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid code"
            )
        
        # Find valid token
        reset_token = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.user_id == user.id,
            models.PasswordResetToken.code == request.code,
            models.PasswordResetToken.used == False,
            models.PasswordResetToken.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="รหัสยืนยันไม่ถูกต้องหรือหมดอายุแล้ว"
            )
        
        return {
            "success": True,
            "token": reset_token.token,
            "message": "รหัสยืนยันถูกต้อง"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in verify_reset_code: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify code"
        )


@router.post("/reset-password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using verified token
    
    - **token**: Reset token from verify-reset-code
    - **new_password**: New password (minimum 6 characters)
    """
    try:
        # Validate password length
        if len(request.new_password) < 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="รหัสผ่านต้องมีอย่างน้อย 6 ตัวอักษร"
            )
        
        # Find valid token
        reset_token = db.query(models.PasswordResetToken).filter(
            models.PasswordResetToken.token == request.token,
            models.PasswordResetToken.used == False,
            models.PasswordResetToken.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )
        
        # Get user
        user = db.query(models.User).filter(models.User.id == reset_token.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Update password
        user.password_hash = hash_password(request.new_password)
        
        # Mark token as used
        reset_token.used = True
        
        db.commit()
        
        return {
            "success": True,
            "message": "รีเซ็ตรหัสผ่านสำเร็จ"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in reset_password: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )
