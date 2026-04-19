from datetime import datetime
from typing import Annotated, List, Literal, Optional

from fastapi import Form
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.api.v1.auth.schemas import UserBase, UserPublic
from app.api.v1.categories.schemas import CategoryPublic
from app.models import category


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
    user: Optional[UserPublic] = None
    image_url: Optional[str] = None
    category: Optional[CategoryPublic] = None

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
    category_id: Optional[int] = None
    tags: Optional[List[Tag]] = Field(default_factory=list)

    # Para recibir datos de un formulario multipart/form-data en vez de JSON, se define un método de clase que utiliza Form() para cada campo
    @classmethod
    def as_form(
        cls,
        title: Annotated[str, Form(min_length=3)],
        content: Annotated[str, Form(min_length=10)],
        category_id: Annotated[int, Form(ge=1)],
        tags: Annotated[Optional[List[str]], Form()] = None,
    ):
        tag_objects = [Tag(name=tag) for tag in (tags or [])]
        return cls(
            title=title, content=content, category_id=category_id, tags=tag_objects
        )

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
    category_id: Optional[int] = None


class PostPublic(PostBase):
    id: int
    slug: str
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
