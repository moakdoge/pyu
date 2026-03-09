UNITS = {
    "B": 1,
    "KiB": 1024,
    "MiB": 1024**2,
    "GiB": 1024**3,
    "TiB": 1024**4,
    "PiB": 1024**5,
}

def num_to_unit(num: int):
    units = list(UNITS.items())

    for i in range(len(units) - 1):
        name, size = units[i]
        next_size = units[i + 1][1]

        if num < next_size:
            value = num / size
            return f"{value:.2f} {name}"

    name, size = units[-1]
    return f"{num / size:.2f} {name}"


def unit_to_num(s: str) -> int:
    import re
    m = re.fullmatch(r"\s*([\d.]+)\s*([A-Za-z]+)\s*", s)
    if not m:
        raise ValueError("Invalid size format")

    value = float(m.group(1))
    unit = m.group(2)

    if unit not in UNITS:
        raise ValueError(f"Unknown unit: {unit}")

    return int(value * UNITS[unit])