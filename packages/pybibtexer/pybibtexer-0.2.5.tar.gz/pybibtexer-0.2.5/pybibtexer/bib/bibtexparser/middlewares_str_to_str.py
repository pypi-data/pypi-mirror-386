import re
from typing import Any, Dict, List


class MiddlewaresStrToStr(object):
    r"""Middlewares for converting a string to a string.

    Args:
        options (dict): Options for the middlewares.

    Attributes:
        substitute_in_bib (bool): Substitute in the bib. Default is True.
        substitute_old_list (list): List of old strings to substitute. Default is [].
        substitute_new_list (list): List of new strings to substitute. Default is [].
    """

    def __init__(self, options: Dict[str, Any]):
        self.substitute_in_bib = options.get("substitute_in_bib", True)
        self.substitute_old_list = options.get("substitute_old_list", [])
        self.substitute_new_list = options.get("substitute_new_list", [])

    def functions(self, data_list: List[str]) -> List[str]:
        # Substitute
        if self.substitute_in_bib:
            for i in range(len(data_list)):
                for old, new in zip(self.substitute_old_list, self.substitute_new_list):
                    data_list[i] = re.sub(old, new, data_list[i])

        return data_list
