from datetime import timedelta

from dns import update
from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.api.v1.auth import repository
from app.api.v1.auth.repository import UserRepository
from app.api.v1.auth.schemas import (
    RoleUpdate,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserPublic,
)
from app.core.db import get_db
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
    require_admin,
    oauth2_token,
)
from app.models.user import UserORM


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED
)
async def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserPublic:
    repository = UserRepository(db)
    if repository.get_by_email(payload.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    user = repository.create(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )

    try:
        db.commit()
        db.refresh(user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al crear el usuario",
        )

    return UserPublic.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, db: Session = Depends(get_db)) -> TokenResponse:
    repository = UserRepository(db)
    user = repository.get_by_email(payload.email)
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    access_token = create_access_token(sub=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": UserPublic.model_validate(user),
    }


@router.get("/me", response_model=UserPublic)
async def read_current_user(
    current_user: UserORM = Depends(get_current_user),
) -> UserPublic:
    return UserPublic.model_validate(current_user)


@router.put("/role/{user_id}", response_model=UserPublic)
def set_role(
    user_id: int = Path(..., ge=1),
    payload: RoleUpdate = None,
    db: Session = Depends(get_db),
    _admin_user: UserORM = Depends(
        require_admin
    ),  # Solo los administradores pueden cambiar el rol de otros usuarios
) -> UserPublic:
    repository = UserRepository(db)
    user = repository.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado"
        )
    updated_user = repository.set_role(user, payload.role)
    try:
        db.commit()
        db.refresh(updated_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error al actualizar el rol del usuario",
        )

    return UserPublic.model_validate(updated_user)


# Endpoint para obtener el token de acceso (login) desde Swagger UI
@router.post("/token")
async def oauth2_token(response=Depends(oauth2_token)):
    return response
