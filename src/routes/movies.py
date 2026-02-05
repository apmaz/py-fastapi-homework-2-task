import asyncio
import math

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import schemas.movies
from crud.movies import (
    get_or_create_genre,
    get_or_create_actor,
    get_or_create_language,
    check_duplicate_movie,
    get_movie_by_id,
    delete_movie, get_movies_list, patch_movie, get_or_create_country
)
from database import get_db, MovieModel
from schemas.movies import (
    MovieListResponseSchema,
    MovieCreateSchema,
    MovieCreateResponseSchema
)


router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def get_all_movies(
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=20)
):

    skip = (page - 1) * per_page
    limit = per_page

    movies_list = await get_movies_list(db=db, skip=skip, limit=limit)

    total_items = (await db.scalars(select(func.count()).select_from(MovieModel))).one()
    total_pages = math.ceil(total_items / per_page)

    if page > total_pages:
        raise HTTPException(status_code=404, detail="No movies found.")

    if page == 1:
        prev_page = None
    else:
        prev_page = f"/theater/movies/?page={page - 1}&per_page={per_page}"

    if page == total_pages:
        next_page = None
    else:
        next_page = f"/theater/movies/?page={page + 1}&per_page={per_page}"

    return {
        "movies": movies_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.post("/movies/", response_model=MovieCreateResponseSchema)
async def create_movie(movie: MovieCreateSchema, db: AsyncSession = Depends(get_db),):
    await check_duplicate_movie(movie_name=movie.name, movie_data=movie.date, db=db)

    country = await get_or_create_country(country_code=movie.country, db=db)


    genre_task = [
        get_or_create_genre(genre_name=genre, db=db) for genre in movie.genres
    ]
    genres = await asyncio.gather(*genre_task)

    actor_task = [
        get_or_create_actor(actor_name=actor, db=db) for actor in movie.actors
    ]
    actors = await asyncio.gather(*actor_task)

    language_task = [
        get_or_create_language(language_name=language, db=db) for language in movie.languages
    ]
    languages = await asyncio.gather(*language_task)

    db_movie = MovieModel(
        name=movie.name,
        date=movie.date,
        score=movie.score,
        overview=movie.overview,
        status=movie.status,
        budget=movie.budget,
        revenue=movie.revenue,
        country=country,
        genres=genres,
        actors=actors,
        languages=languages,
    )

    db.add(db_movie)
    await db.commit()
    stmt = select(MovieModel).where(MovieModel.id == db_movie.id).options(
        selectinload(MovieModel.country),
        selectinload(MovieModel.genres),
        selectinload(MovieModel.actors),
        selectinload(MovieModel.languages)
    )
    result = await db.execute(stmt)
    db_movie_eager = result.scalar_one()
    return db_movie_eager

@router.get("/movies/{movie_id}/", response_model=schemas.MovieDetailSchema)
async def get_movie_detail(id: int, db: AsyncSession = Depends(get_db)):
    return await get_movie_by_id(db=db, movie_id=id)


@router.delete("/movies/{movie_id}", status_code=204)
async def delete_movie_endpoint(movie_id: int, db: AsyncSession = Depends(get_db)):
    movie = await get_movie_by_id(movie_id=movie_id, db=db)
    await delete_movie(movie=movie, db=db)


@router.patch("/movies/{movie_id}/", response_model=schemas.MovieUpdateOutSchema)
async def patch_movie_endpoint(
    movie_id: int,
    movie: schemas.MovieUpdateInSchema,
    db: AsyncSession = Depends(get_db)

):
    db_movie = await get_movie_by_id(movie_id=movie_id, db=db)

    return await patch_movie(db_movie=db_movie, movie=movie, db=db)
