"""Macro language parser for template-based path generation."""

from griptape_nodes.common.macro_parser.core import ParsedMacro
from griptape_nodes.common.macro_parser.exceptions import MacroResolutionError, MacroSyntaxError
from griptape_nodes.common.macro_parser.formats import (
    DateFormat,
    LowerCaseFormat,
    NumericPaddingFormat,
    SeparatorFormat,
    SlugFormat,
    UpperCaseFormat,
)
from griptape_nodes.common.macro_parser.segments import ParsedStaticValue, ParsedVariable, VariableInfo

__all__ = [
    "DateFormat",
    "LowerCaseFormat",
    "MacroResolutionError",
    "MacroSyntaxError",
    "NumericPaddingFormat",
    "ParsedMacro",
    "ParsedStaticValue",
    "ParsedVariable",
    "SeparatorFormat",
    "SlugFormat",
    "UpperCaseFormat",
    "VariableInfo",
]
