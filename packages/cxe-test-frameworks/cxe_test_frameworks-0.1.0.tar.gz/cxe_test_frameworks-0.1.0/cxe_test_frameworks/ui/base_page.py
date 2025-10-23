"""
Base Page Object for UI Test Automation

Implements the Page Object Model (POM) pattern with common functionality
for Playwright-based UI tests.
"""

import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Literal, Optional

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect

from .assertions import AssertionUtils
from .waits import WaitHelpers


class BasePage(ABC):
    """
    Base class for all page objects implementing common functionality.

    Provides shared methods for navigation, element interaction, waiting,
    screenshots, and error handling.
    """

    def __init__(self, page: Page, config: Optional[Dict] = None):
        """
        Initialize base page with Playwright page instance and configuration.

        Args:
            page (Page): Playwright page instance
            config (Dict, optional): Page-specific configuration
        """
        self.page = page
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30000)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.wait_helpers = WaitHelpers(page)
        self.assertions = AssertionUtils(page)

        # Common selectors that might be used across pages
        self.common_selectors = {
            "loading_spinner": '[data-testid="loading-spinner"]',
            "error_message": '[data-testid="error-message"]',
            "success_message": '[data-testid="success-message"]',
            "modal_dialog": '[data-testid="modal-dialog"]',
            "close_button": '[data-testid="close-button"]',
        }

    @property
    @abstractmethod
    def page_url(self) -> str:
        """Abstract property that must be implemented by child classes."""
        pass

    @property
    @abstractmethod
    def page_title(self) -> str:
        """Abstract property that must be implemented by child classes."""
        pass

    @abstractmethod
    def verify_page_loaded(self) -> bool:
        """Abstract method to verify page has loaded correctly."""
        pass

    # Navigation Methods

    def navigate_to(self, url: Optional[str] = None, wait_for_load: bool = True) -> None:
        """
        Navigate to specified URL or page's default URL.

        Args:
            url (str, optional): URL to navigate to. If None, uses page_url
            wait_for_load (bool): Whether to wait for page load completion

        Raises:
            PlaywrightTimeoutError: If navigation times out
        """
        target_url = url or self.page_url

        try:
            self.logger.info(f"Navigating to: {target_url}")
            self.page.goto(target_url, timeout=self.timeout)

            if wait_for_load:
                self.wait_for_page_load()

            self.logger.info(f"Successfully navigated to: {target_url}")

        except PlaywrightTimeoutError as e:
            self.logger.error(f"Navigation timeout to {target_url}: {str(e)}")
            self.take_screenshot(f"navigation_timeout_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            raise
        except Exception as e:
            self.logger.error(f"Navigation error to {target_url}: {str(e)}")
            raise

    def reload_page(self, wait_for_load: bool = True) -> None:
        """
        Reload the current page.

        Args:
            wait_for_load (bool): Whether to wait for page load completion
        """
        try:
            self.logger.info("Reloading page")
            self.page.reload(timeout=self.timeout)

            if wait_for_load:
                self.wait_for_page_load()

            self.logger.info("Page reloaded successfully")

        except Exception as e:
            self.logger.error(f"Page reload error: {str(e)}")
            raise

    # Element Interaction Methods

    def find_element(self, selector: str, timeout: Optional[int] = None) -> Locator:
        """
        Find element by selector with optional timeout.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            Locator: Playwright locator for the element
        """
        timeout = timeout or self.timeout
        return self.page.locator(selector).first

    def click_element(
        self, selector: str, timeout: Optional[int] = None, force: bool = False
    ) -> None:
        """
        Click element with retry logic and error handling.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds
            force (bool): Whether to force click even if element is not actionable
        """
        try:
            element = self.find_element(selector, timeout)
            self.wait_helpers.wait_for_element_clickable(selector, timeout)

            self.logger.debug(f"Clicking element: {selector}")
            element.click(force=force, timeout=timeout or self.timeout)

        except Exception as e:
            self.logger.error(f"Click failed for {selector}: {str(e)}")
            self.take_screenshot(f"click_failed_{selector.replace('[', '').replace(']', '')}")
            raise

    def type_text(
        self, selector: str, text: str, clear: bool = True, timeout: Optional[int] = None
    ) -> None:
        """
        Type text into input element.

        Args:
            selector (str): CSS selector or data-testid
            text (str): Text to type
            clear (bool): Whether to clear existing text first
            timeout (int, optional): Custom timeout in milliseconds
        """
        try:
            element = self.find_element(selector, timeout)
            self.wait_helpers.wait_for_element_visible(selector, timeout)

            if clear:
                element.clear(timeout=timeout or self.timeout)

            self.logger.debug(f"Typing text into {selector}: {text}")
            element.type(text, timeout=timeout or self.timeout)

        except Exception as e:
            self.logger.error(f"Type text failed for {selector}: {str(e)}")
            raise

    def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        """
        Get text content from element.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            str: Element text content
        """
        try:
            element = self.find_element(selector, timeout)
            self.wait_helpers.wait_for_element_visible(selector, timeout)

            text = element.text_content(timeout=timeout or self.timeout)
            self.logger.debug(f"Retrieved text from {selector}: {text}")
            return text or ""

        except Exception as e:
            self.logger.error(f"Get text failed for {selector}: {str(e)}")
            raise

    def get_attribute(
        self, selector: str, attribute: str, timeout: Optional[int] = None
    ) -> Optional[str]:
        """
        Get attribute value from element.

        Args:
            selector (str): CSS selector or data-testid
            attribute (str): Attribute name
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            str: Attribute value or None if not found
        """
        try:
            element = self.find_element(selector, timeout)
            value = element.get_attribute(attribute, timeout=timeout or self.timeout)
            self.logger.debug(f"Retrieved {attribute} from {selector}: {value}")
            return value

        except Exception as e:
            self.logger.error(f"Get attribute failed for {selector}.{attribute}: {str(e)}")
            raise

    # Wait Methods

    def wait_for_page_load(self, timeout: Optional[int] = None) -> None:
        """
        Wait for page to fully load.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
        """
        timeout = timeout or self.timeout

        try:
            # Wait for network idle and DOM content loaded
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

            # Wait for any loading spinners to disappear
            if self.page.locator(self.common_selectors["loading_spinner"]).count() > 0:
                self.wait_helpers.wait_for_element_hidden(
                    self.common_selectors["loading_spinner"], timeout
                )

            self.logger.debug("Page load completed")

        except PlaywrightTimeoutError:
            self.logger.warning(f"Page load timeout after {timeout}ms")
            raise

    def wait_for_element(
        self,
        selector: str,
        state: Literal["attached", "detached", "hidden", "visible"] = "visible",
        timeout: Optional[int] = None,
    ) -> None:
        """
        Wait for element to reach specified state.

        Args:
            selector (str): CSS selector or data-testid
            state (str): Element state ('visible', 'hidden', 'attached', 'detached')
            timeout (int, optional): Custom timeout in milliseconds
        """
        timeout = timeout or self.timeout

        try:
            element = self.find_element(selector)
            element.wait_for(state=state, timeout=timeout)
            self.logger.debug(f"Element {selector} reached state: {state}")

        except PlaywrightTimeoutError:
            self.logger.error(f"Timeout waiting for {selector} to be {state}")
            raise

    # Assertion Methods

    def verify_element_visible(self, selector: str, timeout: Optional[int] = None) -> bool:
        """
        Verify element is visible on the page.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            bool: True if element is visible, False otherwise
        """
        try:
            element = self.find_element(selector)
            expect(element).to_be_visible(timeout=timeout or self.timeout)
            return True
        except Exception as e:
            self.logger.warning(f"Element {selector} not visible: {str(e)}")
            return False

    def verify_text_present(
        self, expected_text: str, selector: Optional[str] = None, timeout: Optional[int] = None
    ) -> bool:
        """
        Verify text is present on the page or in specific element.

        Args:
            expected_text (str): Text to look for
            selector (str, optional): Specific element to check. If None, checks entire page
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            bool: True if text is found, False otherwise
        """
        try:
            if selector:
                element = self.find_element(selector)
                expect(element).to_contain_text(expected_text, timeout=timeout or self.timeout)
            else:
                text_locator = self.page.locator(f"text={expected_text}").first
                expect(text_locator).to_be_visible(timeout=timeout or self.timeout)
            return True
        except Exception as e:
            self.logger.warning(f"Text '{expected_text}' not found: {str(e)}")
            return False

    def verify_url_contains(self, expected_url_part: str, timeout: Optional[int] = None) -> bool:
        """
        Verify current URL contains expected part.

        Args:
            expected_url_part (str): URL part to verify
            timeout (int, optional): Custom timeout in milliseconds

        Returns:
            bool: True if URL contains expected part, False otherwise
        """
        try:
            expect(self.page).to_have_url(f"*{expected_url_part}*", timeout=timeout or self.timeout)
            return True
        except Exception as e:
            self.logger.warning(f"URL does not contain '{expected_url_part}': {str(e)}")
            return False

    # Utility Methods

    def take_screenshot(self, name: str, full_page: bool = True) -> str:
        """
        Take screenshot of current page.

        Args:
            name (str): Screenshot file name (without extension)
            full_page (bool): Whether to capture full page or just viewport

        Returns:
            str: Path to saved screenshot
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{name}_{timestamp}.png"
            screenshot_path = f"./reports/screenshots/{filename}"

            self.page.screenshot(path=screenshot_path, full_page=full_page)
            self.logger.info(f"Screenshot saved: {screenshot_path}")
            return screenshot_path

        except Exception as e:
            self.logger.error(f"Screenshot failed: {str(e)}")
            raise

    def get_page_source(self) -> str:
        """
        Get current page HTML source.

        Returns:
            str: Page HTML source
        """
        try:
            source = self.page.content()
            self.logger.debug("Retrieved page source")
            return source
        except Exception as e:
            self.logger.error(f"Get page source failed: {str(e)}")
            raise

    def execute_javascript(self, script: str, *args) -> Any:
        """
        Execute JavaScript on the page.

        Args:
            script (str): JavaScript code to execute
            *args: Arguments to pass to the script

        Returns:
            Any: Result of JavaScript execution
        """
        try:
            result = self.page.evaluate(script, *args)
            self.logger.debug(f"Executed JavaScript: {script}")
            return result
        except Exception as e:
            self.logger.error(f"JavaScript execution failed: {str(e)}")
            raise

    def scroll_to_element(self, selector: str, timeout: Optional[int] = None) -> None:
        """
        Scroll element into view.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds
        """
        try:
            element = self.find_element(selector, timeout)
            element.scroll_into_view_if_needed(timeout=timeout or self.timeout)
            self.logger.debug(f"Scrolled to element: {selector}")
        except Exception as e:
            self.logger.error(f"Scroll to element failed for {selector}: {str(e)}")
            raise

    # Error Handling Methods

    def handle_error_dialog(self, action: str = "dismiss") -> bool:
        """
        Handle error dialogs that may appear.

        Args:
            action (str): Action to take ('dismiss', 'accept')

        Returns:
            bool: True if dialog was handled, False if no dialog found
        """
        try:
            if self.page.locator(self.common_selectors["modal_dialog"]).count() > 0:
                if action == "dismiss":
                    self.click_element(self.common_selectors["close_button"])
                self.logger.info(f"Handled error dialog with action: {action}")
                return True
            return False
        except Exception as e:
            self.logger.warning(f"Error dialog handling failed: {str(e)}")
            return False

    def get_error_message(self) -> Optional[str]:
        """
        Get error message if present on page.

        Returns:
            str: Error message text or None if no error found
        """
        try:
            if self.page.locator(self.common_selectors["error_message"]).count() > 0:
                error_text = self.get_text(self.common_selectors["error_message"])
                self.logger.info(f"Error message found: {error_text}")
                return error_text
            return None
        except Exception as e:
            self.logger.warning(f"Error message retrieval failed: {str(e)}")
            return None

    # Context Management

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with error handling."""
        if exc_type:
            self.logger.error(f"Exception in page context: {exc_type.__name__}: {exc_val}")
            self.take_screenshot(f"context_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        return False
