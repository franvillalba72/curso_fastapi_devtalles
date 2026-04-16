from datetime import datetime, timedelta, timezone
from typing import Literal, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from jwt import PyJWTError
from pwdlib import PasswordHash
from sqlalchemy.orm import Session

from app.api.v1.auth.repository import UserRepository
from app.core.db import get_db
from app.models.user import UserORM
from app.core.config import Settings

password_hash = PasswordHash.recommended()
# Defino el esquema de autenticación OAuth2 con contraseña (tokenUrl es la URL donde los usuarios pueden obtener un token)
# En este caso, la URL es "/api/v1/auth/token" que corresponde al endpoint que definiremos para el login desde un formulario para Swagger UI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

credentials_exc = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No autenticado",
    headers={"WWW-Authenticate": "Bearer"},
)


def raise_expired_token():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )


def raise_forbidden():
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No tienes permiso para realizar esta acción",
        headers={"WWW-Authenticate": "Bearer"},
    )


def invalid_credentials():
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales inválidas"
    )


# def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
#     to_encode = data.copy()
#     expire = datetime.now(tz=timezone.utc) + (
#         expires_delta
#         if expires_delta
#         else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )
#     to_encode.update({"exp": expire})
#     token = jwt.encode(payload=to_encode, key=SECRET_KEY, algorithm=ALGORITHM)
#     return token


def decode_access_token(token: str) -> dict:
    payload = jwt.decode(
        jwt=token, key=Settings.JWT_SECRET_KEY, algorithms=[Settings.JWT_ALGORITHM]
    )
    return payload


def create_access_token(sub: str, minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=minutes or Settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    return jwt.encode(
        {"sub": sub, "exp": expire},
        Settings.JWT_SECRET_KEY,
        algorithm=Settings.JWT_ALGORITHM,
    )


async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserORM:

    try:
        playload = decode_access_token(token)
        sub: Optional[str] = playload.get("sub")
        if not sub:
            raise credentials_exc

        user_id = int(sub)
    except ExpiredSignatureError:
        raise raise_expired_token()
    except InvalidTokenError:
        raise credentials_exc
    except PyJWTError:
        raise invalid_credentials()

    user = db.get(UserORM, user_id)

    if not user or not user.is_active:
        raise invalid_credentials()

    return user


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def require_role(min_role: Literal["user", "editor", "admin"]):
    order = {"user": 0, "editor": 1, "admin": 2}

    def role_checker(current_user: UserORM = Depends(get_current_user)) -> UserORM:
        if order[current_user.role] < order[min_role]:
            raise raise_forbidden()
        return current_user

    return role_checker


# Variables de dependencia para requerir roles específicos en los endpoints
require_user = require_role("user")
require_editor = require_role("editor")
require_admin = require_role("admin")


# Función para obtener el token de acceso (login) para usarlo desde Swagger UI
async def oauth2_token(
    form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    repository = UserRepository(db)
    user = repository.get_by_email(form.username)
    if not user or not verify_password(form.password, user.hashed_password):
        raise invalid_credentials()

    access_token = create_access_token(sub=str(user.id))
    return {"access_token": access_token, "token_type": "bearer"}
