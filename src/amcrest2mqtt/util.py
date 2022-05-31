import functools


@functools.lru_cache()
def to_gb(total: float) -> str:
    return str(round(total / 1024 / 1024 / 1024, 2))
