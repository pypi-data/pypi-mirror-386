"""UiSelector converter module for Shadowstep framework.

This module provides the UiSelectorConverter class for converting
UiSelector strings between different formats including XPath,
dictionary locators, and back to UiSelector strings with
comprehensive error handling and validation.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from shadowstep.exceptions.shadowstep_exceptions import (
    ShadowstepConflictingMethodsError,
    ShadowstepInvalidUiSelectorError,
    ShadowstepInvalidUiSelectorStringError,
    ShadowstepMethodRequiresArgumentError,
    ShadowstepSelectorToXPathError,
    ShadowstepUiSelectorConversionError,
    ShadowstepUiSelectorMethodArgumentError,
    ShadowstepUnsupportedNestedSelectorError,
)

if TYPE_CHECKING:
    from shadowstep.locator.converter.ui_selector_converter_core.ui_selector_ast import Selector
from shadowstep.locator.converter.ui_selector_converter_core.ui_selector_lexer import Lexer
from shadowstep.locator.converter.ui_selector_converter_core.ui_selector_parser import Parser
from shadowstep.locator.locator_types.ui_selector import UiAttribute
from shadowstep.locator.map.ui_to_dict import UI_TO_SHADOWSTEP_DICT
from shadowstep.locator.map.ui_to_xpath import (
    UI_TO_XPATH,
    get_xpath_for_method,
    is_hierarchical_method,
)


class UiSelectorConverter:
    """Enhanced UiSelector converter with improved error handling and caching.

    This class provides methods to convert UiSelector strings to various formats
    including XPath, dictionary locators, and back to UiSelector strings.
    """

    def __init__(self) -> None:
        """Initialize the converter with logging."""
        self.logger = logging.getLogger(__name__)
        self._compatible_groups = self._build_compatibility_groups()

    def selector_to_xpath(self, selector_str: str) -> str:
        """Convert UiSelector string directly to XPath.

        Args:
            selector_str: UiSelector string

        Returns:
            XPath string

        Raises:
            ShadowstepInvalidUiSelectorError: If selector string is invalid
            ShadowstepConversionError: If conversion fails

        """
        try:
            parsed_dict = self.parse_selector_string(selector_str)
            return self._selector_to_xpath(parsed_dict)  # type: ignore[return-any]
        except ShadowstepInvalidUiSelectorError:
            raise
        except Exception as e:
            error_message = str(e)
            conversion_type = "XPath"
            raise ShadowstepUiSelectorConversionError(operation=conversion_type, details=error_message) from e

    def selector_to_dict(self, selector_str: str) -> dict[str, Any]:
        """Convert UiSelector string to dictionary format.

        Args:
            selector_str: UiSelector string

        Returns:
            Dictionary representation of the selector

        """
        try:
            parsed_dict = self.parse_selector_string(selector_str)
            return self._selector_to_dict(parsed_dict)  # type: ignore[return-any]
        except ShadowstepInvalidUiSelectorError:
            raise
        except Exception as e:
            error_message = str(e)
            conversion_type = "Dict"
            raise ShadowstepUiSelectorConversionError(operation=conversion_type, details=error_message) from e

    def parse_selector_string(self, selector_str: str) -> dict[str, Any]:
        """Parse UiSelector string into dictionary format.

        Args:
            selector_str: UiSelector string to parse

        Returns:
            Parsed selector dictionary

        Raises:
            ShadowstepInvalidUiSelectorError: If parsing fails

        """
        try:
            # Clean the input string
            cleaned_str = selector_str.strip()
            if cleaned_str.startswith("'") and cleaned_str.endswith("'"):
                cleaned_str = cleaned_str[1:-1]

            # Tokenize and parse
            tokens = Lexer(cleaned_str).tokens()
            selector = Parser(tokens).parse()

            return self._selector_to_parsed_dict(selector)

        except Exception as e:
            self.logger.exception("Failed to parse UiSelector string")
            raise ShadowstepInvalidUiSelectorStringError(str(e)) from e

    def _selector_to_xpath(self, sel: dict[str, Any], base_xpath: str = "//*") -> str:  # noqa: PLR0912, C901
        """Convert a parsed selector dictionary to XPath.

        Args:
            sel: Parsed selector dictionary with methods
            base_xpath: Base XPath to start with (default: "//*")

        Returns:
            XPath string representation

        Raises:
            ShadowstepConversionError: If conversion fails

        """
        try:
            xpath = base_xpath

            for method_data in sel.get("methods", []):
                name = method_data["name"]
                args = method_data.get("args", [])

                try:
                    method = UiAttribute(name)
                except ValueError as e:
                    self.logger.warning("Unknown UiSelector method '%s', skipping: %s", name, e)
                    continue

                if is_hierarchical_method(method):
                    # Handle hierarchical methods specially
                    if method == UiAttribute.CHILD_SELECTOR:
                        child_xpath = self._convert_nested_selector(args[0])
                        xpath += f"/{child_xpath}"
                    elif method == UiAttribute.FROM_PARENT:
                        parent_xpath = self._convert_nested_selector(args[0])
                        if parent_xpath.startswith("//"):
                            xpath = f"{xpath}/..{parent_xpath}"
                        else:
                            xpath = f"{xpath}/..//{parent_xpath}"
                elif method in UI_TO_XPATH:
                    if args:
                        xpath += get_xpath_for_method(method, args[0])
                    else:
                        xpath += get_xpath_for_method(method, True)  # noqa: FBT003
                else:
                    self.logger.warning("Method '%s' not supported in XPath conversion", method)

        except Exception as e:
            raise ShadowstepSelectorToXPathError(str(e)) from e
        else:
            return xpath

    def _selector_to_dict(self, sel: dict[str, Any]) -> dict[str, Any]:
        """Convert parsed selector dictionary to Shadowstep dict format.

        Args:
            sel: Parsed selector dictionary

        Returns:
            Shadowstep dict representation

        """
        result: dict[str, Any] = {}
        methods = sel.get("methods", [])

        if not methods:
            return {}

        for method_data in methods:
            method_name = method_data["name"]
            args = method_data.get("args", [])

            if method_name not in UI_TO_SHADOWSTEP_DICT:
                error_message = f"Method '{method_name}' is not supported"
                raise NotImplementedError(error_message)

            self._validate_method_compatibility(method_name, result.keys())     # type: ignore[arg-type]

            if method_name in [UiAttribute.CHILD_SELECTOR, UiAttribute.FROM_PARENT]:
                if args and isinstance(args[0], dict):
                    nested_result = self._selector_to_dict(args[0])
                    result[method_name] = nested_result
                else:
                    result[method_name] = args[0] if args else None
            else:
                converter = UI_TO_SHADOWSTEP_DICT[method_name]
                if not args:
                    raise ShadowstepMethodRequiresArgumentError(method_name)

                converted = converter(args[0])
                result.update(converted)

        return result

    def _validate_method_compatibility(self, new_method: str, existing_methods: list[str]) -> None:
        """Validate that new method is compatible with existing methods.

        Args:
            new_method: New method to add
            existing_methods: List of already added methods

        Raises:
            ValueError: If methods are incompatible

        """
        if not existing_methods:
            return

        for group_name, group_methods in self._compatible_groups.items():
            if new_method in group_methods:
                for existing in existing_methods:
                    if (existing in group_methods and existing != new_method and
                            group_name in ["text", "description", "resource", "class"]):
                            raise ShadowstepConflictingMethodsError(existing, new_method, group_name)
                break

    def _build_compatibility_groups(self) -> dict[str, list[str]]:
        return {
            "text": [UiAttribute.TEXT, UiAttribute.TEXT_CONTAINS, UiAttribute.TEXT_STARTS_WITH, UiAttribute.TEXT_MATCHES],
            "description": [UiAttribute.DESCRIPTION, UiAttribute.DESCRIPTION_CONTAINS, UiAttribute.DESCRIPTION_STARTS_WITH, UiAttribute.DESCRIPTION_STARTS_WITH],
            "resource": [UiAttribute.RESOURCE_ID, UiAttribute.RESOURCE_ID_MATCHES, UiAttribute.PACKAGE_NAME, UiAttribute.PACKAGE_NAME_MATCHES],
            "class": [UiAttribute.CLASS_NAME, UiAttribute.CLASS_NAME_MATCHES],
            "boolean": [UiAttribute.CHECKABLE, UiAttribute.CHECKED, UiAttribute.CLICKABLE, UiAttribute.LONG_CLICKABLE, UiAttribute.ENABLED,
                        UiAttribute.FOCUSABLE, UiAttribute.FOCUSED, UiAttribute.SCROLLABLE, UiAttribute.SELECTED, UiAttribute.PASSWORD],
            "numeric": [UiAttribute.INDEX, UiAttribute.INSTANCE],
            "hierarchy": [UiAttribute.CHILD_SELECTOR, UiAttribute.FROM_PARENT],
        }

    def _convert_nested_selector(self, nested_sel: dict[str, Any] | Selector) -> str:
        """Convert a nested selector to XPath.

        Args:
            nested_sel: Nested selector (can be dict or Selector object)

        Returns:
            XPath string for the nested selector

        """
        if isinstance(nested_sel, dict):
            return self._selector_to_xpath(nested_sel, base_xpath="*")  # type: ignore[return-any]
        if hasattr(nested_sel, "methods"):
            # Handle Selector AST object
            parsed_dict = self._selector_to_parsed_dict(nested_sel)
            return self._selector_to_xpath(parsed_dict, base_xpath="*")  # type: ignore[return-any]
        raise ShadowstepUnsupportedNestedSelectorError(str(type(nested_sel)))

    def _selector_to_parsed_dict(self, sel: Selector) -> dict[str, Any]:
        """Convert Selector AST object to dictionary format.

        Args:
            sel: Selector AST object

        Returns:
            Dictionary representation of the selector

        """

        def convert_arg(arg: str | float | bool | Selector) -> str | int | float | bool | dict[str, Any]:  # noqa: FBT001
            if hasattr(arg, "methods"):  # Nested Selector
                return self._selector_to_parsed_dict(arg)  # type: ignore[arg-type]
            return arg  # type: ignore[return-value]

        return {
            "methods": [
                {"name": method.name, "args": [convert_arg(arg) for arg in method.args]}
                for method in sel.methods
            ],
        }

    def _parsed_dict_to_selector(self, selector_dict: dict[str, Any], top_level: bool = True) -> str:  # noqa: FBT001, FBT002
        """Convert parsed dictionary back to UiSelector string.

        Args:
            selector_dict: Parsed selector dictionary
            top_level: Whether this is the top-level selector

        Returns:
            UiSelector string

        """

        def format_arg(arg: str | float | bool | dict[str, Any]) -> str:  # noqa: FBT001
            if isinstance(arg, dict):
                # Nested selector - without final semicolon
                return self._parsed_dict_to_selector(arg, top_level=False)
            if isinstance(arg, bool):
                return "true" if arg else "false"
            if isinstance(arg, int):
                return str(arg)
            # Escape quotes and backslashes
            escaped = str(arg).replace("\\", "\\\\").replace('"', '\\"')
            return f'"{escaped}"'

        parts = ["new UiSelector()"]

        for method_data in selector_dict.get("methods", []):
            method_name = method_data["name"]
            args = method_data.get("args", [])

            if len(args) > 1:
                raise ShadowstepUiSelectorMethodArgumentError(str(len(args)))

            arg_str = format_arg(args[0]) if args else ""
            parts.append(f".{method_name}({arg_str})")

        result = "".join(parts)
        return result + ";" if top_level else result
