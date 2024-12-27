from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

geolocator = Nominatim(user_agent="my_telegram_bot")


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


def get_address_by_coordinates(latitude, longitude):
    """
    Обратное геокодирование: получение адреса по координатам.
    """
    try:
        location = geolocator.reverse((latitude, longitude), exactly_one=True)
        if location:
            return location.address
        else:
            return None
    except (GeocoderTimedOut, GeocoderServiceError):
        return None
