import random
import time

start_time = time.time()

random_start = random.randint(20, 85)

def is_valid(rows):
    # 1. Не должно быть одинаковых чисел в одной строчке (для всех маршрутов)
    for row in rows:
        nums_without_nones = [num for num in row if num is not None]
        if len(set(nums_without_nones)) != len(nums_without_nones):
            return False

    # 2. Не должно быть одинаковых чисел в одном столбце для первых 4 маршрутов
    pl1_nums = []
    pl2_nums = []
    pl3_nums = []
    for row in rows[:4]:
        if row[0] is not None:
            pl1_nums.append(row[0])
        if row[1] is not None:
            pl2_nums.append(row[1])
        if row[2] is not None:
            pl3_nums.append(row[2])
    if len(pl1_nums) == 0 or len(pl2_nums) == 0 or len(pl3_nums) == 0:
        return False
    all_nums = pl1_nums + pl2_nums + pl3_nums
    min_num_in_combo = min(all_nums)
    if all_nums.count(min_num_in_combo) > 1 or len(pl1_nums) != len(set(pl1_nums)) or len(pl2_nums) != len(set(pl2_nums)) or len(pl3_nums) != len(set(pl3_nums)):
        return False

    pl1_nums_2 = []
    pl2_nums_2 = []
    pl3_nums_2 = []
    for row in rows:
        if row[0] is not None:
            pl1_nums_2.append(row[0])
        if row[1] is not None:
            pl2_nums_2.append(row[1])
        if row[2] is not None:
            pl3_nums_2.append(row[2])

    if len(pl1_nums_2) != len(set(pl1_nums_2)) or len(pl2_nums_2) != len(set(pl2_nums_2)) or len(pl3_nums_2) != len(set(pl3_nums_2)):
        return False

    pl1_result = min(pl1_nums) + rows[4][0] + rows[5][0] + rows[6][0] + rows[7][0]
    pl2_result = min(pl2_nums) + rows[4][1] + rows[5][1] + rows[6][1] + rows[7][1]
    pl3_result = min(pl3_nums) + rows[4][2] + rows[5][2] + rows[6][2] + rows[7][2]

    if len(set([pl1_result, pl2_result, pl3_result])) != 3:
        return False

    return True

all_3pls = None

counter = 0
counter2 = [0]

# for i in range(1):
for j in range(100000):
    all_random_3pls_grouped = []

    for _ in range(8):
        pls = random.sample(range(random_start * 100, (random_start + 15) * 100, 100), 3)
        all_random_3pls_grouped.append(pls)

    for i in range(4):
        random_index_for_none = random.randint(0, 2)
        all_random_3pls_grouped[i][random_index_for_none] = None


    if is_valid(all_random_3pls_grouped):
        all_3pls = all_random_3pls_grouped
        # for row in all_random_3pls_grouped:
        #     print(row)
        # break
        counter += 1
        # print()
        # if counter >= 15:
        #     break




print(f"counter= {counter}")
print(f"counter2= {counter2[0]}")
print(f"time_spent = {time.time() - start_time}")