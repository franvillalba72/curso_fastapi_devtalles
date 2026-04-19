from slugify import slugify as _slugify
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.post import PostORM


def slugify_base(text: str) -> str:
    slug = _slugify(text, lowercase=True, separator="-", max_length=160)
    return slug or "post"


def ensure_unique_slug(db: Session, base_text: str) -> str:
    slug = slugify_base(base_text)

    existing_slugs = (
        db.execute(select(PostORM.slug).where(PostORM.slug.like(f"{slug}%")))
        .scalars()
        .all()
    )

    if slug not in existing_slugs:
        return slug

    suffix = 1
    new_slug = f"{slug}-{suffix}"
    while new_slug in existing_slugs:
        suffix += 1
        new_slug = f"{slug}-{suffix}"

    return new_slug
