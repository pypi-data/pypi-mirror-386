from typing import List

from .middleware import Middleware


def default_parse_stack(allow_inplace_modification: bool = True) -> List[Middleware]:
    """Give the default parse stack to be applied after splitting, if not specified otherwise."""
    return []


def default_unparse_stack(allow_inplace_modification: bool = False) -> List[Middleware]:
    """Give the default unparse stack to be applied before writing, if not specified otherwise."""
    return []
