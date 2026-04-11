from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from app.api.v1.auth.schemas import Token, UserPublic
from app.core.security import create_access_token, get_current_user

FAKE_USERS = {
    "franvillalba@example.com": {
        "email": "franvillalba@example.com",
        "username": "franvillalba",
        "password": "holamundo",
    },
    "alumno@example.com": {
        "email": "alumno@example.com",
        "username": "alumno",
        "password": "holamundo",
    },
}

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    user = FAKE_USERS.get(
        form_data.username
    )  # En un caso real, aquí haríamos una consulta a la base de datos
    if not user or user["password"] != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas",
        )

    access_token = create_access_token(
        data={"sub": user["email"], "username": user["username"]},
        expires_delta=timedelta(minutes=30),
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserPublic)
async def read_current_user(
    current_user: dict = Depends(get_current_user),
) -> UserPublic:
    return {"email": current_user["email"], "username": current_user["username"]}
