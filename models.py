from sqlmodel import SQLModel, Field


class UserBase(SQLModel):
    username: str = Field(index=True)


class User(UserBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str
    hashed_password: str


class UserCreate(UserBase):
    password: str


class UserUpdate(SQLModel):
    username: str | None = None
    password: str | None = None


class UserPublic(UserBase):
    id: int


class Token(SQLModel):
    access_token: str
    token_type: str