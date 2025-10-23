"""
Base Element Class for UI Test Automation

Provides enhanced element interaction capabilities with built-in retry logic,
smart waiting, and comprehensive error handling. Complements the BasePage class
by offering element-level operations.

Extracted from production tests for reuse across CXE services.
"""

from datetime import datetime
from typing import Any, Callable, Dict, Optional

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from ..utils.logger import LoggerConfig
from .waits import WaitCondition, WaitHelpers


class BaseElement:
    """
    Enhanced element wrapper providing intelligent interactions.

    Encapsulates Playwright Locator with smart waiting, retry mechanisms,
    and comprehensive error handling for reliable UI automation.
    """

    def __init__(
        self, page: Page, selector: str, name: Optional[str] = None, timeout: Optional[int] = None
    ):
        """
        Initialize BaseElement with page and selector.

        Args:
            page (Page): Playwright page instance
            selector (str): CSS selector or data-testid
            name (str, optional): Human-readable element name for logging
            timeout (int, optional): Custom timeout for this element
        """
        self.page = page
        self.selector = selector
        self.name = name or selector
        self.timeout = timeout or 30000
        self.logger = LoggerConfig.get_logger(f"{self.__class__.__name__}[{self.name}]")
        self.wait_helpers = WaitHelpers(page)

        # Internal state tracking
        self._last_interaction_time = None
        self._interaction_count = 0
        self._cache = {}

    @property
    def locator(self) -> Locator:
        """Get fresh Playwright locator for the element."""
        return self.page.locator(self.selector).first

    def is_visible(self, timeout: Optional[int] = None) -> bool:
        """
        Check if element is visible.

        Args:
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            bool: True if element is visible
        """
        try:
            timeout = timeout or (self.timeout // 2)  # Use shorter timeout for checks
            expect(self.locator).to_be_visible(timeout=timeout)
            return True
        except Exception:
            return False

    def is_enabled(self, timeout: Optional[int] = None) -> bool:
        """
        Check if element is enabled.

        Args:
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            bool: True if element is enabled
        """
        try:
            timeout = timeout or (self.timeout // 2)
            expect(self.locator).to_be_enabled(timeout=timeout)
            return True
        except Exception:
            return False

    def is_clickable(self, timeout: Optional[int] = None) -> bool:
        """
        Check if element is clickable (visible and enabled).

        Args:
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            bool: True if element is clickable
        """
        return self.wait_helpers.wait_for_element_clickable(self.selector, timeout or self.timeout)

    def wait_for_visible(
        self, timeout: Optional[int] = None, retry_count: int = 3
    ) -> "BaseElement":
        """
        Wait for element to become visible with retry logic.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining

        Raises:
            Exception: If element doesn't become visible after retries
        """
        timeout = timeout or self.timeout

        if not self.wait_helpers.wait_for_element_visible(self.selector, timeout, retry_count):
            self.logger.error(f"Element '{self.name}' not visible after {retry_count} retries")
            raise PlaywrightTimeoutError(f"Element '{self.name}' not visible")

        self.logger.debug(f"Element '{self.name}' is visible")
        return self

    def wait_for_clickable(
        self, timeout: Optional[int] = None, retry_count: int = 3
    ) -> "BaseElement":
        """
        Wait for element to become clickable with retry logic.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        if not self.wait_helpers.wait_for_element_clickable(self.selector, timeout, retry_count):
            self.logger.error(f"Element '{self.name}' not clickable after {retry_count} retries")
            raise PlaywrightTimeoutError(f"Element '{self.name}' not clickable")

        self.logger.debug(f"Element '{self.name}' is clickable")
        return self

    def click(
        self, force: bool = False, timeout: Optional[int] = None, retry_count: int = 2
    ) -> "BaseElement":
        """
        Click element with intelligent waiting and retry logic.

        Args:
            force (bool): Whether to force click even if not actionable
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def click_operation():
            if not force:
                self.wait_for_clickable(timeout // (retry_count + 1))

            self.locator.click(force=force, timeout=timeout // (retry_count + 1))
            self._track_interaction("click")
            self.logger.debug(f"Clicked element '{self.name}'")

        return self._retry_operation(click_operation, retry_count, f"click on '{self.name}'")

    def double_click(self, timeout: Optional[int] = None, retry_count: int = 2) -> "BaseElement":
        """
        Double-click element with retry logic.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def double_click_operation():
            self.wait_for_clickable(timeout // (retry_count + 1))
            self.locator.dblclick(timeout=timeout // (retry_count + 1))
            self._track_interaction("double_click")
            self.logger.debug(f"Double-clicked element '{self.name}'")

        return self._retry_operation(
            double_click_operation, retry_count, f"double-click on '{self.name}'"
        )

    def type_text(
        self,
        text: str,
        clear: bool = True,
        delay: Optional[int] = None,
        timeout: Optional[int] = None,
        retry_count: int = 2,
    ) -> "BaseElement":
        """
        Type text into element with retry logic.

        Args:
            text (str): Text to type
            clear (bool): Whether to clear existing text first
            delay (int, optional): Delay between keystrokes in milliseconds
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def type_operation():
            self.wait_for_visible(timeout // (retry_count + 1))

            if clear:
                self.locator.clear(timeout=timeout // (retry_count + 1))

            type_options = {"timeout": timeout // (retry_count + 1)}
            if delay is not None:
                type_options["delay"] = delay

            self.locator.type(text, **type_options)
            self._track_interaction("type")
            self.logger.debug(f"Typed text into '{self.name}': {text}")

        return self._retry_operation(type_operation, retry_count, f"type text into '{self.name}'")

    def fill(self, text: str, timeout: Optional[int] = None, retry_count: int = 2) -> "BaseElement":
        """
        Fill element with text (faster than typing).

        Args:
            text (str): Text to fill
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def fill_operation():
            self.wait_for_visible(timeout // (retry_count + 1))
            self.locator.fill(text, timeout=timeout // (retry_count + 1))
            self._track_interaction("fill")
            self.logger.debug(f"Filled element '{self.name}' with: {text}")

        return self._retry_operation(fill_operation, retry_count, f"fill '{self.name}'")

    def get_text(self, timeout: Optional[int] = None, retry_count: int = 2) -> str:
        """
        Get text content from element.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            str: Element text content
        """
        timeout = timeout or self.timeout

        def get_text_operation():
            self.wait_for_visible(timeout // (retry_count + 1))
            text = self.locator.text_content(timeout=timeout // (retry_count + 1))
            self.logger.debug(f"Retrieved text from '{self.name}': {text}")
            return text or ""

        return self._retry_operation(
            get_text_operation, retry_count, f"get text from '{self.name}'"
        )

    def get_inner_text(self, timeout: Optional[int] = None, retry_count: int = 2) -> str:
        """
        Get inner text from element (excludes hidden elements).

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            str: Element inner text
        """
        timeout = timeout or self.timeout

        def get_inner_text_operation():
            self.wait_for_visible(timeout // (retry_count + 1))
            text = self.locator.inner_text(timeout=timeout // (retry_count + 1))
            self.logger.debug(f"Retrieved inner text from '{self.name}': {text}")
            return text or ""

        return self._retry_operation(
            get_inner_text_operation, retry_count, f"get inner text from '{self.name}'"
        )

    def get_attribute(
        self, attribute: str, timeout: Optional[int] = None, retry_count: int = 2
    ) -> Optional[str]:
        """
        Get attribute value from element.

        Args:
            attribute (str): Attribute name
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            str: Attribute value or None if not found
        """
        timeout = timeout or self.timeout

        def get_attribute_operation():
            value = self.locator.get_attribute(attribute, timeout=timeout // (retry_count + 1))
            self.logger.debug(f"Retrieved {attribute} from '{self.name}': {value}")
            return value

        return self._retry_operation(
            get_attribute_operation, retry_count, f"get {attribute} from '{self.name}'"
        )

    def select_option(
        self,
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        timeout: Optional[int] = None,
        retry_count: int = 2,
    ) -> "BaseElement":
        """
        Select option from dropdown/select element.

        Args:
            value (str, optional): Option value to select
            label (str, optional): Option label to select
            index (int, optional): Option index to select
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def select_operation():
            self.wait_for_visible(timeout // (retry_count + 1))

            if value is not None:
                self.locator.select_option(value=value, timeout=timeout // (retry_count + 1))
                self.logger.debug(f"Selected option by value in '{self.name}': {value}")
            elif label is not None:
                self.locator.select_option(label=label, timeout=timeout // (retry_count + 1))
                self.logger.debug(f"Selected option by label in '{self.name}': {label}")
            elif index is not None:
                self.locator.select_option(index=index, timeout=timeout // (retry_count + 1))
                self.logger.debug(f"Selected option by index in '{self.name}': {index}")
            else:
                raise ValueError("Must provide value, label, or index for selection")

            self._track_interaction("select")

        return self._retry_operation(
            select_operation, retry_count, f"select option in '{self.name}'"
        )

    def check(self, timeout: Optional[int] = None, retry_count: int = 2) -> "BaseElement":
        """
        Check checkbox or radio button.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def check_operation():
            self.wait_for_visible(timeout // (retry_count + 1))
            self.locator.check(timeout=timeout // (retry_count + 1))
            self._track_interaction("check")
            self.logger.debug(f"Checked element '{self.name}'")

        return self._retry_operation(check_operation, retry_count, f"check '{self.name}'")

    def uncheck(self, timeout: Optional[int] = None, retry_count: int = 2) -> "BaseElement":
        """
        Uncheck checkbox or radio button.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def uncheck_operation():
            self.wait_for_visible(timeout // (retry_count + 1))
            self.locator.uncheck(timeout=timeout // (retry_count + 1))
            self._track_interaction("uncheck")
            self.logger.debug(f"Unchecked element '{self.name}'")

        return self._retry_operation(uncheck_operation, retry_count, f"uncheck '{self.name}'")

    def scroll_into_view(
        self, timeout: Optional[int] = None, retry_count: int = 2
    ) -> "BaseElement":
        """
        Scroll element into view.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def scroll_operation():
            self.locator.scroll_into_view_if_needed(timeout=timeout // (retry_count + 1))
            self._track_interaction("scroll")
            self.logger.debug(f"Scrolled '{self.name}' into view")

        return self._retry_operation(
            scroll_operation, retry_count, f"scroll '{self.name}' into view"
        )

    def hover(self, timeout: Optional[int] = None, retry_count: int = 2) -> "BaseElement":
        """
        Hover over element.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        def hover_operation():
            self.wait_for_visible(timeout // (retry_count + 1))
            self.locator.hover(timeout=timeout // (retry_count + 1))
            self._track_interaction("hover")
            self.logger.debug(f"Hovered over '{self.name}'")

        return self._retry_operation(hover_operation, retry_count, f"hover over '{self.name}'")

    def wait_for_condition(
        self, condition: WaitCondition, timeout: Optional[int] = None
    ) -> "BaseElement":
        """
        Wait for element to meet specific condition.

        Args:
            condition (WaitCondition): Condition to wait for
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        if not self.wait_helpers._wait_for_element_condition(
            self.selector, condition, timeout, retry_count=3
        ):
            raise PlaywrightTimeoutError(
                f"Element '{self.name}' did not meet condition: {condition.value}"
            )

        self.logger.debug(f"Element '{self.name}' met condition: {condition.value}")
        return self

    def wait_for_text_to_contain(self, text: str, timeout: Optional[int] = None) -> "BaseElement":
        """
        Wait for element text to contain specific text.

        Args:
            text (str): Text to wait for
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        try:
            expect(self.locator).to_contain_text(text, timeout=timeout)
            self.logger.debug(f"Element '{self.name}' contains text: {text}")
            return self
        except PlaywrightTimeoutError:
            current_text = self.get_text()
            self.logger.error(
                f"Element '{self.name}' does not contain '{text}'. Current text: '{current_text}'"
            )
            raise

    def assert_visible(self, timeout: Optional[int] = None) -> "BaseElement":
        """
        Assert element is visible (raises exception if not).

        Args:
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        try:
            expect(self.locator).to_be_visible(timeout=timeout)
            self.logger.debug(f"Assertion passed: '{self.name}' is visible")
            return self
        except AssertionError:
            self.logger.error(f"Assertion failed: '{self.name}' is not visible")
            raise

    def assert_text_equals(
        self, expected_text: str, timeout: Optional[int] = None
    ) -> "BaseElement":
        """
        Assert element text equals expected value.

        Args:
            expected_text (str): Expected text value
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        try:
            expect(self.locator).to_have_text(expected_text, timeout=timeout)
            self.logger.debug(f"Assertion passed: '{self.name}' text equals '{expected_text}'")
            return self
        except AssertionError:
            actual_text = self.get_text()
            self.logger.error(
                f"Assertion failed: '{self.name}' text. Expected: '{expected_text}', Actual: '{actual_text}'"  # noqa: E501
            )
            raise

    def assert_text_contains(
        self, expected_text: str, timeout: Optional[int] = None
    ) -> "BaseElement":
        """
        Assert element text contains expected value.

        Args:
            expected_text (str): Expected text to contain
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            BaseElement: Self for method chaining
        """
        timeout = timeout or self.timeout

        try:
            expect(self.locator).to_contain_text(expected_text, timeout=timeout)
            self.logger.debug(f"Assertion passed: '{self.name}' contains text '{expected_text}'")
            return self
        except AssertionError:
            actual_text = self.get_text()
            self.logger.error(
                f"Assertion failed: '{self.name}' does not contain '{expected_text}'. Actual: '{actual_text}'"  # noqa: E501
            )
            raise

    def get_stats(self) -> Dict[str, Any]:
        """
        Get interaction statistics for this element.

        Returns:
            Dict[str, Any]: Element interaction statistics
        """
        return {
            "selector": self.selector,
            "name": self.name,
            "interaction_count": self._interaction_count,
            "last_interaction": self._last_interaction_time,
            "timeout": self.timeout,
        }

    def _retry_operation(
        self, operation: Callable, retry_count: int, operation_name: str
    ) -> "BaseElement":
        """
        Execute operation with retry logic.

        Args:
            operation (Callable): Operation to retry
            retry_count (int): Number of retry attempts
            operation_name (str): Operation description for logging

        Returns:
            BaseElement: Self for method chaining
        """
        last_exception = None

        for attempt in range(retry_count + 1):
            try:
                result = operation()
                if attempt > 0:
                    self.logger.info(
                        f"Operation '{operation_name}' succeeded on attempt {attempt + 1}"
                    )
                return self if result is None else result

            except Exception as e:
                last_exception = e

                if attempt < retry_count:
                    wait_time = 0.5 * (attempt + 1)  # Progressive backoff
                    self.logger.warning(
                        f"Operation '{operation_name}' failed on attempt {attempt + 1}, "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    self.page.wait_for_timeout(int(wait_time * 1000))
                else:
                    self.logger.error(
                        f"Operation '{operation_name}' failed after {retry_count + 1} attempts: {str(e)}"  # noqa: E501
                    )

        # Take screenshot on final failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_name = f"element_operation_failed_{self.name.replace(' ', '_')}_{timestamp}"
        try:
            self.page.screenshot(path=f"./reports/screenshots/{screenshot_name}.png")
        except Exception:  # noqa: E722
            pass  # Don't fail the test if screenshot fails

        raise last_exception

    def _track_interaction(self, interaction_type: str) -> None:
        """Track element interaction for statistics."""
        self._interaction_count += 1
        self._last_interaction_time = datetime.now().isoformat()
        self.logger.debug(
            f"Interaction tracked: {interaction_type} on '{self.name}' (count: {self._interaction_count})"  # noqa: E501
        )


class ElementFactory:
    """
    Factory class for creating BaseElement instances with consistent configuration.
    """

    def __init__(self, page: Page, default_timeout: Optional[int] = None):
        """
        Initialize element factory.

        Args:
            page (Page): Playwright page instance
            default_timeout (int, optional): Default timeout for elements
        """
        self.page = page
        self.default_timeout = default_timeout or 30000
        self.created_elements = {}

    def create_element(
        self, selector: str, name: Optional[str] = None, timeout: Optional[int] = None
    ) -> BaseElement:
        """
        Create or retrieve cached BaseElement instance.

        Args:
            selector (str): Element selector
            name (str, optional): Element name
            timeout (int, optional): Custom timeout

        Returns:
            BaseElement: Configured element instance
        """
        element_key = f"{selector}::{name or selector}"

        if element_key not in self.created_elements:
            self.created_elements[element_key] = BaseElement(
                self.page, selector, name, timeout or self.default_timeout
            )

        return self.created_elements[element_key]

    def get_element_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all created elements."""
        return {key: element.get_stats() for key, element in self.created_elements.items()}

    def clear_cache(self) -> None:
        """Clear element cache."""
        self.created_elements.clear()
