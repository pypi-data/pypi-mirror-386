from pydantic import BaseModel, Field
from typing import List, Optional

class WeatherDesc(BaseModel):
    id: int
    main: str
    description: str
    icon: str

class MainBlock(BaseModel):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int

class Wind(BaseModel):
    speed: float
    deg: int
    gust: Optional[float] = None

class Sys(BaseModel):
    country: Optional[str] = None

class CurrentWeather(BaseModel):
    name: str
    weather: List[WeatherDesc]
    main: MainBlock
    wind: Wind
    sys: Sys

class ForecastItem(BaseModel):
    dt: int
    main: MainBlock
    weather: List[WeatherDesc]
    wind: Wind
    dt_txt: Optional[str] = None

class City(BaseModel):
    id: int
    name: str
    country: str

class Forecast(BaseModel):
    cod: str
    cnt: int
    list: List[ForecastItem] = Field(default_factory=list)
    city: City