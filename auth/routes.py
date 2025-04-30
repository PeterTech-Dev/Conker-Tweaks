from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from schemas.users import UserCreate, UserLogin, UserResponse
from models.users import User
from database import get_db
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
import os
from dotenv import load_dotenv
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
RECAPTCHA_PROJECT_ID = os.getenv("RECAPTCHA_PROJECT_ID")
RECAPTCHA_SITE_KEY = os.getenv("RECAPTCHA_SITE_KEY")
RECAPTCHA_MIN_SCORE = float(os.getenv("RECAPTCHA_MIN_SCORE", "0.5"))

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
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Register route
@auth_router.post("/register", response_model=UserResponse)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    try:

        result = create_assessment(RECAPTCHA_PROJECT_ID, RECAPTCHA_SITE_KEY, user.recaptcha_token, "register")
        if result.risk_analysis.score < RECAPTCHA_MIN_SCORE:
            raise HTTPException(status_code=400, detail="Low reCAPTCHA score — possible bot.")

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
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token = create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer"}

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
    )
    try:
        result = create_assessment(RECAPTCHA_PROJECT_ID, RECAPTCHA_SITE_KEY, user.recaptcha_token, "register")
        if result.risk_analysis.score < RECAPTCHA_MIN_SCORE:
            raise HTTPException(status_code=400, detail="Low reCAPTCHA score — possible bot.")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
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
    }

@auth_router.post("/profile/update_password")
def update_password(new_password: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.hashed_password = hash_password(new_password)
    db.commit()
    return {"message": "Password updated successfully"}

@auth_router.post("/profile/update_email")
def update_email(new_email: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    current_user.email = new_email
    db.commit()
    return {"message": "Email updated successfully"}