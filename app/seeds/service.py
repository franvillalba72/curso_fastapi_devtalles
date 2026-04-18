from contextlib import contextmanager
from typing import Optional

from pwdlib import PasswordHash
from pydantic import Tag
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.category import CategoryORM
from app.models.tag import TagORM
from app.models.user import UserORM
from app.seeds.data.categories import CATEGORIES
from app.seeds.data.tags import TAGS
from app.seeds.data.users import USERS


def hash_password(password: str) -> str:
    return PasswordHash.recommended().hash(password)


@contextmanager
def atomic(db: Session):
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise


def _user_by_email(db: Session, email: str) -> Optional[UserORM]:
    return db.execute(select(UserORM).where(UserORM.email == email)).scalars().first()


def _category_by_slug(db: Session, slug: str) -> Optional[CategoryORM]:
    return (
        db.execute(select(CategoryORM).where(CategoryORM.slug == slug))
        .scalars()
        .first()
    )


def _tag_by_name(db: Session, name: str) -> Optional[TagORM]:
    return db.execute(select(TagORM).where(TagORM.name == name)).scalars().first()


def seed_users(db: Session):
    with atomic(db):
        for user in USERS:
            obj = _user_by_email(db, user["email"])
            if obj:
                changed = False
                if obj.full_name != user["full_name"]:
                    obj.full_name = user["full_name"]
                    changed = True
                if not PasswordHash().verify(user["password"], obj.hashed_password):
                    obj.hashed_password = hash_password(user["password"])
                    changed = True
                if obj.role != user["role"]:
                    obj.role = user["role"]
                    changed = True
                if changed:
                    db.add(obj)
            else:
                db.add(
                    UserORM(
                        email=user["email"],
                        full_name=user["full_name"],
                        hashed_password=hash_password(user["password"]),
                        role=user["role"],
                    )
                )


def seed_categories(db: Session):
    with atomic(db):
        for category in CATEGORIES:
            obj = _category_by_slug(db, category["slug"])
            if obj:
                if obj.name != category["name"]:
                    obj.name = category["name"]
                    db.add(obj)
            else:
                db.add(
                    CategoryORM(
                        name=category["name"],
                        slug=category["slug"],
                    )
                )


def seed_tags(db: Session):
    with atomic(db):
        for tag in TAGS:
            obj = _tag_by_name(db, tag["name"])
            if obj:
                if obj.name != tag["name"]:
                    obj.name = tag["name"]
                    db.add(obj)
            else:
                db.add(
                    TagORM(
                        name=tag["name"],
                    )
                )


def run_all() -> None:
    with SessionLocal() as db:
        seed_users(db)
        seed_categories(db)
        seed_tags(db)


def run_users() -> None:
    with SessionLocal() as db:
        seed_users(db)


def run_categories() -> None:
    with SessionLocal() as db:
        seed_categories(db)


def run_tags() -> None:
    with SessionLocal() as db:
        seed_tags(db)
