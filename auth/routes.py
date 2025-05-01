from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.users import UserCreate, UserLogin, UserResponse, PasswordUpdateRequest
from models.users import User
from database import get_db
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import pyotp
import qrcode
from fastapi.responses import StreamingResponse
import io
import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")

auth_router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Utility functions
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=60))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Register route
@auth_router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check if email or username already exists
        existing_user = db.query(User).filter(User.email == user.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed_password = hash_password(user.password)
        new_user = User(
            username=user.username,
            email=user.email,
            hashed_password=hashed_password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    except Exception as e:
        print("🔥 Registration Error:", e)
        raise HTTPException(status_code=500, detail="Registration failed")


# Login route
@auth_router.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.email == user.email).first()
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(user.password, db_user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        # ✅ Only require 2FA for admin users
        if db_user.is_admin and db_user.has_2fa:
            if not user.code:
                raise HTTPException(status_code=401, detail="2FA code required")
            totp = pyotp.TOTP(db_user.twofa_secret)
            if not totp.verify(user.code):
                raise HTTPException(status_code=403, detail="Invalid 2FA code")

        access_token = create_access_token(data={"sub": db_user.email})
        return {"access_token": access_token, "token_type": "bearer"}

    except Exception as e:
        print("🔥 Login error:", e)
        raise HTTPException(status_code=500, detail="Internal server error")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        print("❌ No user found for given email")
        raise credentials_exception
    return user



@auth_router.get("/protected")
def protected_route(current_user: User = Depends(get_current_user)):
    return {"message": f"Welcome {current_user.username}!"}

@auth_router.get("/profile")
def view_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "created_at": current_user.created_at,
        "current_package": current_user.current_package,
        "license_key": current_user.license_key,
    }

@auth_router.post("/profile/update_password")
def update_password(
    payload: PasswordUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(status_code=403, detail="Incorrect current password")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@auth_router.post("/profile/update_email")
def update_email(new_email: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.email = new_email
    db.commit()
    return {"message": "Email updated successfully"}

@auth_router.get("/2fa/setup")
def setup_2fa(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if current_user.has_2fa:
        raise HTTPException(status_code=400, detail="2FA already enabled")

    # 1. Generate a secret
    secret = pyotp.random_base32()

    # 2. Save secret to user
    current_user.twofa_secret = secret
    db.commit()

    # 3. Generate provisioning URL
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=current_user.email, issuer_name="ConkerTweaks")

    # 4. Generate QR Code
    img = qrcode.make(uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)

    return StreamingResponse(buf, media_type="image/png")

@auth_router.post("/2fa/verify")
def verify_2fa(code: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.twofa_secret:
        raise HTTPException(status_code=400, detail="2FA not setup")

    totp = pyotp.TOTP(current_user.twofa_secret)

    if not totp.verify(code):
        raise HTTPException(status_code=403, detail="Invalid 2FA code")

    current_user.has_2fa = True
    db.commit()

    return {"message": "2FA verified and enabled"}
