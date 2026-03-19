from datetime import datetime, timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import requests
from requests.exceptions import RequestException

from app.core import security
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse, UserProfileUpdate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Inactive user")
    if user.suspended_until and user.suspended_until > datetime.utcnow():
        raise HTTPException(status_code=403, detail="User account is suspended")
    return user

@router.post("/register", response_model=UserResponse)
def register(*, db: Session = Depends(get_db), user_in: UserCreate) -> Any:
    """
    Register a new user.
    """
    try:
        # Check if user with this email exists
        user = db.query(User).filter(User.email == user_in.email).first()
        if user:
            raise HTTPException(
                status_code=400,
                detail="A user with this email already exists.",
            )
        
        # Check if user with this username exists
        user = db.query(User).filter(User.username == user_in.username).first()
        if user:
            raise HTTPException(
                status_code=400,
                detail="A user with this username already exists.",
            )
        
        # Create new user
        user = User(
            email=user_in.email,
            username=user_in.username,
            hashed_password=security.get_password_hash(user_in.password),
            role=user_in.role,
            feature_flags=user_in.feature_flags,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    except RequestException as e:
        raise HTTPException(
            status_code=503,
            detail="Network error or server is unreachable. Please try again later.",
        ) from e

@router.post("/token", response_model=Token)
def login_access_token(
    db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/test-token", response_model=UserResponse)
def test_token(current_user: User = Depends(get_current_user)) -> Any:
    """
    Test access token by getting current user.
    """
    return current_user


def get_current_admin(current_user: User = Depends(get_current_user)) -> User:
    if not (current_user.is_superuser or current_user.role in {"admin", "super_admin"}):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def get_current_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if not (current_user.is_superuser or current_user.role == "super_admin"):
        raise HTTPException(status_code=403, detail="Super-admin access required")
    return current_user


def get_current_expert(current_user: User = Depends(get_current_user)) -> User:
    if not (current_user.is_superuser or current_user.is_expert or current_user.role in {"expert", "super_admin"}):
        raise HTTPException(status_code=403, detail="Expert access required")
    return current_user


@router.get("/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)) -> Any:
    return current_user


@router.put("/me", response_model=UserResponse)
def update_profile(
    *,
    db: Session = Depends(get_db),
    profile_in: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
) -> Any:
    updates = profile_in.dict(exclude_unset=True)

    if "email" in updates and updates["email"] != current_user.email:
        existing = db.query(User).filter(User.email == updates["email"], User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="A user with this email already exists.")

    if "username" in updates and updates["username"] != current_user.username:
        existing = db.query(User).filter(User.username == updates["username"], User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="A user with this username already exists.")

    password = updates.pop("password", None)
    if password:
        current_user.hashed_password = security.get_password_hash(password)

    for field, value in updates.items():
        setattr(current_user, field, value)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/users", response_model=list[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    del current_user
    return db.query(User).order_by(User.username.asc()).all()
