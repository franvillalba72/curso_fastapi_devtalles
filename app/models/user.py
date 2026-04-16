# Para que FastAPI pueda importar el modelo de usuario, es necesario crear este archivo __init__.py en el directorio models y agregar la importación del UserORM. Esto permite que el modelo de usuario esté disponible para su uso en otras partes de la aplicación, como en los routers o servicios que lo necesiten. Además, si queremos que se cree la tabla de usuarios en la base de datos, es necesario que el modelo esté registrado en el archivo __init__.py para que SQLAlchemy lo reconozca al crear las tablas.

from datetime import datetime
from typing import Literal

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

Role = Literal["admin", "user", "editor"]


class UserORM(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[Role] = mapped_column(
        Enum("admin", "user", "editor", name="role_enum"), default="user"
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
