from typing import Optional

from fastapi import HTTPException, status
from httpx import post
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.v1.tags.schemas import TagPublic
from app.models.post import PostORM, post_tags
from app.models.tag import TagORM
from app.services.pagination import paginate_query


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_tags(
        self,
        search: Optional[str],
        order_by: str = "id",
        direction: str = "asc",
        page: int = 1,
        per_page: int = 10,
    ):
        query = select(TagORM)

        if search:
            query = query.where(func.lower(TagORM.name).like(f"%{search.lower()}%"))

        allowed_order = {"id": TagORM.id, "name": func.lower(TagORM.name)}

        result = paginate_query(
            db=self.db,
            model=TagORM,
            base_query=query,
            page=page,
            per_page=per_page,
            order_by=order_by,
            direction=direction,
            allowed_order=allowed_order,
        )

        result["items"] = [TagPublic.model_validate(item) for item in result["items"]]

        return result

    def get_by_id(self, tag_id: int) -> Optional[TagORM]:
        tag_find = select(TagORM).where(TagORM.id == tag_id)
        return self.db.execute(tag_find).scalar_one_or_none()

    def create_tag(self, name: str) -> TagORM:
        normalized_name = name.strip().lower()
        tag_obj = self.db.execute(
            select(TagORM).where(func.lower(TagORM.name) == normalized_name)
        ).scalar_one_or_none()

        if tag_obj:
            return tag_obj

        tag_obj = TagORM(name=name)
        self.db.add(tag_obj)
        self.db.commit()
        self.db.refresh(tag_obj)
        return tag_obj

    def update_tag(self, tag_id: int, new_name: str) -> Optional[TagORM]:
        tag_obj = self.get_by_id(tag_id)
        if not tag_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )

        normalized_name = new_name.strip().lower()
        existing_tag = self.db.execute(
            select(TagORM).where(
                func.lower(TagORM.name) == normalized_name, TagORM.id != tag_id
            )
        ).scalar_one_or_none()

        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A tag with this name already exists.",
            )

        tag_obj.name = new_name
        self.db.flush()  # Asegura que el cambio se envíe a la base de datos para validar unicidad
        self.db.refresh(
            tag_obj
        )  # Refresca el objeto para obtener cualquier cambio generado por la base de datos
        return tag_obj

    def delete_tag(self, tag_id: int) -> bool:
        tag_obj = self.get_by_id(tag_id)
        if not tag_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found"
            )

        self.db.delete(tag_obj)
        self.db.flush()  # Asegura que el cambio se envíe a la base de datos para validar restricciones de integridad
        return True

    def most_popular(self) -> dict | None:
        row = (
            self.db.execute(
                select(
                    TagORM.id.label("id"),
                    TagORM.name.label("name"),
                    func.count(PostORM.id).label("uses"),
                )
                .join(post_tags, post_tags.c.tag_id == TagORM.id)
                .join(PostORM, PostORM.id == post_tags.c.post_id)
                .group_by(TagORM.id, TagORM.name)
                .order_by(func.count(PostORM.id).desc(), func.lower(TagORM.name).asc())
                # .limit(1)
            )
            .mappings()  # Devuelve resultados como diccionarios en lugar de objetos ORM
            .first()  # Obtiene la primera fila del resultado o None si no hay resultados
        )

        return dict(row) if row else None
