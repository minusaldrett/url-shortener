import validators
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import URL

from . import models, schemas, crud
from .database import SessionLocal, engine
from .config import get_settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="URL Shortener API")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def raise_bad_request(message: str):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request: Request):
    raise HTTPException(
        status_code=404, detail=f"URL '{request.url}' doesn't exist"
    )


def get_admin_info(db_url: models.URL) -> schemas.URLInfo:
    base_url = URL(get_settings().base_url)

    short_url = str(base_url.replace(path=db_url.key))
    stats_endpoint = app.url_path_for("get_url_stats", short_id=db_url.key)
    stats_url = str(base_url.replace(path=stats_endpoint))

    return schemas.URLInfo(
        target_url=db_url.target_url,
        short_id=db_url.key,
        url=short_url,
        stats_url=stats_url,
        clicks=db_url.clicks,
    )


@app.post("/shorten", response_model=schemas.URLInfo)
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request("Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url)

    base_url = URL(get_settings().base_url)

    return schemas.URLInfo(
        target_url=db_url.target_url,
        short_id=db_url.key,
        url=str(base_url.replace(path=db_url.key)),
        clicks=db_url.clicks,
        is_active=db_url.is_active
    )


@app.get("/{short_id}")
def forward_to_target_url(short_id: str, request: Request, db: Session = Depends(get_db)):
    db_url = crud.get_db_url_by_short_id(db=db, short_id=short_id)

    if not db_url:
        raise_not_found(request)

    crud.update_db_clicks(db=db, db_url=db_url)

    return RedirectResponse(db_url.target_url)


@app.get("/stats/{short_id}", response_model=schemas.URLInfo)
def get_url_stats(short_id: str, request: Request, db: Session = Depends(get_db)):
    db_url = crud.get_db_url_by_short_id(db=db, short_id=short_id)

    if not db_url:
        raise_not_found(request)

    base_url = URL(get_settings().base_url)

    return schemas.URLInfo(
        target_url=db_url.target_url,
        short_id=db_url.key,
        url=str(base_url.replace(path=db_url.key)),
        clicks=db_url.clicks,
        is_active=db_url.is_active
    )
