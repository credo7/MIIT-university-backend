import random
import time

start_time = time.time()

random_start = random.randint(20, 85)

def is_valid(groups):
    nums1, nums2, nums3, nums4 = set(), set(), set(), set()
    min1, min2, min3 = float('inf'), float('inf'), float('inf')

    for i in range(4):
        if groups[i][0] is not None and groups[i][0] < min1:
            min1 = groups[i][0]
        if groups[i][1] is not None and groups[i][1] < min2:
            min2 = groups[i][1]
        if groups[i][2] is not None and groups[i][2] < min3:
            min3 = groups[i][2]

    min_combo = min(min1, min2, min3)
    nums1.add(min1)
    nums2.add(min2)
    nums3.add(min3)
    nums4.add(min_combo)

    # Process remaining groups
    for group in groups[4:]:
        nums1.add(group[0])
        nums2.add(group[1])
        nums3.add(group[2])
        nums4.add(min(filter(None, group)))  # Ignore None values

    if len(nums1) == 5 and len(nums2) == 5 and len(nums3) == 5 and len(nums4) == 5:
        return True

    return False

all_3pls = None

for i in range(30000):
    all_random_3pls_grouped = []

    for _ in range(8):
        pls = random.sample(range(random_start * 100, (random_start + 15) * 100, 100), 3)
        all_random_3pls_grouped.append(pls)

    for i in range(4):
        random_index_for_none = random.randint(0, 2)
        all_random_3pls_grouped[i][random_index_for_none] = None

    if is_valid(all_random_3pls_grouped):
        all_3pls = all_random_3pls_grouped
        break




print(f"counter= {counter}")
print(f"time_spent = {time.time() - start_time}")