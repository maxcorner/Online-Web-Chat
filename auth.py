from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash
from sqlmodel import select

from db import SessionDep
from models import User

SECRET_KEY = "mr9"
ALGORITHM = "HS256"

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain, hashed):
    return password_hash.verify(plain, hashed)


def get_password_hash(password: str):
    return password_hash.hash(password)


def get_user(session: SessionDep, username: str):
    return session.exec(select(User).where(User.username == username)).first()


def authenticate_user(session: SessionDep, username: str, password: str):
    user = get_user(session, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    data.update({"exp": expire})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception

    user = get_user(session, username)
    if user is None:
        raise credentials_exception

    return user