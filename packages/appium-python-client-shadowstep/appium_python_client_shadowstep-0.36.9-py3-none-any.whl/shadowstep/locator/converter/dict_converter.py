"""DictConverter for converting Shadowstep dictionary locators to other formats.

This module provides the main DictConverter class that handles conversion
from Shadowstep dictionary format to XPath and UiSelector expressions.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, Generic, TypeVar, Union

from shadowstep.exceptions.shadowstep_exceptions import (
    ShadowstepConflictingDescriptionAttributesError,
    ShadowstepConflictingTextAttributesError,
    ShadowstepDictConversionError,
    ShadowstepEmptySelectorError,
    ShadowstepHierarchicalAttributeError,
    ShadowstepSelectorTypeError,
)
from shadowstep.locator.locator_types.shadowstep_dict import ShadowstepDictAttribute
from shadowstep.locator.map.dict_to_ui import (
    DICT_TO_UI_MAPPING,
    get_ui_method_for_hierarchical_attribute,
)
from shadowstep.locator.map.dict_to_xpath import (
    DICT_TO_XPATH_MAPPING,
    get_xpath_for_hierarchical_attribute,
)

# Type aliases for better readability and maintainability
SelectorDict = Union[dict[str, Any], dict[ShadowstepDictAttribute, Any]]
HierarchicalParts = list[tuple[Union[str, ShadowstepDictAttribute], Any]]
XPathParts = list[str]
UIParts = list[str]
MappingFunction = Callable[[Any], str]

# Additional type aliases for better type safety
KeyType = Union[str, ShadowstepDictAttribute]
ValueType = Any
HierarchicalKeyType = Union[str, ShadowstepDictAttribute]
HierarchicalValueType = Union[dict[str, Any], dict[ShadowstepDictAttribute, Any]]

# Type variables for generic typing
T = TypeVar("T", bound=Any)


class DictConverter(Generic[T]):
    """Converter for Shadowstep dictionary locators to XPath and UiSelector formats.

    This class provides methods to convert dictionary-based locators to various
    formats including XPath expressions and UiSelector strings.
    """

    def __init__(self) -> None:
        """Initialize the converter with logging."""
        self.logger: logging.Logger = logging.getLogger(__name__)

    def dict_to_xpath(self, selector_dict: SelectorDict) -> str:
        """Convert Shadowstep dictionary locator to XPath expression.

        Args:
            selector_dict: Dictionary representation of the selector

        Returns:
            XPath expression string

        Raises:
            ShadowstepConversionError: If conversion fails

        """
        try:
            return self._dict_to_xpath_recursive(selector_dict)
        except Exception as e:
            error_message = str(e)
            conversion_type = "XPath"
            raise ShadowstepDictConversionError(conversion_type, error_message) from e

    def dict_to_ui_selector(self, selector_dict: SelectorDict) -> str:
        """Convert Shadowstep dictionary locator to UiSelector string.

        Args:
            selector_dict: Dictionary representation of the selector

        Returns:
            UiSelector string

        Raises:
            ShadowstepConversionError: If conversion fails

        """
        try:
            ui_selector = self._dict_to_ui_recursive(selector_dict)
        except Exception as e:
            error_message = str(e)
            conversion_type = "UiSelector"
            raise ShadowstepDictConversionError(conversion_type, error_message) from e
        else:
            return f"new UiSelector(){ui_selector};"

    def _dict_to_xpath_recursive(  # noqa: C901
            self,
            selector_dict: SelectorDict,
            base_xpath: str = "//*",
    ) -> str:
        if not selector_dict:
            return base_xpath

        xpath_parts: XPathParts = []
        hierarchical_parts: HierarchicalParts = []
        instance_part: str | None = None

        for key, value in selector_dict.items():
            if key in (
                    ShadowstepDictAttribute.CHILD_SELECTOR,
                    ShadowstepDictAttribute.FROM_PARENT,
                    ShadowstepDictAttribute.SIBLING,
            ):
                hierarchical_parts.append((key, value))
                continue

            try:
                # try Enum
                attr: ShadowstepDictAttribute = ShadowstepDictAttribute(key)
            except ValueError:
                # fallback: key not in ShadowstepDictAttribute → take as is
                xpath_parts.append(f"@{key}='{value}'")
                continue

            if attr == ShadowstepDictAttribute.INSTANCE:
                instance_part = f"[{int(value) + 1}]"
            elif attr in DICT_TO_XPATH_MAPPING:
                mapping_func: MappingFunction = DICT_TO_XPATH_MAPPING[attr]
                xpath_parts.append(mapping_func(value))
            else:
                # fallback: Enum exists but not in DICT_TO_XPATH_MAPPING → still use raw
                xpath_parts.append(f"@{attr.value}='{value}'")

        # build XPath
        xpath = base_xpath
        for condition in xpath_parts:
            xpath = f"{xpath}[{condition}]"

        if instance_part:
            xpath += instance_part

        for hierarchical_key, hierarchical_value in hierarchical_parts:
            if isinstance(hierarchical_value, dict):
                nested_xpath: str = self._dict_to_xpath_recursive(
                    hierarchical_value,  # type: ignore[arg-type]
                )
                hierarchical_attr: ShadowstepDictAttribute = ShadowstepDictAttribute(hierarchical_key)
                xpath += get_xpath_for_hierarchical_attribute(
                    hierarchical_attr, nested_xpath,
                )
            else:
                self.logger.warning(
                    "Hierarchical attribute %s requires dict value", hierarchical_key,
                )

        return xpath

    def _dict_to_ui_recursive(self, selector_dict: SelectorDict) -> str:
        """Recursively convert dictionary to UiSelector method chain.

        Args:
            selector_dict: Dictionary representation of the selector

        Returns:
            UiSelector method chain string

        """
        if not selector_dict:
            return ""

        ui_parts: UIParts = []
        hierarchical_parts: HierarchicalParts = []

        # Process regular attributes
        for key, value in selector_dict.items():
            if key in (ShadowstepDictAttribute.CHILD_SELECTOR, ShadowstepDictAttribute.FROM_PARENT, ShadowstepDictAttribute.SIBLING):
                # Handle hierarchical attributes separately
                hierarchical_parts.append((key, value))
                continue

            try:
                # Map UiSelector keys to ShadowstepDictAttribute keys
                key_mapping: dict[str, str] = {
                    "className": "class",
                    "classNameMatches": "classMatches",
                    "textContains": "textContains",
                    "textStartsWith": "textStartsWith",
                    "textMatches": "textMatches",
                    "description": "content-desc",
                    "descriptionContains": "content-descContains",
                    "descriptionStartsWith": "content-descStartsWith",
                    "descriptionMatches": "content-descMatches",
                    "resourceId": "resource-id",
                    "resourceIdMatches": "resource-idMatches",
                    "packageName": "package",
                    "packageNameMatches": "packageMatches",
                    "longClickable": "long-clickable",
                }
                mapped_key: str = key_mapping.get(key, key)
                attr: ShadowstepDictAttribute = ShadowstepDictAttribute(mapped_key)
                if attr in DICT_TO_UI_MAPPING:
                    mapping_func: MappingFunction = DICT_TO_UI_MAPPING[attr]
                    ui_part: str = mapping_func(value)
                    ui_parts.append(ui_part)
                else:
                    self.logger.warning("Unsupported attribute for UiSelector: %s", key)
            except ValueError:
                self.logger.warning("Unknown attribute: %s", key)
                continue

        # Build shadowstep UiSelector chain
        ui_selector: str = "".join(ui_parts)

        # Handle hierarchical relationships
        for hierarchical_key, hierarchical_value in hierarchical_parts:
            if isinstance(hierarchical_value, dict):
                nested_ui: str = self._dict_to_ui_recursive(hierarchical_value)  # type: ignore[arg-type]
                hierarchical_attr: ShadowstepDictAttribute = ShadowstepDictAttribute(hierarchical_key)
                method_name: str = get_ui_method_for_hierarchical_attribute(hierarchical_attr)
                ui_selector += f".{method_name}(new UiSelector(){nested_ui})"
            else:
                self.logger.warning("Hierarchical attribute %s requires dict value", hierarchical_key)

        return ui_selector

    def validate_dict_selector(self, selector_dict: SelectorDict) -> None:
        """Validate dictionary selector for compatibility.

        Args:
            selector_dict: Dictionary representation of the selector

        Raises:
            ValueError: If selector is invalid

        """
        if not isinstance(selector_dict, dict): # type: ignore[arg-type]
            raise ShadowstepSelectorTypeError

        if not selector_dict:
            raise ShadowstepEmptySelectorError

        # Check for conflicting attributes
        text_attrs: list[ShadowstepDictAttribute] = [
            ShadowstepDictAttribute.TEXT,
            ShadowstepDictAttribute.TEXT_CONTAINS,
            ShadowstepDictAttribute.TEXT_STARTS_WITH,
            ShadowstepDictAttribute.TEXT_MATCHES,
        ]
        desc_attrs: list[ShadowstepDictAttribute] = [
            ShadowstepDictAttribute.DESCRIPTION,
            ShadowstepDictAttribute.DESCRIPTION_CONTAINS,
            ShadowstepDictAttribute.DESCRIPTION_STARTS_WITH,
            ShadowstepDictAttribute.DESCRIPTION_MATCHES,
        ]

        found_text_attrs: list[ShadowstepDictAttribute] = [
            attr for attr in text_attrs if attr.value in selector_dict
        ]
        found_desc_attrs: list[ShadowstepDictAttribute] = [
            attr for attr in desc_attrs if attr.value in selector_dict
        ]

        if len(found_text_attrs) > 1:
            raise ShadowstepConflictingTextAttributesError(str(found_text_attrs))
        if len(found_desc_attrs) > 1:
            raise ShadowstepConflictingDescriptionAttributesError(str(found_desc_attrs))

        # Validate hierarchical attributes
        for key, value in selector_dict.items():
            if key in (ShadowstepDictAttribute.CHILD_SELECTOR, ShadowstepDictAttribute.FROM_PARENT, ShadowstepDictAttribute.SIBLING):
                if not isinstance(value, dict):
                    raise ShadowstepHierarchicalAttributeError(key)
                # Recursive validation with proper type casting
                self.validate_dict_selector(value)  # type: ignore[arg-type]
