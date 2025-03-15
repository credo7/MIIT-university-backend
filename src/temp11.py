import random

from constants.pr2_class_info import pr2_class_info


def get_point_by_city_name(city: str):
    for point in pr2_class_info.all_points:
        if point.city == city:
            return point
    raise Exception('Точка не найдена')


routes_city_names = set()
routes_city_codes = set()
routes_quantity_by_route = {}

for i in range(100000):
    all_destination_countries = ['Польша', 'Германия', 'Франция', 'Нидерланды', 'Бельгия', 'Чехия', 'Австрия']
    random.shuffle(all_destination_countries)
    random_destination_country_for_china = all_destination_countries[0]
    random_destination_countries_for_japan = all_destination_countries[1:3]
    random_destination_countries_for_south_korea = all_destination_countries[3:5]
    random_city_from_for_china = random.choice(['Шицзячжуан', 'Цзинань', 'Иу', 'Баодин'])
    random_city_from_for_japan = random.choice(['Киото', 'Аябе', 'Асаго', 'Мацумото'])
    random_city_from_for_south_korea = random.choice(['Сувон', 'Тэджон', 'Чханвон', 'Кванджу'])

    destination_cities_by_destination_country = {
        'Польша': ['Острава', 'Лодзь'],
        'Германия': ['Лейпциг', 'Аугсбург'],
        'Франция': ['Руан', 'Лион'],
        'Нидерланды': ['Утрехт', 'Харлем'],
        'Бельгия': ['Лёвен', 'Гент'],
        'Чехия': ['Пардубице', 'Пльзень'],
        'Австрия': ['Линц', 'Санкт-Пёльтен'],
    }

    random_destination_city_for_china = random.choice(
        destination_cities_by_destination_country[random_destination_country_for_china]
    )

    random_destination_cities_for_japan = [
        random.choice(destination_cities_by_destination_country[random_destination_countries_for_japan[0]]),
        random.choice(destination_cities_by_destination_country[random_destination_countries_for_japan[1]]),
    ]

    random_destination_cities_for_south_korea = [
        random.choice(destination_cities_by_destination_country[random_destination_countries_for_south_korea[0]]),
        random.choice(destination_cities_by_destination_country[random_destination_countries_for_south_korea[1]]),
    ]

    dynamic_borders = ['Достык', 'Алтынколь']
    chosen_dynamic_border = random.choice(dynamic_borders)

    random_china_port = random.choice(['Гуанчжоу', 'Нинбо', 'Чунцин', 'Циндао'])
    random_japan_port = random.choice(['Акита', 'Йокогама', 'Кобе', 'Нагоя'])
    random_south_korea_port = random.choice(['Пусан', 'Инчон'])
    random_russia_port = random.choice(['Владивосток', 'Восточный'])

    china_route_1_points = [
        get_point_by_city_name(random_city_from_for_china),
        get_point_by_city_name('Забайкальск'),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_city_for_china),
    ]

    china_route_2_points = [
        get_point_by_city_name(random_city_from_for_china),
        get_point_by_city_name('Наушки'),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_city_for_china),
    ]

    china_route_3_points = [
        get_point_by_city_name(random_city_from_for_china),
        get_point_by_city_name(chosen_dynamic_border),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_city_for_china),
    ]

    china_route_4_points = [
        get_point_by_city_name(random_city_from_for_china),
        get_point_by_city_name(random_china_port),
        get_point_by_city_name(random_russia_port),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_city_for_china),
    ]

    japan_route_1_points = [
        get_point_by_city_name(random_city_from_for_japan),
        get_point_by_city_name(random_japan_port),
        get_point_by_city_name(random_russia_port),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_cities_for_japan[0]),
    ]

    japan_route_2_points = [
        get_point_by_city_name(random_city_from_for_japan),
        get_point_by_city_name(random_japan_port),
        get_point_by_city_name(random_russia_port),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_cities_for_japan[1]),
    ]

    korea_route_1_points = [
        get_point_by_city_name(random_city_from_for_south_korea),
        get_point_by_city_name(random_south_korea_port),
        get_point_by_city_name(random_russia_port),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_cities_for_south_korea[0]),
    ]

    korea_route_2_points = [
        get_point_by_city_name(random_city_from_for_south_korea),
        get_point_by_city_name(random_south_korea_port),
        get_point_by_city_name(random_russia_port),
        get_point_by_city_name('Брест'),
        get_point_by_city_name(random_destination_cities_for_south_korea[1]),
    ]

    all_routes = [
        china_route_1_points,
        china_route_2_points,
        china_route_3_points,
        china_route_4_points,
        japan_route_1_points,
        japan_route_2_points,
        korea_route_1_points,
        korea_route_2_points,
    ]

    for r in all_routes:
        city_route = ' - '.join([p.city for p in r])
        routes_city_names.add(' - '.join([p.city for p in r]))
        routes_city_codes.add(' - '.join([p.code for p in r]))
        if city_route not in routes_quantity_by_route:
            routes_quantity_by_route[city_route] = 1
        else:
            routes_quantity_by_route[city_route] += 1

print(routes_quantity_by_route)
print(f'min = {min(list(routes_quantity_by_route.values()))}')
print(f'len = {len(routes_quantity_by_route)}')

breaks_names = set()
breaks_codes = set()

for r in routes_city_names:
    points_names = r.split(' - ')
    for i in range(len(points_names) - 1):
        breaks_names.add(f'{points_names[i]} - {points_names[i+1]}')

for r in routes_city_codes:
    points_codes = r.split(' - ')
    for i in range(len(points_codes) - 1):
        breaks_codes.add(f'{points_codes[i]} - {points_codes[i+1]}')

print(f'count breaks_names={len(breaks_names)}')
print(f'count breaks_codes={len(breaks_codes)}')

with open('segments_names.txt', 'w', encoding='utf-8') as file:
    for string in breaks_names:
        file.write(string + '\n')

with open('segments_codes.txt', 'w', encoding='utf-8') as file:
    for string in breaks_codes:
        file.write(string + '\n')
