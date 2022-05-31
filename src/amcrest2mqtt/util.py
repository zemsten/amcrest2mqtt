import functools


@functools.lru_cache()
def to_gb(total) -> str:
    return str(round(float(total[0]) / 1024 / 1024 / 1024, 2))
