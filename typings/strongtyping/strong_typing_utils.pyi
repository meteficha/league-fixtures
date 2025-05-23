"""
This type stub file was generated by pyright.
"""

import typing
from functools import lru_cache
from typing import Any

"""
@created: 19.11.20
@author: felix
"""
empty = ...
default_return_queue = ...
class TypeMisMatch(AttributeError):
    def __init__(self, message, failed_params=..., param_values=..., annotations=...) -> None:
        ...
    


class ValidationError(Exception):
    def __init__(self, message) -> None:
        ...
    


class UndefinedKey(Exception):
    def __init__(self, message) -> None:
        ...
    


typing_base_class = ...
@lru_cache(maxsize=1024)
def get_possible_types(typ_to_check, origin_name: str = ...) -> typing.Union[tuple, None]:
    """
    :param typ_to_check: some typing like List[str], Dict[str, int], Tuple[Union[str, int], List[int]]
    :param origin_name: the name of the origin
    :return: the inner types, classes of the type
        - List[str] = (str, )
        - Dict[str, int] = (str, int, )
        - Tuple[Union[str, int], List[int]] = (Union[str, int], List[int], )
    """
    ...

def get_origins(typ_to_check: Any) -> tuple:
    ...

def checking_typing_dict(arg: Any, possible_types: tuple, *args): # -> bool:
    ...

def checking_typing_set(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def checking_typing_type(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def checking_typing_union(arg: Any, possible_types: tuple, mro, **kwargs): # -> bool:
    ...

def checking_typing_optional(arg: Any, possible_types: tuple, mro, **kwargs): # -> Literal[True]:
    ...

def checking_typing_iterator(arg: Any, *args, **kwargs): # -> bool:
    ...

def checking_typing_callable(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def checking_typing_tuple(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def checking_typing_list(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def checking_ellipsis(arg, possible_types, *args, **kwargs): # -> bool:
    ...

def checking_typing_json(arg, possible_types, *args, **kwargs): # -> bool:
    ...

def checking_typing_generator(arg, possible_types, *args, **kwargs): # -> bool:
    ...

def checking_typing_literal(arg, possible_types, *args, **kwargs): # -> bool:
    ...

def checking_typing_validator(arg, possible_types, *args, **kwargs): # -> bool | None:
    ...

def checking_typing_itervalidator(arg, possible_types, *args, **kwargs):
    ...

def checking_typing_iterable(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def checking_typing_typedict_values(args: dict, required_types: dict, total: bool): # -> bool:
    ...

def checking_typing_class(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def checking_typing_typeddict(arg: Any, possible_types: Any, *args, **kwargs): # -> bool:
    ...

def checking_typing_typeddict_required(arg: Any, possible_types: Any, *args, **kwargs):
    ...

def checking_typing_typeddict_notrequired(arg: Any, possible_types: Any, *args, **kwargs): # -> Literal[True]:
    ...

def checking_typing_unpack(arg: Any, possible_types: tuple, *args, **kwargs): # -> bool:
    ...

def module_checking_typing_list(arg: Any, possible_types: Any): # -> bool:
    ...

def module_checking_typing_dict(arg: Any, possible_types: Any): # -> bool:
    ...

def module_checking_typing_set(arg: Any, possible_types: Any): # -> bool:
    ...

def module_checking_typing_tuple(arg: Any, possible_types: Any): # -> bool:
    ...

def module_checking_typing_validator(arg, possible_types, *args, **kwargs):
    ...

def validate_object(value, validation_func=...): # -> Literal[True]:
    ...

def check_duck_typing(arg, possible_types, *args, **kwargs): # -> bool:
    ...

supported_typings = ...
def check_type(argument, type_of, mro=..., **kwargs):
    ...

