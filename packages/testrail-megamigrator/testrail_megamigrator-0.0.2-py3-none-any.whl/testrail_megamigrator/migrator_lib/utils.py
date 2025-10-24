
import json
from contextlib import contextmanager
from datetime import datetime
from typing import Any


def back_up(dict_to_backup, path, name):
    with open(f'{path}/{name}{datetime.now()}.json', 'w') as file:
        file.write(json.dumps(dict_to_backup, indent=2))


@contextmanager
def timer(function_name: str):
    start_time = datetime.now()
    yield
    print(f'{function_name} took: ', datetime.now() - start_time)


def split_list_by_chunks(src_list: list, chunk_size: int = 40):
    return [src_list[x:x + chunk_size] for x in range(0, len(src_list), chunk_size)]


def find_idx_by_key_value(key: str, value: Any, src_list: list):
    for idx, elem in enumerate(src_list):
        if elem[key] == value:
            return idx


@contextmanager
def suppress_auto_now(model, field_names):
    """
    Suppress auto_now and auto_now_add options in model fields.

    Function is not supposed to be used inside Django app, may cause breaking of auto fields. Not supposed to be used
    in views/forms/serializers etc.

    Args:
        model: Model class
        field_names: name of fields with auto content
    """
    fields_state = {}
    for field_name in field_names:
        field = model._meta.get_field(field_name)
        fields_state[field] = {'auto_now': field.auto_now, 'auto_now_add': field.auto_now_add}

    for field in fields_state:
        field.auto_now = False
        field.auto_now_add = False
    try:
        yield
    finally:
        for field, state in fields_state.items():
            field.auto_now = state['auto_now']
            field.auto_now_add = state['auto_now_add']
