from fastapi import FastAPI, HTTPException, Depends, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import select
from datetime import timedelta

from db import SessionDep, create_db_and_tables
from auth import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user,
)
from models import User, UserCreate, UserUpdate, UserPublic, Token


ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI()


@app.on_event("startup")
def startup():
    create_db_and_tables()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/api/v1/")
def api_v1():
    return {"message": "API v1"}


@app.post("/token/", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: SessionDep = None,
):
    user = authenticate_user(session, form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )

    token = create_access_token(
        {"sub": user.username},
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return Token(access_token=token, token_type="bearer")


@app.get("/api/v1/account/", response_model=UserPublic)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.post("/api/v1/create-user/", response_model=UserPublic)
def create_user(user: UserCreate, session: SessionDep):
    db_user = User(
        username=user.username,
        hashed_password=get_password_hash(user.password),
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.get("/api/v1/users/", response_model=list[UserPublic])
def get_users(
    session: SessionDep,
    offset: int = 0,
    limit: int = Query(le=10),
):
    return session.exec(
        select(User).offset(offset).limit(limit)
    ).all()


@app.get("/api/v1/user/{user_id}/", response_model=UserPublic)
def get_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.patch("/api/v1/users/{user_id}/", response_model=UserPublic)
def update_user(user_id: int, user: UserUpdate, session: SessionDep):
    db_user = session.get(User, user_id)

    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    data = user.model_dump(exclude_unset=True)

    if "password" in data:
        db_user.hashed_password = get_password_hash(data["password"])
        del data["password"]

    for key, value in data.items():
        setattr(db_user, key, value)

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


@app.delete("/api/v1/users/{user_id}/")
def delete_user(user_id: int, session: SessionDep):
    user = session.get(User, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    session.delete(user)
    session.commit()
    return {"success": True}