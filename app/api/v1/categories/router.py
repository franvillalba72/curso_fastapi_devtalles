from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.v1.auth import repository
from app.api.v1.categories.repository import CategoryRepository
from app.core.db import get_db
from app.api.v1.categories.schemas import CategoryCreate, CategoryUpdate, CategoryPublic

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryPublic])
def list_categories(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)
    return repository.list_many(skip=skip, limit=limit)


@router.post("", response_model=CategoryPublic, status_code=status.HTTP_201_CREATED)
def create_category(data: CategoryCreate, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)
    category_existing = repository.get_by_slug(data.slug)
    if category_existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with slug '{data.slug}' already exists.",
        )
    category = repository.create(name=data.name, slug=data.slug)
    db.commit()
    db.refresh(category)
    return category


@router.get("/{category_id}", response_model=CategoryPublic)
def get_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)
    category = repository.get(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{category_id}' not found.",
        )
    return category


@router.put("/{category_id}", response_model=CategoryPublic)
def update_category(
    category_id: int, data: CategoryUpdate, db: Session = Depends(get_db)
):
    repository = CategoryRepository(db)
    category = repository.get(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{category_id}' not found.",
        )
    category = repository.update(
        category, updates=data.model_dump(exclude_unset=True)
    )  # model_dump(exclude_unset=True) para obtener solo los campos que se han enviado en la solicitud creando un diccionario con solo esos campos
    db.commit()
    db.refresh(category)
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    repository = CategoryRepository(db)
    category = repository.get(category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID '{category_id}' not found.",
        )
    repository.delete(category)
    db.commit()
    return None
