#!/usr/bin/env python3

import gc
from typing import Type
import os
import warnings
import functools
import time

from lxml import etree as ET
import psutil
from sqlalchemy.ext.declarative import DeclarativeMeta as DeclarativeBase
from sqlalchemy.inspection import inspect


@functools.lru_cache(maxsize=10)
def get_sub_elements(parent_element: ET._Element, tag_name: str) -> list[ET._Element]:
    return parent_element.findall(tag_name)


def log_memory(msg=""):
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / (1024 * 1024)
    print(f"{msg} Memory: {memory_mb:.2f} MB")
    return memory_mb


def time_execution(message: str):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            elapsed_time = end_time - start_time
            print(f"{message} executed in {elapsed_time:.6f} seconds")
            return result

        return wrapper

    return decorator


#
# Currently not used
#


def check_cpu_utilization(threshold=90):
    cpu_usages = psutil.cpu_percent(percpu=True)
    for i, cpu_usage in enumerate(cpu_usages):
        if cpu_usage > threshold:
            warnings.warn(f"CPU core {i} usage is {cpu_usage}%")


def check_memory_utilization(threshold=90):
    memory_usage = psutil.virtual_memory().percent
    if memory_usage > threshold:
        warnings.warn(f"Memory usage is {memory_usage}%")


def get_instance_attributes(instance: DeclarativeBase, model_class: Type[DeclarativeBase]) -> dict[str, str]:
    """
    Return instance attributes with the exception of the primary key and any relationships.
    """
    primary_key_column = inspect(model_class).primary_key[0].key  # type: ignore
    instance_attrs = {c.key: getattr(instance, c.key) for c in inspect(instance).mapper.column_attrs}
    instance_attrs.pop(primary_key_column, None)
    return instance_attrs

def force_memory_cleanup():
    """
    Force aggressive memory cleanup
    """
    before_count = len(gc.get_objects())
    for i in range(3):
        gc.collect()
    after_count = len(gc.get_objects())
    print(f"Garbage collection: removed {before_count - after_count} objects")
    return log_memory("After forced cleanup:")
