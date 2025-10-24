"""Page object generator for Shadowstep framework.

This module provides the PageObjectGenerator class for automatically
generating page object classes from UI element trees, including
property extraction, locator generation, and template-based rendering.
"""
from __future__ import annotations

import keyword
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

from anyascii import anyascii
from jinja2 import Environment, FileSystemLoader

from shadowstep.exceptions.shadowstep_exceptions import (
    ShadowstepFailedToNormalizeScreenNameError,
    ShadowstepNameCannotBeEmptyError,
    ShadowstepPageClassNameCannotBeEmptyError,
    ShadowstepTitleNodeNoUsableNameError,
    ShadowstepTitleNotFoundError,
)
from shadowstep.utils.utils import get_current_func_name

if TYPE_CHECKING:
    from shadowstep.page_object.page_object_element_node import UiElementNode


class PageObjectGenerator:
    """Generator for creating page object classes from UI element trees.

    This class provides functionality to automatically generate page object
    classes from UI element trees, including property extraction, locator
    generation, and template-based rendering.
    """

    def __init__(self, translator: Any = None) -> None:
        """Initialize the PageObjectGenerator.

        Args:
            translator: Optional translator instance for text translation, must contain def translate(text: str) -> str.

        """
        self.logger = logging.getLogger(__name__)
        self.translator = translator
        self.BLACKLIST_NO_TEXT_CLASSES = {
            "android.widget.SeekBar",
            "android.widget.ProgressBar",
            "android.widget.Switch",
            "android.widget.CheckBox",
            "android.widget.ToggleButton",
            "android.view.View",
            "android.widget.ImageView",
            "android.widget.ImageButton",
            "android.widget.RatingBar",
            "androidx.recyclerview.widget.RecyclerView",
            "androidx.viewpager.widget.ViewPager",
        }
        self.STRUCTURAL_CLASSES = {
            "android.widget.FrameLayout",
            "android.widget.LinearLayout",
            "android.widget.RelativeLayout",
            "android.view.ViewGroup",
        }
        self.CONTAINER_IDS = {
            "android:id/content",
            "com.android.settings:id/app_bar",
            "com.android.settings:id/action_bar",
            "com.android.settings:id/content_frame",
            "com.android.settings:id/main_content",
            "com.android.settings:id/container_material",
            "android:id/widget_frame",
            "android:id/list_container",
        }
        self._anchor_name_map = None

        # Initialize Jinja2
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),  # where to load templates from (directory with .j2 files)
            autoescape=False,  # noqa: S701
            keep_trailing_newline=True,
            # preserve trailing newline in file (important for git-diff, PEP8, etc.)
            trim_blocks=True,  # removes newline immediately after {% block %} or {% endif %} (reduces empty lines)
            lstrip_blocks=True,
            # removes leading spaces before {% block %} (eliminates accidental indentation and empty lines)
        )
        # add repr filter
        self.env.filters["pretty_dict"] = _pretty_dict

    def generate(  # noqa: PLR0915
            self,
            ui_element_tree: UiElementNode,
            output_dir: str,
            filename_prefix: str = "",
    ) -> tuple[Path, str]:
        """Generate page object from UI element tree.

        Args:
            ui_element_tree: Root UI element node.
            output_dir: Directory to save generated files.
            filename_prefix: Prefix for generated filenames.

        Returns:
            tuple[Path, str]: (output_path, class_name) of generated page object.

        """
        self.logger.debug("%s", get_current_func_name())
        step = "Forming title property"
        self.logger.debug(step)
        title = self._get_title_property(ui_element_tree)
        if title is None:
            raise ShadowstepTitleNotFoundError
        self.logger.debug("title.attrs=%s", title.attrs)

        step = "Forming name property"
        self.logger.debug(step)
        name = self._get_name_property(title)
        if name == "":
            raise ShadowstepNameCannotBeEmptyError
        self.logger.debug("name=%s", name)

        step = "Forming class name"
        self.logger.debug(step)
        page_class_name = self._normilize_to_camel_case(name)
        if page_class_name == "":
            raise ShadowstepPageClassNameCannotBeEmptyError
        self.logger.debug("page_class_name=%s", page_class_name)

        step = "Forming recycler property"
        self.logger.debug(step)
        recycler = self._get_recycler_property(ui_element_tree)
        # assert recycler is not None, "Can't find recycler"
        if recycler is None:
            recycler = title
        self.logger.debug("recycler.attrs=%s", recycler.attrs)

        step = "Collecting switch-anchor pairs"
        self.logger.debug(step)
        switcher_anchor_pairs = self._get_anchor_pairs(ui_element_tree, {"class": "android.widget.Switch"})
        # switches may not be found, this is normal
        self.logger.debug("len(switcher_anchor_pairs)=%s", len(switcher_anchor_pairs))

        step = "Collecting summary properties"
        self.logger.debug(step)
        summary_anchor_pairs = self._get_summary_pairs(ui_element_tree)
        # summary may not be found, this is normal
        self.logger.debug("len(summary_anchor_pairs)=%s", len(summary_anchor_pairs))

        step = "Collecting remaining regular properties"
        self.logger.debug(step)
        used_elements = switcher_anchor_pairs + summary_anchor_pairs + [(title, recycler)]
        regular_properties = self._get_regular_properties(ui_element_tree, used_elements, recycler)

        step = "Removing text from locators for elements that are not searched by text in UiAutomator2 (ex. android.widget.SeekBar)"
        self.logger.debug(step)
        self._remove_text_from_non_text_elements(regular_properties)

        step = "Determining recycler necessity"
        self.logger.debug(step)
        need_recycler = self._is_need_recycler(recycler, regular_properties)
        self.logger.debug("need_recycler=%s", need_recycler)

        step = "Preparing properties for template"
        self.logger.debug(step)
        properties_for_template = self._transform_properties(
            regular_properties,
            switcher_anchor_pairs,
            summary_anchor_pairs,
            recycler.id if recycler else None,
        )

        step = ""
        self.logger.debug(step)
        skip_ids = {title.id, recycler.id}
        properties_for_template = [p for p in properties_for_template if p.get("element_id") not in skip_ids]

        step = "Filtering final properties"
        self.logger.debug(step)

        properties_for_template = self._filter_properties(properties_for_template,
                                                          title.id,
                                                          recycler.id if recycler else None)

        step = "Preparing data for rendering"
        self.logger.debug(step)
        template_data = self._prepare_template_data(
            title,
            recycler,
            properties_for_template,
            need_recycler,
        )

        step = "Rendering"
        self.logger.debug(step)
        template = self.env.get_template("page_object.py.j2")
        rendered = template.render(**template_data)

        step = "Forming filename"
        self.logger.debug(step)
        class_name = template_data["class_name"]
        file_name = self._class_name_to_file_name(class_name)

        step = "Adding prefix to filename if necessary"
        self.logger.debug(step)
        if filename_prefix:
            file_name = f"{filename_prefix}{file_name}"

        step = "Writing to file"
        self.logger.debug(step)
        path = Path(output_dir) / file_name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            f.write(rendered)

        self.logger.debug("Generated PageObject → %s", path)
        return path, class_name

    def _get_title_property(self, ui_element_tree: UiElementNode) -> UiElementNode | None:
        """Return the most likely title node from the tree.

        Args:
            ui_element_tree (UiElementNode): Root node of the parsed UI tree.

        Returns:
            Optional[UiElementNode]: Node with screen title (from text or content-desc).

        """
        self.logger.debug("%s", get_current_func_name())

        def is_potential_title(ui_node: UiElementNode) -> bool:
            if ui_node.tag not in {"android.widget.TextView", "android.widget.FrameLayout"}:
                return False
            if ui_node.attrs.get("displayed", "false") != "true":
                return False
            if ui_node.attrs.get("content-desc"):
                return True
            return bool(ui_node.attrs.get("text"))

        # Use BFS to prioritize topmost title
        queue = [ui_element_tree]
        while queue:
            ui_node = queue.pop(0)
            if is_potential_title(ui_node):
                content = ui_node.attrs.get("content-desc") or ui_node.attrs.get("text")
                if content and content.strip():
                    self.logger.debug("Found title node: %s → %s", ui_node.id, content)
                    return ui_node
            queue.extend(ui_node.children)

        self.logger.warning("No title node found.")
        return None

    def _get_name_property(self, title: UiElementNode) -> str:
        """Extract screen name from title node for use as PageObject class name.

        Args:
            title (UiElementNode): UI node considered the screen title.

        Returns:
            str: Name derived from title node.

        """
        self.logger.debug("%s", get_current_func_name())
        raw_name = title.attrs.get("text") or title.attrs.get("content-desc") or ""
        raw_name = raw_name.strip()
        if not raw_name:
            raise ShadowstepTitleNodeNoUsableNameError
        if raw_name in keyword.kwlist:
            raw_name = raw_name + "_"
        return raw_name

    def _get_recycler_property(self, ui_element_tree: UiElementNode) -> UiElementNode | None:
        """Return the first scrollable parent found in the tree (used as recycler).

        Args:
            ui_element_tree (UiElementNode): Root of parsed UI tree.

        Returns:
            Optional[UiElementNode]: Node marked as scrollable container (recycler).

        """
        self.logger.debug("%s", get_current_func_name())

        for node in ui_element_tree.walk():
            scrollable_parents = node.scrollable_parents
            if scrollable_parents:
                # take the closest scrollable (first in list)
                scrollable_id = scrollable_parents[0]
                self.logger.debug("Recycler determined from node=%s, scrollable_id=%s", node.id, scrollable_id)
                return self._find_by_id(ui_element_tree, scrollable_id)

        self.logger.warning("No scrollable parent found in any node")
        return None

    def _get_anchor_pairs(
            self,
            ui_element_tree: UiElementNode,
            target_attrs: dict[str, Any],
            max_ancestor_distance: int = 3,
            target_anchor: tuple[str, ...] = ("text", "content-desc"),
    ) -> list[tuple[UiElementNode, UiElementNode]]:
        self.logger.debug("%s", get_current_func_name())

        step = "Init anchor-target pair list"
        self.logger.debug("[%s] started", step)
        anchor_pairs: list[tuple[UiElementNode, UiElementNode]] = []

        step = "Find matching targets"
        self.logger.debug("[%s] started", step)
        targets = ui_element_tree.find(**target_attrs)
        if not targets:
            return []

        step = "Process each target"
        self.logger.debug("[%s] started", step)
        for target in targets:
            anchor = self._find_anchor_for_target(target, max_ancestor_distance, target_anchor)
            if anchor:
                anchor_pairs.append((anchor, target))
        return anchor_pairs

    def _find_anchor_for_target(self, target_element: UiElementNode, max_levels: int,
                                target_anchor: tuple[str, ...] = ("text", "content-desc")) -> UiElementNode | None:
        self.logger.debug("%s", get_current_func_name())
        for level in range(max_levels + 1):
            parent = self._get_ancestor(target_element, level)
            if not parent:
                break
            candidates = self._get_siblings_or_cousins(parent, target_element)
            for candidate in candidates:
                if self._is_anchor_like(candidate, target_anchor):
                    return candidate
        return None

    def _get_ancestor(self, node: UiElementNode, levels_up: int) -> UiElementNode | None:
        current = node
        for _ in range(levels_up + 1):
            if not current.parent:
                return None
            current = current.parent
        return current

    def _get_siblings_or_cousins(self,
                                 ancestor: UiElementNode,
                                 target: UiElementNode) -> list[UiElementNode]:
        """Return list of sibling or cousin nodes at same depth as target, excluding target itself.

        Args:
            ancestor (UiElementNode): Common ancestor of nodes.
            target (UiElementNode): Node for which to find siblings or cousins.

        Returns:
            List[UiElementNode]: Filtered nodes at same depth.

        """
        self.logger.debug("%s", get_current_func_name())

        step = "Iterating over ancestor.children"
        self.logger.debug("[%s] started", step)

        result: list[UiElementNode] = []
        # First collect all descendants of ancestor
        all_descendants: list[UiElementNode] = []
        for child in ancestor.children:
            all_descendants.extend(child.walk())  # type: ignore[arg-type]

        # Now filter by depth
        for node in all_descendants:
            if node is target:
                continue

            if node.depth == target.depth:  # type: ignore[attr-defined]
                self.logger.debug(
                    "Sibling/cousin candidate: id=%s, class=%s, text=%s, content-desc=%s", node.id, node.tag,  # type: ignore[attr-defined]
                    node.attrs.get("text"), node.attrs.get("content-desc"))  # type: ignore[attr-defined]
                result.append(node)  # type: ignore[arg-type]
            else:
                self.logger.debug("Rejected (wrong depth): id=%s, depth=%s ≠ %s", node.id, node.depth, target.depth)  # type: ignore[attr-defined]

        self.logger.debug("Total candidates found: %s", len(result))
        return result

    def _is_same_depth(self, node1: UiElementNode, node2: UiElementNode) -> bool:
        return node1.depth == node2.depth

    def _is_anchor_like(self, node: UiElementNode, target_anchor: tuple[str, ...] = ("text", "content-desc")) -> bool:
        """Check if the node has any of the specified attributes used to identify anchor elements.

        Args:
            node (UiElementNode): Node to check.
            target_anchor (Tuple[str, ...]): Attributes that may indicate anchor-like quality.

        Returns:
            bool: True if node has any non-empty anchor attribute.

        """
        # Ensure at least one anchor attribute is present and non-empty
        return any(node.attrs.get(attr) for attr in target_anchor)

    def _get_summary_pairs(self, ui_element_tree: UiElementNode) -> list[tuple[UiElementNode, UiElementNode]]:
        """Find anchor-summary element pairs.

        Args:
            ui_element_tree (UiElementNode): UI element tree

        Returns:
            List[Tuple[UiElementNode, UiElementNode]]: List of (anchor, summary) pairs

        """
        self.logger.debug("%s", get_current_func_name())

        # Find all elements that have "summary" in attributes
        summary_elements: list[UiElementNode] = []
        for element in ui_element_tree.walk():
            if any(re.search(r"\bsummary\b", str(value).lower()) for value in element.attrs.values()):
                summary_elements.append(element)  # type: ignore[arg-type]
                self.logger.debug("Found summary element: %s, attrs=%s", element.id, element.attrs)  # type: ignore[attr-defined]

        # For each summary element find corresponding anchor
        summary_pairs: list[tuple[UiElementNode, UiElementNode]] = []
        for summary in summary_elements:
            # Find closest anchor for summary element
            anchor = self._find_anchor_for_target(summary, max_levels=3,
                                                  target_anchor=("text", "content-desc"))
            if anchor and not any("summary" in str(value).lower() for value in anchor.attrs.values()):
                self.logger.debug("Found anchor for summary %s: %s, attrs=%s", summary.id, anchor.id, anchor.attrs)  # type: ignore[attr-defined]
                summary_pairs.append((anchor, summary))
            else:
                self.logger.warning("No anchor found for summary element %s", summary.id)  # type: ignore[attr-defined]

        self.logger.debug("Total summary-anchor pairs found: %s", len(summary_pairs))
        return summary_pairs

    def _get_regular_properties(
            self,
            ui_element_tree: UiElementNode,
            used_elements: list[tuple[UiElementNode, UiElementNode]],
            recycler: UiElementNode | None = None,
    ) -> list[UiElementNode]:
        """Return all elements that are not part of used_elements, filtering by locator to avoid duplicates.

        Args:
            ui_element_tree (UiElementNode): UI tree root
            used_elements (List[Tuple[UiElementNode, UiElementNode]]): Already used pairs (anchor, target)
            recycler (UiElementNode | None): Optional recycler element to filter out

        Returns:
            List[UiElementNode]: List of unused, unique-locator elements

        """
        self.logger.debug("%s", get_current_func_name())

        # 🔁 Convert used_elements to set of locator hashes
        used_locators: set[frozenset[tuple[str, str]]] = set()
        for pair in used_elements:
            for node in pair:
                locator = self._node_to_locator(node)
                locator_frozen = frozenset(locator.items())
                used_locators.add(locator_frozen)

        regular_elements: list[UiElementNode] = []
        for element in ui_element_tree.walk():
            locator = self._node_to_locator(element)
            if not locator:
                continue

            locator_frozen = frozenset(locator.items())
            if locator_frozen in used_locators:
                continue

            if element.tag == "androidx.recyclerview.widget.RecyclerView" and recycler.id and element.id != recycler.id:  # type: ignore[comparison-overlap]
                self.logger.debug("Skipping redundant recycler view: id=%s", recycler.id)  # type: ignore[arg-type]
                continue

            self.logger.debug("Regular element accepted: %s, locator=%s", element.id, locator)
            regular_elements.append(element)
            used_locators.add(locator_frozen)

        self.logger.debug("Total regular elements found (filtered): %s", len(regular_elements))
        return regular_elements

    def _normilize_to_camel_case(self, text: str) -> str:
        self.logger.debug("%s", get_current_func_name())
        # sanitize → remove spaces, symbols, make CamelCase
        normalized = self._translate(text)  # translate to English
        normalized = re.sub(r"[^\w\s]", "", normalized)  # remove special characters
        camel_case = "".join(word.capitalize() for word in normalized.split())

        if not camel_case:
            raise ShadowstepFailedToNormalizeScreenNameError(text)
        if not camel_case.startswith("Page"):
            camel_case = "Page" + camel_case
        return camel_case

    def _translate(self, text: str) -> str:
        self.logger.debug("%s", get_current_func_name())
        if self.translator is not None:
            text = self.translator.translate(text)
        return text

    def _find_by_id(self, root: UiElementNode, target_id: str) -> UiElementNode | None:
        for node in root.walk():
            if node.id == target_id:
                return node
        return None

    def _remove_text_from_non_text_elements(self, elements: list[UiElementNode]) -> None:
        self.logger.debug("%s", get_current_func_name())

        for element in elements:
            if element.tag in self.BLACKLIST_NO_TEXT_CLASSES and "text" in element.attrs:
                self.logger.debug("Removing text attribute from %s element: %s", element.tag, element.attrs.get("text"))
                del element.attrs["text"]

    def _prepare_template_data(self,
                               title: UiElementNode,
                               recycler: UiElementNode | None,
                               properties: list[dict[str, Any]],
                               need_recycler: bool) -> dict[str, Any]:  # noqa: FBT001
        self.logger.debug("%s", get_current_func_name())
        raw_title = self._get_name_property(title)
        translated = self._translate(raw_title)
        class_name = self._normilize_to_camel_case(translated)

        title_locator = self._node_to_locator(title)
        recycler_locator = self._node_to_locator(recycler) if recycler else None

        return {
            "class_name": class_name,
            "raw_title": raw_title,
            "title_locator": title_locator,
            "properties": properties,
            "need_recycler": need_recycler,
            "recycler_locator": recycler_locator,
        }

    def _node_to_locator(self, node: UiElementNode, only_id: bool = False) -> dict[str, Any]:  # noqa: FBT001, FBT002
        """Convert UiElementNode to a locator dictionary for template.

        Args:
            node (UiElementNode): Node to convert
            only_id (bool): Whether to return only resource-id

        Returns:
            dict[str, Any]: Locator dictionary

        """
        self.logger.debug("%s", get_current_func_name())
        if only_id and node.attrs.get("resource-id"):
            return {"resource-id": node.attrs["resource-id"]}

        locator: dict[str, Any] = {}
        for attr in ["text", "content-desc", "resource-id"]:
            if value := node.attrs.get(attr):
                locator[attr] = value

        if node.tag and "class" not in locator:
            locator["class"] = node.tag

        return locator

    def _transform_properties(  # noqa: C901, PLR0915, PLR0912
            self,
            regular_properties: list[UiElementNode],
            switcher_anchor_pairs: list[tuple[UiElementNode, UiElementNode]],
            summary_anchor_pairs: list[tuple[UiElementNode, UiElementNode]],
            recycler_id: str | None,
    ) -> list[dict[str, Any]]:
        """Transform property nodes into template-compatible property dictionaries.

        Args:
            regular_properties (List[UiElementNode]): Regular UI elements
            switcher_anchor_pairs (List[Tuple[UiElementNode, UiElementNode]]): Anchor-switch pairs
            summary_anchor_pairs (List[Tuple[UiElementNode, UiElementNode]]): Anchor-summary pairs
            recycler_id (Optional[str]): ID of recycler element if available

        Returns:
            List[Dict[str, Any]]: Template-ready property dictionaries

        """
        self.logger.debug("%s", get_current_func_name())

        properties: list[dict[str, Any]] = []
        used_names: set[str] = set()
        used_ids: set[str] = set()

        # 💣 Filtering: remove element if it matches recycler
        regular_properties = [
            node for node in regular_properties
            if node.id != recycler_id
        ]

        # Regular properties
        for node in regular_properties:
            if node.id in used_ids:
                continue
            name = self._generate_property_name(node, used_names)
            prop = {
                "type": "regular",
                "name": name,
                "element_id": node.id,
                "locator": self._node_to_locator(node),
                "sibling": False,
                "via_recycler": self._is_scrollable_by(node, recycler_id),
            }
            properties.append(prop)
            used_names.add(name)
            used_ids.add(node.id)
            self.logger.debug("Added regular: %s → %s", name, prop["locator"])

        # Switcher properties
        for anchor, switcher in switcher_anchor_pairs:
            if anchor.id not in used_ids:
                anchor_name = self._generate_property_name(anchor, used_names)
                anchor_prop = {
                    "type": "anchor",
                    "name": anchor_name,
                    "element_id": anchor.id,
                    "locator": self._node_to_locator(anchor),
                    "sibling": False,
                    "via_recycler": self._is_scrollable_by(anchor, recycler_id),
                    "anchor_locator": self._node_to_locator(anchor),
                }
                properties.append(anchor_prop)
                used_names.add(anchor_name)
                used_ids.add(anchor.id)
                self.logger.debug("Added anchor: %s → %s", anchor_name, anchor_prop["locator"])
            else:
                anchor_name = None
                for p in properties:
                    if p.get("element_id") == anchor.id:
                        anchor_name = p.get("name")
                        break
                if anchor_name is None:
                    anchor_name = self._generate_property_name(anchor, used_names)

            if switcher.id in used_ids:
                continue
            name = self._generate_property_name(switcher, used_names, "_switch", anchor_base=anchor_name)
            prop = {
                "type": "switcher",
                "name": name,
                "locator": self._node_to_locator(switcher),
                "sibling": False,
                "via_recycler": self._is_scrollable_by(switcher, recycler_id),
                "anchor_name": anchor_name,
                "depth": self._calculate_depth(anchor, switcher),
                "anchor_locator": self._node_to_locator(anchor),
            }
            properties.append(prop)
            used_names.add(name)
            used_ids.add(switcher.id)
            self.logger.debug("Added switcher: %s (anchor: %s) → %s", name, anchor_name, prop["locator"])

        # Summary properties
        for anchor, summary in summary_anchor_pairs:
            if anchor.id not in used_ids:
                base_name = self._generate_property_name(anchor, used_names)
                anchor_prop = {
                    "type": "anchor",
                    "name": base_name,
                    "element_id": anchor.id,
                    "locator": self._node_to_locator(anchor),
                    "sibling": False,
                    "via_recycler": self._is_scrollable_by(anchor, recycler_id),
                    "anchor_locator": self._node_to_locator(anchor),
                }
                properties.append(anchor_prop)
                used_names.add(base_name)
                used_ids.add(anchor.id)
                self.logger.debug("Added summary anchor: %s → %s", base_name, anchor_prop["locator"])
            else:
                base_name = None
                for p in properties:
                    if p.get("element_id") == anchor.id:
                        base_name = p["name"]
                        self.logger.debug("[Find base_name] matched property: name=%s, id=%s", base_name, anchor.id)
                        break
                if base_name is None:
                    self.logger.debug("[Find base_name] no match found, generating new name")
                    base_name = self._generate_property_name(anchor, used_names)
                    self.logger.debug("[Find base_name] generated name: %s", base_name)

            if summary.id in used_ids:
                continue
            name = self._generate_property_name(summary, used_names, "_summary", anchor_base=base_name)
            prop = {
                "type": "summary",
                "name": name,
                "element_id": anchor.id,
                "locator": self._node_to_locator(anchor),
                "sibling": True,
                "summary_id": self._node_to_locator(summary, only_id=True),
                "base_name": base_name,
                "anchor_locator": self._node_to_locator(anchor),
            }
            properties.append(prop)
            used_names.add(name)
            used_ids.add(summary.id)
            self.logger.debug("Added summary: %s (anchor: %s) → %s", name, base_name, prop["summary_id"])

        return properties

    def _is_scrollable_by(self, node: UiElementNode, recycler_id: str | None) -> bool:
        """Check if the node is scrollable by the given recycler.

        Args:
            node (UiElementNode): Node to check
            recycler_id (Optional[str]): ID of potential recycler

        Returns:
            bool: True if node is scrollable by the recycler

        """
        self.logger.debug("%s", get_current_func_name())
        if not recycler_id or not node.scrollable_parents:
            return False
        return recycler_id in node.scrollable_parents

    def _calculate_depth(self, anchor: UiElementNode, target: UiElementNode) -> int:
        """Calculate parent traversal depth between anchor and target.

        Args:
            anchor (UiElementNode): Anchor node
            target (UiElementNode): Target node

        Returns:
            int: Number of parent traversals needed

        """
        self.logger.debug("%s", get_current_func_name())
        # Find common ancestor
        anchor_ancestors = [anchor]
        current = anchor
        while current.parent:
            anchor_ancestors.append(current.parent)
            current = current.parent

        # Find path from target to first common ancestor
        depth = 0
        current = target
        while current and current not in anchor_ancestors:
            depth += 1
            current = current.parent

        if not current:
            # No common ancestor found, default to 0
            return 0

        # Add distance from anchor to common ancestor
        depth += anchor_ancestors.index(current)

        return depth

    def _generate_property_name(
            self,
            node: UiElementNode,
            used_names: set[str],
            suffix: str = "",
            anchor_base: str | None = None,
    ) -> str:
        """Generate a clean, unique property name for a node.

        Args:
            node (UiElementNode): UI node.
            used_names (Set[str]): Already used property names.
            suffix (str): Optional suffix, like '_switch' or '_summary'.
            anchor_base (Optional[str]): Use anchor name as prefix if provided.

        Returns:
            str: Property name.

        """
        self.logger.debug("%s", get_current_func_name())

        base = ""
        # Use anchor name if explicitly passed (e.g., switcher/summary tied to anchor)
        if anchor_base:
            base = anchor_base
        else:
            # Prefer text → content-desc → stripped resource-id
            text = node.attrs.get("text") or node.attrs.get("content-desc") or ""
            if not text and node.attrs.get("resource-id"):
                text = self._strip_package_prefix(node.attrs["resource-id"])
            if self.translator is not None:
                text = self._translate(text)
            words = self._slug_words(text)[:5]
            base = "_".join(words) if words else "element"

        name = self._sanitize_name(f"{base}{suffix}")
        i = 1
        original = name
        while name in used_names:
            name = f"{original}_{i}"
            i += 1
        if name in keyword.kwlist:
            name = name + "_"
        return name

    def _slug_words(self, s: str) -> list[str]:
        """Break a string into lowercase slug words.

        Args:
            s (str): Input string

        Returns:
            List[str]: List of slug words

        """
        self.logger.debug("%s", get_current_func_name())
        parts = re.split(r"[^\w]+", anyascii(s))
        return [p.lower() for p in parts if p]

    def _strip_package_prefix(self, resource_id: str) -> str:
        """Strip package prefix from resource ID.

        Args:
            resource_id (str): Full resource ID

        Returns:
            str: Resource ID without package prefix

        """
        self.logger.debug("%s", get_current_func_name())
        return resource_id.split("/", 1)[-1] if "/" in resource_id else resource_id

    def _sanitize_name(self, raw_name: str) -> str:
        """Create a valid Python property name.

        Args:
            raw_name (str): Raw property name

        Returns:
            str: Sanitized property name

        """
        self.logger.debug("%s", get_current_func_name())
        name = re.sub(r"[^\w]", "_", raw_name)
        if name and name[0].isdigit():
            name = "num_" + name
        return name

    def _class_name_to_file_name(self, class_name: str) -> str:
        """Convert CamelCase class name to snake_case file name.

        Args:
            class_name (str): Class name in CamelCase

        Returns:
            str: File name in snake_case with .py extension

        """
        self.logger.debug("%s", get_current_func_name())

        step = "Convert CamelCase to snake_case"
        self.logger.debug("[%s] started", step)
        file_name = re.sub(r"(?<!^)(?=[A-Z])", "_", class_name).lower()
        return f"{file_name}.py"

    def _is_need_recycler(self, recycler: UiElementNode | None, regular_properties: list[UiElementNode]) -> bool:
        """Determine if recycler is needed by checking if any regular properties use it.

        Args:
            recycler (Optional[UiElementNode]): Recycler node if found
            regular_properties (List[UiElementNode]): Regular properties

        Returns:
            bool: Whether recycler is needed

        """
        self.logger.debug("%s", get_current_func_name())
        if not recycler:
            return False

        recycler_id = recycler.id
        return any(
            node.scrollable_parents and recycler_id in node.scrollable_parents
            for node in regular_properties if node.scrollable_parents
        )

    def _filter_properties(
            self,
            properties: list[dict[str, Any]],
            title_id: str | None,
            recycler_id: str | None,
    ) -> list[dict[str, Any]]:
        """Filter out redundant properties, but preserve title and recycler.

        Args:
            properties (List[Dict[str, Any]]): Raw property list.
            title_id (Optional[str]): ID of the title node.
            recycler_id (Optional[str]): ID of the recycler node.

        Returns:
            List[Dict[str, Any]]: Cleaned list of properties.

        """
        self.logger.debug("%s", get_current_func_name())

        step = "Filter class-only properties"
        self.logger.debug("[%s] started", step)
        properties = self._filter_class_only_properties(properties)

        step = "Filter structural containers"
        self.logger.debug("[%s] started", step)
        properties = self._filter_structural_containers(properties)

        # ⛔ Protection from removing title and recycler
        step = "Protect title and recycler"
        self.logger.debug("[%s] started", step)

        def is_important(prop: dict[str, Any]) -> bool:
            return prop.get("element_id") in {title_id, recycler_id}

        final: list[dict[str, Any]] = []
        for prop in properties:
            if is_important(prop):
                final.append(prop)  # type: ignore[arg-type]
                continue
            # Other filtering (if you add more steps - insert here)
            final.append(prop)  # type: ignore[arg-type]

        self.logger.debug("%s > final=%s", get_current_func_name(), final)  # type: ignore[arg-type]
        return final

    def _filter_class_only_properties(self, properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove properties where the locator contains only 'class' and no other meaningful attributes.

        Args:
            properties (List[Dict[str, Any]]): List of property dictionaries.

        Returns:
            List[Dict[str, Any]]: Filtered property list.

        """
        self.logger.debug("%s", get_current_func_name())

        filtered: list[dict[str, Any]] = []
        for prop in properties:
            locator = prop.get("locator", {})
            if list(locator.keys()) == ["class"]:
                self.logger.debug("Removing class-only locator: %s (%s)", prop["name"], locator["class"])
                continue
            filtered.append(prop)  # type: ignore[arg-type]

        return filtered

    def _filter_structural_containers(self, properties: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Remove non-interactive structural container elements like FrameLayout, LinearLayout, etc.

        Args:
            properties (List[Dict[str, Any]]): List of property dictionaries.

        Returns:
            List[Dict[str, Any]]: Filtered property list.

        """
        self.logger.debug("%s", get_current_func_name())

        filtered: list[dict[str, Any]] = []
        for prop in properties:
            locator = prop.get("locator", {})
            cls = locator.get("class")
            res_id = locator.get("resource-id", "")

            # Class is a known container, and either no id, or id is known to be layout-only
            if cls in self.STRUCTURAL_CLASSES and (not res_id or res_id in self.CONTAINER_IDS):
                self.logger.debug("Removing structural container: %s (%s, %s)", prop["name"], cls, res_id)
                continue

            filtered.append(prop)  # type: ignore[arg-type]

        return filtered


def _pretty_dict(d: dict[str, Any], base_indent: int = 8) -> str:
    """Format dict in Python style: each key on new line, aligned by indentation."""
    lines = ["{"]
    indent = " " * base_indent
    for i, (k, v) in enumerate(d.items()):
        line = f"{indent!s}{k!r}: {v!r}"
        if i < len(d) - 1:
            line += ","
        lines.append(line)
    lines.append(" " * (base_indent - 4) + "}")
    return "\n".join(lines)
