"""
Assertion Utilities for UI Test Automation

Provides enhanced assertion methods with better error messages and soft assertions
for Playwright-based tests.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from playwright.sync_api import Page, expect


class AssertionUtils:
    """
    Enhanced assertion utilities for UI testing.

    Provides custom assertion methods with detailed error messages
    and soft assertion support.
    """

    def __init__(self, page: Page):
        """
        Initialize assertion utilities.

        Args:
            page (Page): Playwright page instance
        """
        self.page = page
        self.logger = logging.getLogger(self.__class__.__name__)
        self.soft_assertions: List[Dict[str, Any]] = []
        self.assertion_count = 0

    def assert_element_visible(
        self, selector: str, timeout: int = 30000, message: Optional[str] = None
    ) -> bool:
        """
        Assert that element is visible.

        Args:
            selector (str): Element selector
            timeout (int): Timeout in milliseconds
            message (str, optional): Custom error message

        Returns:
            bool: True if assertion passes

        Raises:
            AssertionError: If element is not visible
        """
        try:
            element = self.page.locator(selector).first
            expect(element).to_be_visible(timeout=timeout)

            self._log_assertion_success(f"Element visible: {selector}")
            return True

        except Exception as e:
            error_msg = message or f"Element not visible: {selector}"
            self._log_assertion_failure(error_msg, str(e))
            raise AssertionError(f"{error_msg}. Error: {str(e)}")

    def assert_element_not_visible(
        self, selector: str, timeout: int = 30000, message: Optional[str] = None
    ) -> bool:
        """
        Assert that element is not visible.

        Args:
            selector (str): Element selector
            timeout (int): Timeout in milliseconds
            message (str, optional): Custom error message

        Returns:
            bool: True if assertion passes
        """
        try:
            element = self.page.locator(selector).first
            expect(element).to_be_hidden(timeout=timeout)

            self._log_assertion_success(f"Element not visible: {selector}")
            return True

        except Exception as e:
            error_msg = message or f"Element unexpectedly visible: {selector}"
            self._log_assertion_failure(error_msg, str(e))
            raise AssertionError(f"{error_msg}. Error: {str(e)}")

    def assert_text_present(
        self,
        expected_text: str,
        selector: Optional[str] = None,
        timeout: int = 30000,
        message: Optional[str] = None,
    ) -> bool:
        """
        Assert that text is present.

        Args:
            expected_text (str): Text to verify
            selector (str, optional): Element selector to check
            timeout (int): Timeout in milliseconds
            message (str, optional): Custom error message

        Returns:
            bool: True if assertion passes
        """
        try:
            if selector:
                element = self.page.locator(selector).first
                expect(element).to_contain_text(expected_text, timeout=timeout)
                location = f"in element {selector}"
            else:
                expect(self.page.locator("body")).to_contain_text(expected_text, timeout=timeout)
                location = "on page"

            self._log_assertion_success(f"Text present {location}: '{expected_text}'")
            return True

        except Exception as e:
            error_msg = message or f"Text not found: '{expected_text}'"
            self._log_assertion_failure(error_msg, str(e))
            raise AssertionError(f"{error_msg}. Error: {str(e)}")

    def assert_url_contains(
        self, expected_url_part: str, timeout: int = 30000, message: Optional[str] = None
    ) -> bool:
        """
        Assert that URL contains expected part.

        Args:
            expected_url_part (str): URL part to verify
            timeout (int): Timeout in milliseconds
            message (str, optional): Custom error message

        Returns:
            bool: True if assertion passes
        """
        try:
            expect(self.page).to_have_url(f"*{expected_url_part}*", timeout=timeout)

            self._log_assertion_success(f"URL contains: '{expected_url_part}'")
            return True

        except Exception as e:
            current_url = self.page.url
            error_msg = (
                message or f"URL does not contain '{expected_url_part}'. Current URL: {current_url}"
            )
            self._log_assertion_failure(error_msg, str(e))
            raise AssertionError(f"{error_msg}. Error: {str(e)}")

    def assert_element_count(
        self,
        selector: str,
        expected_count: int,
        timeout: int = 30000,
        message: Optional[str] = None,
    ) -> bool:
        """
        Assert element count.

        Args:
            selector (str): Element selector
            expected_count (int): Expected number of elements
            timeout (int): Timeout in milliseconds
            message (str, optional): Custom error message

        Returns:
            bool: True if assertion passes
        """
        try:
            elements = self.page.locator(selector)
            expect(elements).to_have_count(expected_count, timeout=timeout)

            self._log_assertion_success(f"Element count for {selector}: {expected_count}")
            return True

        except Exception as e:
            actual_count = self.page.locator(selector).count()
            error_msg = (  # noqa: E501
                message
                or f"Expected {expected_count} elements, found {actual_count} for selector: {selector}"  # noqa: E501
            )
            self._log_assertion_failure(error_msg, str(e))
            raise AssertionError(f"{error_msg}. Error: {str(e)}")

    def soft_assert_element_visible(
        self, selector: str, timeout: int = 30000, message: Optional[str] = None
    ) -> bool:
        """
        Soft assert that element is visible (doesn't raise exception).

        Args:
            selector (str): Element selector
            timeout (int): Timeout in milliseconds
            message (str, optional): Custom error message

        Returns:
            bool: True if assertion passes
        """
        try:
            self.assert_element_visible(selector, timeout, message)
            return True
        except AssertionError as e:
            self._add_soft_assertion_failure(str(e))
            return False

    def soft_assert_text_present(
        self,
        expected_text: str,
        selector: Optional[str] = None,
        timeout: int = 30000,
        message: Optional[str] = None,
    ) -> bool:
        """
        Soft assert that text is present (doesn't raise exception).

        Args:
            expected_text (str): Text to verify
            selector (str, optional): Element selector to check
            timeout (int): Timeout in milliseconds
            message (str, optional): Custom error message

        Returns:
            bool: True if assertion passes
        """
        try:
            self.assert_text_present(expected_text, selector, timeout, message)
            return True
        except AssertionError as e:
            self._add_soft_assertion_failure(str(e))
            return False

    def assert_all_soft_assertions(self) -> bool:
        """
        Assert all soft assertions and raise if any failed.

        Returns:
            bool: True if all soft assertions passed

        Raises:
            AssertionError: If any soft assertions failed
        """
        if self.soft_assertions:
            failure_messages = [assertion["message"] for assertion in self.soft_assertions]
            error_message = f"Soft assertion failures ({len(failure_messages)}):\n" + "\n".join(
                failure_messages
            )

            self.logger.error(f"Soft assertions failed: {len(failure_messages)} failures")
            raise AssertionError(error_message)

        self.logger.info("All soft assertions passed")
        return True

    def clear_soft_assertions(self) -> None:
        """Clear all soft assertion results."""
        self.soft_assertions.clear()
        self.logger.debug("Soft assertions cleared")

    def _log_assertion_success(self, message: str) -> None:
        """Log successful assertion."""
        self.assertion_count += 1
        self.logger.debug(f"✓ Assertion {self.assertion_count}: {message}")

    def _log_assertion_failure(self, message: str, error: str) -> None:
        """Log failed assertion."""
        self.assertion_count += 1
        self.logger.error(f"✗ Assertion {self.assertion_count}: {message} - {error}")

    def _add_soft_assertion_failure(self, message: str) -> None:
        """Add soft assertion failure to the list."""
        failure = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "assertion_number": self.assertion_count,
        }
        self.soft_assertions.append(failure)
        self.logger.warning(f"Soft assertion failed: {message}")
