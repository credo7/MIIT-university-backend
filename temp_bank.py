import math

from pydantic.main import BaseModel


def compare_containers(package_weight, package_length, package_width, package_height):
    # Container dimensions (in meters)
    length_20 = 5.9
    width_20 = 2.33
    height_20 = 2.35

    length_40 = 12.0
    width_40 = 2.33
    height_40 = 2.35

    # Container volumes (in cubic meters)
    volume_20 = round(length_20 * width_20 * height_20, 2)
    volume_40 = round(length_40 * width_40 * height_40, 2)

    # Package volume (in cubic meters)
    package_volume = package_length * package_width * package_height

    # Number of packages fitting into containers
    n_20 = math.floor(length_20 / package_length) * \
           math.floor(width_20 / package_width) * \
           math.floor(height_20 / package_height)

    n_40 = math.floor(length_40 / package_length) * \
           math.floor(width_40 / package_width) * \
           math.floor(height_40 / package_height)

    # Capacity Utilization
    cu_20 = (n_20 * package_volume) / volume_20
    cu_40 = (n_40 * package_volume) / volume_40

    # Load Utilization
    max_load_20 = 21.8  # in tons
    max_load_40 = 26.4  # in tons

    lu_20 = (n_20 * package_weight) / max_load_20
    lu_40 = (n_40 * package_weight) / max_load_40

    # Check if 40-foot container is better
    cu_better = cu_40 >= cu_20
    lu_better = lu_40 >= lu_20

    return cu_better and lu_better

weight_options = [
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9
]

class PackageSize(BaseModel):
    length: float
    width: float
    height: float

package_options = [
    PackageSize(
        length=0.8,
        width=1.2,
        height=0.8
    ),
    PackageSize(
        length=0.8,
        width=1.2,
        height=0.9
    ),
    PackageSize(
        length=0.8,
        width=1.2,
        height=1
    ),
    PackageSize(
        length=0.8,
        width=1.2,
        height=1.1
    ),
    PackageSize(
        length=1,
        width=1.2,
        height=1
    ),
    PackageSize(
        length=1,
        width=1.2,
        height=1.1
    ),
    PackageSize(
        length=1.1,
        width=1.1,
        height=1
    ),
    PackageSize(
        length=1.1,
        width=1.1,
        height=1.1
    ),
]

for p_option in package_options:
    for p_weight in weight_options:
        print(f"p_weight={p_weight}; p_option={p_option}; {compare_containers(p_weight, p_option.length, p_option.width, p_option.height)}")
