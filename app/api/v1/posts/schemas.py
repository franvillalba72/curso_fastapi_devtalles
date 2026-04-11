from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


# **************************** Pydantic Validation Models ****************************
class Tag(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=30,
        description="The name of the tag, must be between 2 and 30 characters",
    )
    model_config = ConfigDict(from_attributes=True)


class Author(BaseModel):
    name: str
    email: Optional[EmailStr]

    model_config = ConfigDict(from_attributes=True)


class PostBase(BaseModel):
    title: str
    content: str
    tags: Optional[List[Tag]] = Field(default_factory=list)
    author: Optional[Author] = None

    model_config = ConfigDict(from_attributes=True)


class PostCreate(BaseModel):
    title: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="The title of the post, must be between 3 and 100 characters",
        examples=["Mi primer post con FastAPI"],
    )

    content: Optional[str] = Field(
        default="Contenido no disponible",
        min_length=10,
        description="The content of the post, must be at least 10 characters",
        examples=["Este es el contenido de mi primer post con FastAPI"],
    )

    tags: Optional[List[Tag]] = Field(default_factory=list)
    # author: Optional[Author] = None

    @field_validator("title")
    @classmethod
    def not_allowed_title(cls, value: str) -> str:
        if "spam" in value.lower():
            raise ValueError("Title cannot contain the word 'spam'")
        return value


class PostUpdate(BaseModel):
    title: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="The title of the post, must be between 3 and 100 characters",
    )
    content: Optional[str] = Field(
        None,
        min_length=10,
        description="The content of the post, must be at least 10 characters",
    )


class PostPublic(PostBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostSummary(BaseModel):
    id: int
    title: str

    model_config = ConfigDict(from_attributes=True)


class PaginatedPost(BaseModel):
    page: int
    per_page: int
    total: int
    total_pages: int
    has_prev: bool
    has_next: bool
    order_by: Literal["id", "title"]
    direction: Literal["asc", "desc"]
    search: Optional[str] = None
    items: List[PostPublic]
