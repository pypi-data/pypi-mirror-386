from __future__ import annotations # Delays annotation evaluation, allowing modern 3.10+ type syntax and forward references in older Python versions 3.8 and 3.9
import logging
import inspect
from functools import wraps


def log_function_call(level=logging.DEBUG):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__qualname__
            logging.log(level, f"Start: {func_name}() args={args} kwargs={kwargs}")
            return func(*args, **kwargs)
        return wrapper
    return decorator
