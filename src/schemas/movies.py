import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator
from database.models import MovieStatusEnum


class MovieListItemSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str

    class Config:
        model_config = ConfigDict(from_attributes = True)


class MovieListResponseSchema(BaseModel):
    movies: list[MovieListItemSchema]
    prev_page: str | None
    next_page: str | None
    total_pages: int
    total_items: int


class CountryInSchema(BaseModel):
    code: str
    name: str | None


class CountryOutSchema(CountryInSchema):
    id: int


class GenreInSchema(BaseModel):
    name: str


class GenreOutSchema(GenreInSchema):
    id: int


class ActorInSchema(BaseModel):
    name: str


class ActorOutSchema(ActorInSchema):
    id: int


class LanguageInSchema(BaseModel):
    name: str


class LanguageOutSchema(LanguageInSchema):
    id: int


class MovieCreateSchema(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    date: datetime.date

    @field_validator("date")
    @classmethod
    def validate(cls, value: datetime.date) -> datetime.date:
        if value > datetime.date.today() + datetime.timedelta(days=365):
            raise ValueError("Date must not be more than one year in the future")
        return value

    score: float = Field(default=0, ge=0, le=100)
    overview: str
    status: MovieStatusEnum
    budget: float = Field(ge=0)
    revenue: float = Field(ge=0)
    country: str
    genres: list[str]
    actors: list[str]
    languages: list[str]


class MovieCreateResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime.date
    score: float
    overview: str
    status: MovieStatusEnum
    budget: float
    revenue: float
    country: CountryOutSchema
    genres: list[GenreOutSchema]
    actors: list[ActorOutSchema]
    languages: list[LanguageOutSchema]


class MovieDetailSchema(MovieCreateResponseSchema):
    pass


class MovieUpdateInSchema(BaseModel):
    name: str
    date: datetime.date | None
    score: float | None
    overview: str | None
    status: MovieStatusEnum | None
    budget: float | None
    revenue: float | None


class MovieUpdateOutSchema(MovieUpdateInSchema):
    pass
