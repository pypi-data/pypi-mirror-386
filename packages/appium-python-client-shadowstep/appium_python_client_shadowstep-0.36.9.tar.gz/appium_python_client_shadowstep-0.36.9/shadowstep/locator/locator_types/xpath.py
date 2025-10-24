"""XPath attribute types.

This module defines the XPathAttribute enum that represents
all supported attribute types for XPath locators,
including text-based, description, resource ID, class, boolean,
numeric, and hierarchical attributes with their XPath syntax.
"""
from enum import Enum


class XPathAttribute(str, Enum):
    """Enumeration of supported attribute types for XPath locators.

    This enum defines all supported attribute types that can be used
    in XPath locators with their corresponding XPath syntax, including
    text-based, description, resource ID, class, boolean, numeric,
    and hierarchical attributes.
    """

    # --- text-based ---
    TEXT = "@text="
    TEXT_CONTAINS = "contains(@text, "
    TEXT_STARTS_WITH = "starts-with(@text, "
    TEXT_MATCHES = "matches(@text, "

    # --- description ---
    DESCRIPTION = "@content-desc="
    DESCRIPTION_CONTAINS = "contains(@content-desc, "
    DESCRIPTION_STARTS_WITH = "starts-with(@content-desc, "
    DESCRIPTION_MATCHES = "matches(@content-desc, "

    # --- resource id / package ---
    RESOURCE_ID = "@resource-id="
    RESOURCE_ID_MATCHES = "matches(@resource-id, "
    PACKAGE_NAME = "@package="
    PACKAGE_NAME_MATCHES = "matches(@package, "

    # --- class ---
    CLASS_NAME = "@class="
    CLASS_NAME_MATCHES = "matches(@class, "

    # --- bool props ---
    CHECKABLE = "@checkable="
    CHECKED = "@checked="
    CLICKABLE = "@clickable="
    ENABLED = "@enabled="
    FOCUSABLE = "@focusable="
    FOCUSED = "@focused="
    LONG_CLICKABLE = "@long-clickable="
    SCROLLABLE = "@scrollable="
    SELECTED = "@selected="
    PASSWORD = "@password="  # noqa: S105

    # --- numeric ---
    INDEX = "position()="
    INSTANCE = "instance"                       # use special logic

    # --- hierarchy ---
    CHILD_SELECTOR = "childSelector"            # use special logic
    FROM_PARENT = "fromParent"                  # use special logic
    SIBLING = "following-sibling"               # use special logic

    def __str__(self) -> str:
        """Return the string value of the XPathAttribute.

        Returns:
            str: The string value of the enum attribute.

        """
        return self.value

    def __repr__(self) -> str:
        """Return the official string representation of the XPathAttribute.

        Returns:
            str: String representation in format 'ClassName.ATTRIBUTE_NAME'.

        """
        return f"{self.__class__.__name__}.{self.name}"

    def __eq__(self, other: object) -> bool:
        """Check equality with string or other enum values.

        Args:
            other: Object to compare with.

        Returns:
            bool: True if equal, False otherwise.

        """
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        """Return hash value based on the enum value.

        Returns:
            int: Hash value of the enum's string value.

        """
        return hash(self.value)
