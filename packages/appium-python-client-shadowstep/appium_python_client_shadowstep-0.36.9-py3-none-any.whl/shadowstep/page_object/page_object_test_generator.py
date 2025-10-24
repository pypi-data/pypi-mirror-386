"""Page object test generator for Shadowstep framework.

This module provides the PageObjectTestGenerator class for automatically
generating test classes based on existing page objects, creating
visibility checks for all page properties using pytest framework.
"""
import ast
import logging
import os
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from shadowstep.exceptions.shadowstep_exceptions import ShadowstepNoClassDefinitionFoundInTreeError
from shadowstep.utils.utils import get_current_func_name


class PageObjectTestGenerator:
    """Generate basic test class for PageObject.

    This class is used to create a simple test based on an already generated PageObject.
    It goes through page properties and forms an autotest that checks that elements are displayed on screen.

    Uses Jinja2 template, test is written to file, for example: `tests/pages/test_login_page.py`.

    Strategy:
        - gets class or list of PageObject properties;
        - for each element generates `.is_visible()` check;
        - saves template to file (with overwrite check).

    Example:
        source = app.driver.page_source
        tree = parser.parse(source)
        path, class_name = POG.generate(ui_element_tree=tree,
                     output_dir="pages")
        test_generator = PageObjectTestGenerator()
        test_path, test_class_name = test_generator.generate_test(input_path=path, class_name=class_name, output_dir="pages")

    Generation result:
        imports

        @pytest.fixture()
        def page_object_instance():
            # here PageObject instance is created
            yield PageObject

        class TestPageExample:
            def test_title(page_object_instance):
                page_object_instance.title.is_visible()


    """

    def __init__(self) -> None:
        """Initialize the PageObjectTestGenerator."""
        self.logger = logging.getLogger(__name__)
        templates_dir = Path(__file__).parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(templates_dir),
            autoescape=True,
            keep_trailing_newline=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def generate_test(self, input_path: str, class_name: str, output_dir: str) -> tuple[str, str]:
        """Generate test file for page object class.

        Args:
            input_path: Path to the page object file.
            class_name: Name of the page object class.
            output_dir: Directory to save the test file.

        Returns:
            tuple[str, str]: (test_file_path, test_class_name).

        """
        self.logger.debug("%s", get_current_func_name())

        step = "Extracting module name"
        self.logger.debug("[%s] started", step)
        module_path = input_path \
            .replace(os.sep, ".") \
            .removesuffix(".py")

        step = "Extracting properties from file"
        self.logger.debug("[%s] started", step)
        with Path(input_path).open(encoding="utf-8") as f:
            source = f.read()
        properties = self._extract_properties(source)

        step = "Preparing data for template"
        self.logger.debug("[%s] started", step)
        test_class_name = f"Test{class_name}"
        template = self.env.get_template("page_object_test.py.j2")
        rendered = template.render(
            module_path=module_path,
            class_name=class_name,
            test_class_name=test_class_name,
            properties=properties,
        )

        step = "Forming test path"
        self.logger.debug("[%s] started", step)
        test_file_name = f"test_{self._camel_to_snake(class_name)}.py"
        test_path = Path(output_dir) / test_file_name

        step = "Writing file"
        self.logger.debug("[%s] started", step)
        with test_path.open("w", encoding="utf-8") as f:
            f.write(rendered)

        self.logger.info("Generated test → %s", test_path)
        return str(test_path), test_class_name

    def _extract_properties(self, source: str) -> list[str]:
        """Parse Python AST and extract list of class properties."""
        tree = ast.parse(source)
        class_node = next((n for n in tree.body if isinstance(n, ast.ClassDef)), None)
        if not class_node:
            raise ShadowstepNoClassDefinitionFoundInTreeError

        ignore = {"name", "edges", "title", "recycler", "is_current_page"}
        return [
            node.name
            for node in class_node.body
            if isinstance(node, ast.FunctionDef)
               and any(isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list)
               and node.name not in ignore
        ]

    def _camel_to_snake(self, name: str) -> str:
        return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()
