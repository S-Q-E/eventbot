# from geopy.geocoders import GoogleV3
# from geopy.exc import GeocoderServiceError
#
# import logging
#
# logger = logging.Logger(__name__)
#
# GOOGLE_KEY = ""
# # geolocator = GoogleV3(api_key=GOOGLE_KEY, timeout=10)
#
#
# def get_coordinates(address):
#     """
#     Получаем адрес и возвращаем координаты.
#     :param address: str
#     :return: latitude, longitude
#     """
#     try:
#         location = geolocator.geocode(address, timeout=10)
#         if location:
#             return location.latitude, location.longitude
#         else:
#             return None, None
#     except GeocoderServiceError as ex:
#         logger.error(f"Ошибка при получений координат {ex}")
#         return None, None