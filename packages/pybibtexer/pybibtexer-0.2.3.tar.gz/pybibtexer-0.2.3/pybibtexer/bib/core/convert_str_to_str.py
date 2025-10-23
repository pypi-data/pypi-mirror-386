from typing import Any, Dict, List, Tuple

from ..bibtexbase import StandardizeBib
from ..bibtexparser import MiddlewaresStrToStr


class ConvertStrToStr(object):
    """Convert str to str.

    Args:
        options (Dict[str, Any]): Options. Default is {}.

    Attributes:
        default_additional_field_list (List[str]): Default additional field list. Default is [].
    """

    def __init__(self, options: Dict[str, Any] = {}) -> None:

        self.default_additional_field_list = options.get("default_additional_field_list", [])

        self.options = options

    def generate_str(self, data_list: List[str]) -> Tuple[List[str], List[List[str]]]:
        data_list, implicit_comment_list = StandardizeBib(self.default_additional_field_list).standardize(data_list)

        data_list = MiddlewaresStrToStr(self.options).functions(data_list)
        return data_list, implicit_comment_list
