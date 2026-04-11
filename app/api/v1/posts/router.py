import asyncio
from math import ceil
import time
from typing import List, Literal, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.db import get_db
from .schemas import PostPublic, PaginatedPost, PostCreate, PostUpdate, PostSummary
from .repository import PostRepository
from app.core.security import oauth2_scheme, get_current_user
import threading

router = APIRouter(prefix="/posts", tags=["Posts"])


# @router.get("/sync")
# def sync_endpoint():
#     print(f"Thread {threading.get_ident()} - Starting sync endpoint")
#     time.sleep(8)  # Simula una operación síncrona que tarda 8 segundos
#     print(f"Thread {threading.get_ident()} - Ending sync endpoint")
#     return {"message": "This is a synchronous endpoint"}


# @router.get("/async")
# async def async_endpoint():
#     print(f"Thread {threading.get_ident()} - Starting async endpoint")
#     await asyncio.sleep(8)  # Simula una operación asíncrona que tarda 8 segundos
#     print(f"Thread {threading.get_ident()} - Ending async endpoint")
#     return {"message": "This is an asynchronous endpoint"}


@router.get("/", response_model=PaginatedPost)
def list_posts(
    text: Optional[str] = Query(
        default=None,
        description="Search query for post titles (Deprecated, use 'search' instead)",
        deprecated=True,
    ),
    query: Optional[str] = Query(
        default=None,
        description="Search query for post titles",
        alias="search",
        min_length=3,
        max_length=50,
        pattern=r"^[\w\sáéíóúÁÉÍÓÚüÜ-]+$",
    ),
    per_page: int = Query(
        default=10, ge=1, le=50, description="Maximum number of posts to return"
    ),
    page: int = Query(default=1, ge=1, description="Page number to return"),
    order_by: Literal["id", "title"] = Query(
        default="id", description="Field to order the results by"
    ),
    direction: Literal["asc", "desc"] = Query(
        default="asc", description="Direction of the ordering"
    ),
    db: Session = Depends(get_db),
):
    repository = PostRepository(db)

    query = query or text

    total, items = repository.search(query, order_by, direction, page, per_page)

    total_pages = ceil(total / per_page) if total > 0 else 0
    current_page = 1 if total_pages == 0 else min(page, total_pages)
    has_prev = current_page > 1
    has_next = current_page < total_pages

    return PaginatedPost(
        page=current_page,
        per_page=per_page,
        total=total,
        total_pages=total_pages,
        has_prev=has_prev,
        has_next=has_next,
        order_by=order_by,
        direction=direction,
        search=query,
        items=items,
    )


@router.get(
    "/by-tags",
    response_model=List[PostPublic],
    response_description="Posts encontrados por tags",
)
def filter_by_tags(
    tags: List[str] = Query(
        ...,
        min_length=1,
        description="List of tags to filter posts by, example: ?tags=python&tags=fastapi",
    ),
    db: Session = Depends(get_db),
):
    return PostRepository(db).by_tags(tags)


@router.get(
    "/{post_id}",
    response_model=Union[PostPublic, PostSummary],
    response_description="Post encontrado",
)
def get_post(
    post_id: int = Path(
        ..., ge=1, title="Post ID", description="The ID of the post to retrieve"
    ),
    include_content: bool = Query(
        default=True, description="Include post content in the response"
    ),
    db: Session = Depends(get_db),
):
    post = PostRepository(db).get(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    if include_content:
        return PostPublic.model_validate(post, from_attributes=True)
    else:
        return PostSummary.model_validate(post, from_attributes=True)


@router.post(
    "/",
    response_model=PostPublic,
    status_code=status.HTTP_201_CREATED,
    response_description="Post creado exitosamente",
)
def create_post(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    new_post = PostRepository(db).create_post(
        title=post.title,
        content=post.content,
        author=current_user,
        tags=[tag.model_dump() for tag in post.tags],
    )

    try:
        db.commit()
        db.refresh(
            new_post
        )  # Asegurarse de refrescar el objeto para obtener los datos generados por la base de datos (como el ID). Siempre después de commit para evitar problemas con transacciones.
        return new_post
    except IntegrityError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A post with this title already exists",
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating post",
        )


@router.put(
    "/{post_id}",
    response_model=PostPublic,
    response_description="Post actualizado exitosamente",
    response_model_exclude_none=True,
)
def update_post(
    post_id: int,
    updated_post: PostUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):

    repository = PostRepository(db)
    post = repository.get(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    try:
        updates = updated_post.model_dump(
            exclude_unset=True
        )  # Convertir a dict desde el modelo y excluir campos no proporcionados
        post = repository.update_post(post, updates)
        db.commit()
        db.refresh(
            post
        )  # Asegurarse de refrescar el objeto para obtener los datos actualizados
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating post",
        )

    return PostPublic.model_validate(post, from_attributes=True)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_description="Post eliminado exitosamente",
)
def delete_post(
    post_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    repository = PostRepository(db)
    post = repository.get(post_id)

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    try:
        repository.delete_post(post)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting post",
        )

    return


@router.get("/secure")
def secure_endpoint(token: str = Depends(oauth2_scheme)):
    return {"message": "Access granted to secure endpoint", "token": token}
