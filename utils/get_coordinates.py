from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

# Инициализация геокодера
geolocator = Nominatim(user_agent="my_telegram_bot")  # user_agent должен быть уникальным


def get_location_by_address(address):
    """
    Прямое геокодирование: получение координат по адресу.
    """
    try:
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return None
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return None
