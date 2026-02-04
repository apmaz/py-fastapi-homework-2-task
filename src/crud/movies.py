from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.strategy_options import selectinload
from sqlalchemy.sql.expression import desc

import schemas
from database.models import (
    MovieModel,
    CountryModel,
    GenreModel,
    ActorModel,
    LanguageModel
)
from database.session_postgresql import AsyncPostgresqlSessionLocal
from sqlalchemy import select
import datetime
from fastapi import HTTPException


async def get_movies_list(db: AsyncSession, skip: int = 1, limit: int = 10):
    return (await (db.scalars(select(MovieModel).order_by(desc(MovieModel.id)).offset(skip).limit(limit)))).all()


async def create_country(db: AsyncSession, country: schemas.CountryInSchema):
    db_country = CountryModel(
        name=country.name,
        code=country.code,
    )
    db.add(db_country)
    await db.commit()
    await db.refresh(db_country)

    return db_country


async def create_genre(db: AsyncSession, genre: schemas.GenreInSchema):
    db_genre = GenreModel(
        name=genre.name
    )
    db.add(db_genre)
    await db.commit()
    await db.refresh(db_genre)

    return db_genre


async def create_actor(db: AsyncSession, actor: schemas.ActorInSchema):
    db_actor = ActorModel(
        name=actor.name
    )
    db.add(db_actor)
    await db.commit()
    await db.refresh(db_actor)

    return db_actor


async def create_language(db: AsyncSession, language: schemas.LanguageInSchema):
    db_language = LanguageModel(
        name=language.name
    )
    db.add(db_language)
    await db.commit()
    await db.refresh(db_language)

    return db_language


async def get_or_create_genre(genre_name: str):
    async with AsyncPostgresqlSessionLocal() as db:
        genre_obj = await db.scalar(select(GenreModel).where(GenreModel.name == genre_name))
        if not genre_obj:
            genre_schema = schemas.GenreInSchema(
                name=genre_name
            )
            genre_obj = await create_genre(db, genre_schema)
            return genre_obj
        return genre_obj


async def get_or_create_actor(actor_name: str):
    async with AsyncPostgresqlSessionLocal() as db:
        actor_obj = await db.scalar(select(ActorModel).where(ActorModel.name == actor_name))
        if not actor_obj:
            actor_schema = schemas.ActorInSchema(
                name=actor_name
            )
            actor_obj = await create_actor(db, actor_schema)
            return actor_obj
        return actor_obj


async def get_or_create_language(language_name: str):
    async with AsyncPostgresqlSessionLocal() as db:
        language_obj = await db.scalar(select(LanguageModel).where(LanguageModel.name == language_name))
        if not language_obj:
            language_schema = schemas.LanguageInSchema(
                name=language_name
            )
            language_obj = await create_language(db, language_schema)
            return language_obj
        return language_obj


async def check_duplicate_movie(movie_name: str, movie_data: datetime.date, db: AsyncSession):
    movie = (
        await db.scalar(select(MovieModel).where(MovieModel.name == movie_name, MovieModel.date == movie_data))
    )
    if movie is not None:
        raise HTTPException(
            status_code=409, detail=f"A movie with the name '{movie_name}' and release date '{movie_data}' already exists."
        )


async def get_movie_by_id(movie_id: int, db: AsyncSession):
    movie = await db.scalar(select(MovieModel).where(MovieModel.id == movie_id))
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")

    stmt = select(MovieModel).where(MovieModel.id == movie_id).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)
    )
    result = await db.execute(stmt)
    movie = result.scalar_one()
    return movie


async def delete_movie(movie: MovieModel, db: AsyncSession):
    await db.delete(movie)
    await db.commit()


async def patch_movie(db_movie: MovieModel, db: AsyncSession, movie: schemas.MovieUpdateInSchema):
    for field, value in movie:
        setattr(db_movie, field, value)

    await db.commit()
    await db.refresh(db_movie)

    return db_movie