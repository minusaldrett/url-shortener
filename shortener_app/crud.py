from sqlalchemy.orm import Session

from . import keygen, models, schemas


def create_db_url(db: Session, url: schemas.URLBase) -> models.URL:
    key = keygen.create_unique_random_key(db)

    db_url = models.URL(
        target_url=url.target_url,
        key=key
    )

    db.add(db_url)
    db.commit()
    db.refresh(db_url)

    return db_url


def get_db_url_by_short_id(db: Session, short_id: str) -> models.URL:
    return (
        db.query(models.URL)
        .filter(models.URL.key == short_id, models.URL.is_active)
        .first()
    )


def update_db_clicks(db: Session, db_url: models.URL):
    db_url.clicks += 1
    db.commit()
    db.refresh(db_url)
    return db_url