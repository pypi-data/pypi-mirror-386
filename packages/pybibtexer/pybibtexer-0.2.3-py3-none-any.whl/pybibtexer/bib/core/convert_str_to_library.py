from typing import Any, Dict, List

from ..bibtexparser import Library, MiddlewaresStrToLibrary, Splitter
from .convert_str_to_str import ConvertStrToStr


class ConvertStrToLibrary(object):
    """Convert str to library.

    Args:
        options (Dict[str, Any]): Options. Default is {}.

    Attributes:
        is_standardize_bib (bool): Is standardize bib. Default is True.
    """

    def __init__(self, options: Dict[str, Any] = {}) -> None:

        self.is_standardize_bib = options.get("is_standardize_bib", True)

        self.options = options

    def generate_library(self, data_list: List[str]) -> Library:
        implicit_coments = []
        # standardizer
        if self.is_standardize_bib:
            data_list, implicit_coments = ConvertStrToStr(self.options).generate_str(data_list)

        # splitter
        library = Splitter().splitter(data_list, implicit_coments)

        # middlewares
        library = MiddlewaresStrToLibrary(self.options).functions(library)
        return library
