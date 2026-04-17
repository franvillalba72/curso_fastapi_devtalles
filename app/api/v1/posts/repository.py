from concurrent.interpreters import get_current
from locale import normalize
from math import ceil
from typing import List, Optional, Tuple

from fastapi import Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.security import get_current_user
from app.models.post import PostORM
from app.models.tag import TagORM
from app.models.user import UserORM


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, post_id: int) -> Optional[PostORM]:
        post_find = select(PostORM).where(PostORM.id == post_id)
        return self.db.execute(post_find).scalar_one_or_none()

    def search(
        self,
        query: Optional[str],
        order_by: str,
        direction: str,
        page: int,
        per_page: int,
    ) -> Tuple[int, List[PostORM]]:
        results = select(PostORM)

        if query:
            results = results.where(PostORM.title.ilike(f"%{query}%"))

        total = (
            self.db.scalar(select(func.count()).select_from(results.subquery())) or 0
        )

        if total == 0:
            return 0, []

        total_pages = ceil(total / per_page)
        current_page = min(page, max(1, total_pages))

        order_col = PostORM.id if order_by == "id" else func.lower(PostORM.title)

        results = results.order_by(
            order_col.asc() if direction == "asc" else order_col.desc()
        )

        offset = (current_page - 1) * per_page
        items = self.db.execute(results.limit(per_page).offset(offset)).scalars().all()

        return total, items

    def by_tags(self, tags: List[str]) -> List[PostORM]:
        normalized_tags = [tag.strip().lower() for tag in tags if tag.strip()]
        if not normalized_tags:
            return []

        post_list = (
            select(PostORM)
            .options(selectinload(PostORM.tags), joinedload(PostORM.user))
            .where(PostORM.tags.any(func.lower(TagORM.name).in_(normalized_tags)))
            .order_by(PostORM.id.asc())
        )

        return self.db.execute(post_list).scalars().all()

    def ensure_tag(self, tag: str) -> TagORM:
        normalized_tag = tag.strip().lower()
        tag_obj = self.db.execute(
            select(TagORM).where(func.lower(TagORM.name) == normalized_tag)
        ).scalar_one_or_none()

        if not tag_obj:
            tag_obj = TagORM(name=tag)
            self.db.add(tag_obj)
            self.db.flush()

        return tag_obj

    def create_post(
        self,
        title: str,
        content: str,
        tags: List[dict],
        image_url: Optional[str],
        category_id: Optional[int],
        author: UserORM = Depends(get_current_user),
    ) -> PostORM:
        tag_objs = []
        names = (
            tags[0]["name"].split(",") if "," in tags[0]["name"] else [tags[0]["name"]]
        )
        for name in names:
            tag_objs.append(self.ensure_tag(name.strip()))

        new_post = PostORM(
            title=title,
            content=content,
            image_url=image_url,
            user=author,
            tags=tag_objs,
            category_id=category_id,
        )

        self.db.add(new_post)
        self.db.flush()

        return new_post

    def update_post(self, post: PostORM, updates: dict) -> PostORM:
        for key, value in updates.items():
            setattr(post, key, value)

        return post

    def delete_post(self, post: PostORM) -> None:
        self.db.delete(post)
