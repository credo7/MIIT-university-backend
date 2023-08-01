s = {
    'Китай - Польша': [
        {
            'full_route_name': 'Китай - Польша через Россия 3PL1',
            'bet': 4500,
            'amount': '4500*40=180000',
            'route_number': 1,
        },
        {'full_route_name': '3PL2', 'bet': 4800, 'amount': '4800*40=192000', 'route_number': 2},
        {
            'full_route_name': 'Китай - Польша через Монголия 3PL2',
            'bet': 4600,
            'amount': '4600*40=184000',
            'route_number': 3,
        },
        {'full_route_name': '3PL3', 'bet': 4800, 'amount': '4800*40=192000', 'route_number': 4},
        {
            'full_route_name': 'Китай - Польша через Казахстан 3PL1',
            'bet': 4500,
            'amount': '4500*40=180000',
            'route_number': 5,
        },
        {'full_route_name': '3PL3', 'bet': 4600, 'amount': '4600*40=184000', 'route_number': 6},
    ],
    'Япония - Германия': [
        {
            'full_route_name': 'Япония - Германия через морской торговый порт России 3PL1',
            'bet': 5000,
            'amount': '5000*20=100000',
            'route_number': 7,
        },
        {'full_route_name': '3PL2', 'bet': 4800, 'amount': '4800*20=96000', 'route_number': 8},
        {'full_route_name': '3PL3', 'bet': 4900, 'amount': '4900*20=98000', 'route_number': 9},
    ],
    'Япония - Нидерланды': [
        {
            'full_route_name': 'Япония - Нидерланды через морской торговый порт России 3PL1',
            'bet': 5000,
            'amount': '5000*25=125000',
            'route_number': 10,
        },
        {'full_route_name': '3PL2', 'bet': 4900, 'amount': '4900*25=122500', 'route_number': 11},
        {'full_route_name': '3PL3', 'bet': 5000, 'amount': '5000*25=125000', 'route_number': 12},
    ],
    'Корея - Польша': [
        {
            'full_route_name': 'Корея - Польша через морской торговый порт России 3PL1',
            'bet': 4800,
            'amount': '4800*25=120000',
            'route_number': 13,
        },
        {'full_route_name': '3PL2', 'bet': 4700, 'amount': '4700*25=117500', 'route_number': 14},
        {'full_route_name': '3PL3', 'bet': 4800, 'amount': '4800*25=120000', 'route_number': 15},
    ],
    'Корея - Чехия': [
        {
            'full_route_name': 'Корея - Чехия через морской торговый порт России 3PL1',
            'bet': 4900,
            'amount': '4900*15=73500',
            'route_number': 16,
        },
        {'full_route_name': '3PL2', 'bet': 4800, 'amount': '4800*15=72000', 'route_number': 17},
        {'full_route_name': '3PL3', 'bet': 4900, 'amount': '4900*15=73500', 'route_number': 18},
    ],
}


def find_option(PL_name, variant_num, bets_calculations):
    stack = []
    for val in bets_calculations.values():
        count = 0
        last_row = None
        for dic in val:
            variant_num
            if PL_name in dic['full_route_name']:
                count += 1
                if variant_num == count:
                    stack.append(
                        {'route_number': dic['route_number'], 'amount': dic.get('containers_num', 1) * dic['bet']}
                    )
                    break
                last_row = {'route_number': dic['route_number'], 'amount': dic.get('containers_num', 1) * dic['bet']}
        if count < variant_num:
            stack.append(last_row)

    amount = sum(route['amount'] for route in stack)
    route_numbers = [str(route['route_number']) for route in stack]

    return f"{amount}: {'-'.join(route_numbers)}"


def find_optimal_option(bets_calculations, variant_num):
    stack = []
    for val in bets_calculations.values():
        curr_minimal_num = float('inf')
        curr_minimal = None
        for dic in val:
            if curr_minimal_num > dic['bet']:
                curr_minimal_num = dic['bet']
                curr_minimal = {
                    'route_number': dic['route_number'],
                    'amount': dic.get('containers_num', 1) * dic['bet'],
                }
            if variant_num == 2 and curr_minimal_num == dic['bet']:
                curr_minimal = {
                    'route_number': dic['route_number'],
                    'amount': dic.get('containers_num', 1) * dic['bet'],
                }
        stack.append(curr_minimal)

    amount = sum(route['amount'] for route in stack)
    route_numbers = [str(route['route_number']) for route in stack]

    return f"{amount}: {'-'.join(route_numbers)}"


def overall_calculations():
    optimal_solution1 = find_optimal_option(bets_calculations=s, variant_num=1)
    optimal_solution2 = find_optimal_option(bets_calculations=s, variant_num=2)

    PL1_variant1 = find_option(PL_name='PL1', variant_num=1, bets_calculations=s)
    PL1_variant2 = find_option(PL_name='PL1', variant_num=2, bets_calculations=s)

    PL2_variant1 = find_option(PL_name='PL2', variant_num=1, bets_calculations=s)
    PL2_variant2 = find_option(PL_name='PL2', variant_num=2, bets_calculations=s)

    PL3_variant1 = find_option(PL_name='PL3', variant_num=1, bets_calculations=s)
    PL3_variant2 = find_option(PL_name='PL3', variant_num=2, bets_calculations=s)

    return {
        '3PL1': {'first': PL1_variant1, 'second': PL1_variant2},
        '3PL2': {'first': PL2_variant1, 'second': PL2_variant2},
        '3PL3': {'first': PL3_variant1, 'second': PL3_variant2},
        'optimal': {'first': optimal_solution1, 'second': optimal_solution2},
    }


if __name__ == '__main__':
    print(overall_calculations())
