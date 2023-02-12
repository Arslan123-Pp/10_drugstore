from io import BytesIO
from PIL import Image
import math
import requests
import sys


def lonlat_distance(a, b):
    degree_to_meters_factor = 111 * 1000
    a_lon, a_lat = a
    b_lon, b_lat = b
    radians_lattitude = math.radians((a_lat + b_lat) / 2)
    lat_lon_factor = math.cos(radians_lattitude)
    dx = abs(a_lon - b_lon) * degree_to_meters_factor * lat_lon_factor
    dy = abs(a_lat - b_lat) * degree_to_meters_factor
    distance = math.sqrt(dx * dx + dy * dy)
    return distance


def get_spn_org(json_response, i1, i2):
    try:
        organization = json_response["features"][i1]
        point1 = organization["geometry"]["coordinates"]
        organization = json_response["features"][i2]
        point2 = organization["geometry"]["coordinates"]
        x = str(abs(point1[0] - point2[0]) + 0.05)
        y = str(abs(point1[1] - point2[1]) + 0.05)
        return [x, y]
    except Exception:
        return ['1', '1']


search_api_server = "https://search-maps.yandex.ru/v1/"
geocoder_api_server = "http://geocode-maps.yandex.ru/1.x/"
api_key = "dda3ddba-c9ea-4ead-9010-f43fbc15c6e3"

toponym_to_find = " ".join(sys.argv[1:])
geocoder_params = {
    "apikey": "40d1649f-0493-4b70-98ba-98533de7710b",
    "geocode": toponym_to_find,
    "format": "json"}

response = requests.get(geocoder_api_server, params=geocoder_params)

if not response:
    # обработка ошибочной ситуации
    pass

# Преобразуем ответ в json-объект
json_response = response.json()

# Получаем первый топоним из ответа геокодера.
toponym = json_response["response"]["GeoObjectCollection"][
    "featureMember"][0]["GeoObject"]
# Координаты центра топонима:
toponym_coodrinates = toponym["Point"]["pos"]
# Долгота и широта:
toponym_longitude, toponym_lattitude = toponym_coodrinates.split(" ")
address_ll = f'{toponym_longitude},{toponym_lattitude}'


search_params = {
    "apikey": api_key,
    "text": "аптека",
    "lang": "ru_RU",
    "ll": address_ll,
    "type": "biz"
}

response = requests.get(search_api_server, params=search_params)

if not response:
    pass
json_response = response.json()
lst_points = []
# Получаем первую найденную организацию.
mndst, mxdst = 10 ** 20, 0
x, y = 0, 0
for i in range(10):
    organization = json_response["features"][i]
    # Название организации.
    org_name = organization["properties"]["CompanyMetaData"]["name"]
    # Адрес организации.
    org_address = organization["properties"]["CompanyMetaData"]["address"]
    # Получаем координаты ответа.
    point = organization["geometry"]["coordinates"]
    org_point = "{0},{1}".format(point[0], point[1])
    try:
        work_time = json_response['features'][i]["properties"]["CompanyMetaData"]['Hours']['text']
        if 'круглосуточ' in work_time:
            lst_points.append(f'{org_point},pm2dgl')
        else:
            lst_points.append(f'{org_point},pm2dbl')
    except Exception:
        lst_points.append(f'{org_point},pm2grl')
    dst = lonlat_distance(list(map(float, org_point.split(','))), list(map(float, address_ll.split(','))))
    if dst > mxdst:
        mxdst = dst
        x = i
    if dst > mndst:
        mndst = dst
        y = i
crd = get_spn_org(json_response, x, y)
# Собираем параметры для запроса к StaticMapsAPI:
map_params = {
    # позиционируем карту центром на наш исходный адрес
    "ll": address_ll,
    "spn": ",".join(crd),
    "l": "map",
    # добавим точку, чтобы указать найденную аптеку
    "pt": '~'.join(lst_points)
}
map_api_server = "http://static-maps.yandex.ru/1.x/"
# ... и выполняем запрос
response = requests.get(map_api_server, params=map_params)
Image.open(BytesIO(
    response.content)).show()