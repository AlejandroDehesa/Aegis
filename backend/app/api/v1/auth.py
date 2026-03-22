from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin, UserRead


router = APIRouter()


INVALID_CREDENTIALS_MESSAGE = "Invalid email or password"


@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def signup(user_in: UserCreate, db: Session = Depends(get_db)) -> User:
    existing_user = db.execute(
        select(User).where(User.email == user_in.email)
    ).scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = User(
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )

    db.add(user)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        ) from None

    db.refresh(user)
    return user


@router.post("/login", response_model=UserRead)
def login(user_in: UserLogin, db: Session = Depends(get_db)) -> User:
    user = db.execute(
        select(User).where(User.email == user_in.email)
    ).scalar_one_or_none()

    if user is None or not verify_password(user_in.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=INVALID_CREDENTIALS_MESSAGE,
        )

    return user
