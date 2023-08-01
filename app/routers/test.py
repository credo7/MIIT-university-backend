import math

import database
import models
from fastapi import APIRouter
from sqlalchemy.sql.expression import func
from utils import formatting_number as f

router = APIRouter(tags=['test'], prefix='/test')


@router.get('/practice2')
def practice_two():
    variant = database.session.query(models.PracticeTwoVariant).order_by(func.random()).first()
    bets = models.PracticeTwoVariantBet.to_json_list(variant.bets)

    unique_bets_by_to_and_from_fields = []
    unique_pairs = set()

    for bet in bets:
        pair = (bet['from'], bet['to'])
        if pair not in unique_pairs:
            unique_pairs.add(pair)
            unique_bets_by_to_and_from_fields.append(bet)

    for bet in unique_bets_by_to_and_from_fields:
        tons = bet['tons']
        package_tons = variant.package_tons
        bet['forty_containers_count'] = f'{tons}/(40*{package_tons})={int(tons / 40 * package_tons)}'
        bet['route'] = f'{bet["from"]} - {bet["to"]}'

    containers = models.Container.to_json_list(database.session.query(models.Container).all())

    container_first_table = []

    for c in containers:
        length = c['length']
        width = c['width']
        height = c['height']
        loading_volume = length * width * height
        package_length = variant.package_length
        package_width = variant.package_width
        package_height = variant.package_height
        transport_package_volume = package_length * package_width * package_height
        packages_in_container = math.ceil(
            math.floor(length / package_length)
            * math.floor(width / package_width)
            * math.floor(height / package_height)
        )
        size = c['size']
        payload_capacity = c['payload_capacity']

        container_first_table.append(
            {
                'type': f'{size}-футовый контейнер {length}м*{width}м*{height}м (Д*Ш*В), грузоподъёмность {payload_capacity}т',
                'loading_volume': f'{length}*{width}*{height}={f(loading_volume)}',
                'transport_package_volume': f'{package_length}*{package_width}*{package_height}={f(transport_package_volume)}',
                'packages_in_container': f'({length}/{package_length})*({width}/{package_width})*({height}/{package_height})={packages_in_container}',
                'capacity_utilization_rate': f'{f(packages_in_container)}*{f(transport_package_volume)}/{f(loading_volume)}={f(packages_in_container * transport_package_volume / loading_volume)}',
                'payload_utilization_rate': f'{packages_in_container}*{package_tons}/{payload_capacity}={f(packages_in_container * package_tons / payload_capacity)}',
            }
        )

    return {
        'legend': variant.legend,
        'bets': bets,
        'containers_one': container_first_table,
        'containers_two': unique_bets_by_to_and_from_fields,
    }
