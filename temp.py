from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel


class ReservationStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELED = "CANCELED"


class UserRole(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    HOSTESS = "HOSTESS"


class Theme(str, Enum):
    LIGHT = "LIGHT"
    DARK = "DARK"


class UserRestaurant(BaseModel):
    restaurant_id: str
    role: UserRole


class UserSettings(BaseModel):
    theme: Optional[Theme] = Theme.DARK


class User(BaseModel):
    first_name: str
    number: str
    old_numbers: List[str] = []
    telegram_id: Optional[str] = None
    whatsapp: Optional[str] = None
    restaurants: UserRestaurant
    settings: UserSettings


class RestaurantUser(BaseModel):
    user_id: str
    role: UserRole


class TimePeriod(BaseModel):
    start_time: datetime
    end_time: datetime


class WeekDay(str, Enum):
    MONDAY = "MONDAY"
    # TODO: дописать отсальные days


class Canvas(BaseModel): # решим чуть позже
    ...



class RestaurantSettings(BaseModel):
    schedule: dict[WeekDay, TimePeriod]
    future_reservation_days: int = 31
    end_reservation_notification_minutes: int = 15
    max_reservation_time_hours: int = 5
    # Бронирование по факту
    fact_time_reservation_hours: Optional[int]
    automatic_table_opening: Optional[bool] = False
    automatic_table_closing: Optional[bool] = False
    banned_time_periods: dict[WeekDay, list[TimePeriod]]


class Restaurant(BaseModel):
    name: str
    city: str
    is_active: bool = False
    number: str
    address: str
    users: list[RestaurantUser]
    photo_urls: List[str]
    canvas: Optional[Canvas] = None
    settings: RestaurantSettings


class Reservation(BaseModel):
    user_id: str
    restaurant_id: str
    start_time: datetime
    end_time: datetime
    table_number: int
    comment: Optional[str] = None
    status: ReservationStatus
    guests_count: int
