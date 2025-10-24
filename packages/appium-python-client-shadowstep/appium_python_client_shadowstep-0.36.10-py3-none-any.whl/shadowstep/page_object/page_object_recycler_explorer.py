"""Page object recycler explorer for Shadowstep framework.

This module provides the PageObjectRecyclerExplorer class for
automatically exploring scrollable content in mobile applications
by generating page objects for different scroll positions and
merging them into a comprehensive page object.
"""

from __future__ import annotations

import importlib.util
import logging
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

from shadowstep.exceptions.shadowstep_exceptions import (
    ShadowstepPageObjectError,
    ShadowstepTerminalNotInitializedError,
)
from shadowstep.page_object.page_object_generator import PageObjectGenerator
from shadowstep.page_object.page_object_merger import PageObjectMerger
from shadowstep.page_object.page_object_parser import PageObjectParser
from shadowstep.utils.utils import get_current_func_name

if TYPE_CHECKING:
    from shadowstep.shadowstep import Shadowstep


class PageObjectRecyclerExplorer:
    """Explorer for scrollable content in mobile applications.

    This class provides functionality to automatically explore scrollable
    content by generating page objects for different scroll positions
    and merging them into a comprehensive page object.
    """

    def __init__(self, base: Shadowstep, translator: Any) -> None:
        """Initialize the PageObjectRecyclerExplorer.

        Args:
            base: Shadowstep instance for automation operations.
            translator: Translator instance for text translation, must contain def translate(text: str) -> str.

        """
        self.base: Shadowstep = base
        self.logger = logging.getLogger(__name__)
        self.parser = PageObjectParser()
        self.generator = PageObjectGenerator(translator)
        self.merger = PageObjectMerger()

    def explore(self, output_dir: str, timeout: float = 360) -> Path:  # noqa: C901, PLR0915
        """Explore recycler views and generate page objects.

        Args:
            output_dir: Directory to save generated page objects.
            timeout: Timeout for scrolling

        Returns:
            Path: Path to the generated file.

        Raises:
            ValueError: If terminal is not initialized.

        """
        self.logger.info("%s", get_current_func_name())
        if self.base.terminal is None:  # type: ignore[comparison-overlap]
            raise ShadowstepTerminalNotInitializedError
        width, height = self.base.terminal.get_screen_resolution()
        x = width // 2
        y_start = int(height * 0.2)
        y_end = int(height * 0.8)
        for _ in range(9):
            self.base.swipe(
                left=100,
                top=100,
                width=width,
                height=height,
                direction="down",
                percent=1.0,
                speed=10000,
            )  # scroll up
            self.base.terminal.adb_shell(
                command="input",
                args=f"swipe {x} {y_start} {x} {y_end}",
            )

        pages = []
        original_tree = self.parser.parse(self.base.driver.page_source)
        original_page_path, original_page_class_name = self.generator.generate(
            original_tree,
            output_dir=output_dir,
        )
        pages.append((original_page_path, original_page_class_name))  # type: ignore[reportUnknownMemberType]

        original_cls = self._load_class_from_file(original_page_path, original_page_class_name)
        if not original_cls:
            self.logger.warning(
                "Failed to load class %s from %s",
                original_page_class_name,
                original_page_path,
            )
            raise ShadowstepPageObjectError

        original_page = original_cls()
        if not hasattr(original_page, "recycler"):
            self.logger.info("%s does not contain `recycler` property", original_page_class_name)
            raise ShadowstepPageObjectError

        recycler_el = original_page.recycler
        if not hasattr(recycler_el, "scroll_down"):
            self.logger.warning("`recycler` does not support scroll_down")
            raise ShadowstepPageObjectError
        prefix = 0

        start_time = time.monotonic()
        while recycler_el.scroll_down(percent=0.5, speed=1000, return_bool=True):
            if time.monotonic() - start_time > timeout:
                self.logger.warning("Timeout reached while scrolling recycler")
                break

            # tree changed!!! recycler_raw needs to be redefined
            prefix += 1
            tree = self.parser.parse(self.base.driver.page_source)
            page_path, page_class_name = self.generator.generate(
                tree,
                output_dir=output_dir,
                filename_prefix=str(prefix),
            )
            pages.append((page_path, page_class_name))  # type: ignore[reportUnknownMemberType]

        width, height = self.base.terminal.get_screen_resolution()
        x = width // 2
        y_start = int(height * 0.8)
        y_end = int(height * 0.2)
        for _ in range(9):
            self.base.swipe(
                left=100,
                top=100,
                width=width,
                height=height,
                direction="up",
                percent=1.0,
                speed=10000,
            )  # scroll up
            self.base.terminal.adb_shell(
                command="input",
                args=f"swipe {x} {y_start} {x} {y_end}",
            )
        prefix += 1
        tree = self.parser.parse(self.base.driver.page_source)
        page_path, page_class_name = self.generator.generate(
            tree,
            output_dir=output_dir,
            filename_prefix=str(prefix),
        )
        pages.append((page_path, page_class_name))  # type: ignore[reportUnknownMemberType]

        output_path = Path("merged_pages") / original_page_path.name
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self.merger.merge(original_page_path, cast("str", pages[0][0]), output_path)

        for page_tuple in pages:  # type: ignore[reportUnknownVariableType]
            page_path, page_class_name = cast("tuple[Path, str]", page_tuple)
            self.merger.merge(output_path, page_path, output_path)

        for _ in range(5):
            self.base.swipe(
                left=100,
                top=100,
                width=width,
                height=height,
                direction="up",
                percent=1.0,
                speed=10000,
            )  # scroll down

        return output_path

    def _load_class_from_file(self, path: str | Path, class_name: str) -> type | None:
        spec = importlib.util.spec_from_file_location("loaded_po", path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return getattr(module, class_name, None)
