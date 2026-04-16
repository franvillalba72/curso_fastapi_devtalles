import stat

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.tags.repository import TagRepository
from app.api.v1.tags.schemas import TagCreate, TagPublic
from app.core.db import get_db
from app.core.security import (
    get_current_user,
    require_admin,
    require_editor,
    require_user,
)


router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=dict, response_description="List of tags")
def list_tags(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    order_by: str = Query("id", pattern="^(id|name)$"),
    direction: str = Query("asc", pattern="^(asc|desc)$"),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    tag_repo = TagRepository(db)
    return tag_repo.list_tags(
        search=search,
        order_by=order_by,
        direction=direction,
        page=page,
        per_page=per_page,
    )


@router.post(
    "",
    response_model=TagPublic,
    response_description="Tag created successfully",
    status_code=status.HTTP_201_CREATED,
)
def create_tag(
    tag: TagCreate, db: Session = Depends(get_db), _editor=Depends(require_editor)
):
    """
    Create a new tag. If a tag with the same name (case-insensitive) already exists, it will return the existing tag instead of creating a duplicate.
    """
    tag_repo = TagRepository(db)
    try:
        tag_created = tag_repo.create_tag(name=tag.name)
        db.commit()  # Asegura que los cambios se guarden en la base de datos
        db.refresh(tag_created)  # Refresca el objeto para obtener el ID generado
        return tag_created
    except SQLAlchemyError:
        db.rollback()  # Revertir cualquier cambio en caso de error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating tag",
        )


@router.put(
    "/{tag_id}",
    response_model=TagPublic,
    response_description="Tag updated successfully",
)
def update_tag(
    tag_id: int,
    updated_tag: TagCreate,
    db: Session = Depends(get_db),
    _editor=Depends(require_editor),
):
    """
    Update the name of an existing tag. If the new name conflicts with another existing tag (case-insensitive), it will return a 400 error.
    """
    tag_repo = TagRepository(db)
    try:
        tag_updated = tag_repo.update_tag(tag_id=tag_id, new_name=updated_tag.name)
        db.commit()  # Asegura que los cambios se guarden en la base de datos
        db.refresh(
            tag_updated
        )  # Refresca el objeto para obtener cualquier cambio generado por la base de datos
        return tag_updated
    except HTTPException:
        raise  # Re-lanzar excepciones HTTP para que FastAPI las maneje correctamente
    except SQLAlchemyError:
        db.rollback()  # Revertir cualquier cambio en caso de error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating tag",
        )


@router.delete(
    "/{tag_id}",
    response_description="Tag deleted successfully",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_tag(
    tag_id: int, db: Session = Depends(get_db), _admin=Depends(require_admin)
):
    """
    Delete an existing tag by its ID. If the tag does not exist, it will return a 404 error.
    """
    tag_repo = TagRepository(db)
    try:
        tag_repo.delete_tag(tag_id=tag_id)
        db.commit()  # Asegura que los cambios se guarden en la base de datos
    except HTTPException:
        raise  # Re-lanzar excepciones HTTP para que FastAPI las maneje correctamente
    except SQLAlchemyError:
        db.rollback()  # Revertir cualquier cambio en caso de error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error deleting tag",
        )


@router.get(
    "/most-used",
    response_model=dict,
    response_description="Most used tag with its usage count",
)
def most_used_tag(db: Session = Depends(get_db), user=Depends(get_current_user)):
    tag_repo = TagRepository(db)
    row = tag_repo.most_popular()
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No tags found"
        )
    return row
