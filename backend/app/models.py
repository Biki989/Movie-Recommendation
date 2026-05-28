from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

# ── DATABASE SQLMODELS ────────────────────────────────────────────────────────

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    is_admin: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    ratings: List["UserRating"] = Relationship(back_populates="user", cascade_delete=True)
    bookmarks: List["Bookmark"] = Relationship(back_populates="user", cascade_delete=True)
    rec_history: List["RecHistory"] = Relationship(back_populates="user", cascade_delete=True)


class UserRating(SQLModel, table=True):
    __tablename__ = "user_ratings"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    movie_id: int = Field(nullable=False)
    title: str = Field(max_length=200, nullable=False)
    genres: str = Field(max_length=200, nullable=False)
    rating: float = Field(nullable=False)
    rated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="ratings")


class Bookmark(SQLModel, table=True):
    __tablename__ = "bookmarks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    movie_id: int = Field(nullable=False)
    title: str = Field(max_length=200, nullable=False)
    genres: str = Field(max_length=200, nullable=False)
    bookmarked_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="bookmarks")


class RecHistory(SQLModel, table=True):
    __tablename__ = "rec_history"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    movie_id: int = Field(nullable=False)
    title: str = Field(max_length=200, nullable=False)
    genres: str = Field(max_length=200, nullable=False)
    confidence: float = Field(nullable=False)
    recommended_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="rec_history")


# ── PYDANTIC REQUEST/RESPONSE SCHEMAS ─────────────────────────────────────────

class UserCreate(SQLModel):
    username: str
    email: str
    password: str


class UserLogin(SQLModel):
    email: str
    password: str


class UserResponse(SQLModel):
    id: int
    username: str
    email: str
    is_admin: bool
    created_at: datetime


class RatingCreate(SQLModel):
    movie_id: int
    title: str
    genres: str
    rating: float


class RatingResponse(SQLModel):
    id: int
    movie_id: int
    title: str
    genres: str
    rating: float
    rated_at: datetime


class BookmarkCreate(SQLModel):
    movie_id: int
    title: str
    genres: str


class BookmarkResponse(SQLModel):
    id: int
    movie_id: int
    title: str
    genres: str
    bookmarked_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str
