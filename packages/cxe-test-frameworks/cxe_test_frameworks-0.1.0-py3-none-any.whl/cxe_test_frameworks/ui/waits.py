"""
Wait Helpers for UI Test Automation

Provides smart waiting strategies, condition checking, and retry mechanisms
for Playwright-based tests.
"""

import logging
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional

from playwright.sync_api import Locator, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import expect


class WaitCondition(Enum):
    """Enumeration of available wait conditions."""

    VISIBLE = "visible"
    HIDDEN = "hidden"
    ATTACHED = "attached"
    DETACHED = "detached"
    ENABLED = "enabled"
    DISABLED = "disabled"
    EDITABLE = "editable"
    READONLY = "readonly"
    CHECKED = "checked"
    UNCHECKED = "unchecked"
    FOCUSED = "focused"
    STABLE = "stable"


class RetryStrategy(Enum):
    """Enumeration of retry strategies."""

    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


class WaitHelpers:
    """
    Comprehensive wait helpers for reliable UI automation.

    Provides intelligent waiting strategies including element state waiting,
    custom condition waiting, and retry mechanisms.
    """

    def __init__(self, page: Page, default_timeout: int = 30000):
        """
        Initialize wait helpers with page instance.

        Args:
            page (Page): Playwright page instance
            default_timeout (int): Default timeout in milliseconds
        """
        self.page = page
        self.default_timeout = default_timeout
        self.logger = logging.getLogger(self.__class__.__name__)

        # Performance tracking
        self.wait_stats = {
            "total_waits": 0,
            "successful_waits": 0,
            "failed_waits": 0,
            "total_wait_time": 0.0,
        }

    def wait_for_element_visible(
        self, selector: str, timeout: Optional[int] = None, retry_count: int = 3
    ) -> bool:
        """
        Wait for element to become visible with retry logic.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            bool: True if element becomes visible, False otherwise
        """
        return self._wait_for_element_condition(
            selector, WaitCondition.VISIBLE, timeout, retry_count
        )

    def wait_for_element_hidden(
        self, selector: str, timeout: Optional[int] = None, retry_count: int = 3
    ) -> bool:
        """
        Wait for element to become hidden with retry logic.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            bool: True if element becomes hidden, False otherwise
        """
        return self._wait_for_element_condition(
            selector, WaitCondition.HIDDEN, timeout, retry_count
        )

    def wait_for_element_enabled(
        self, selector: str, timeout: Optional[int] = None, retry_count: int = 3
    ) -> bool:
        """
        Wait for element to become enabled with retry logic.

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            bool: True if element becomes enabled, False otherwise
        """
        return self._wait_for_element_condition(
            selector, WaitCondition.ENABLED, timeout, retry_count
        )

    def wait_for_element_clickable(
        self, selector: str, timeout: Optional[int] = None, retry_count: int = 3
    ) -> bool:
        """
        Wait for element to become clickable (visible and enabled).

        Args:
            selector (str): CSS selector or data-testid
            timeout (int, optional): Custom timeout in milliseconds
            retry_count (int): Number of retry attempts

        Returns:
            bool: True if element becomes clickable, False otherwise
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()

        try:

            # Wait for element to be both visible and enabled
            visible = self.wait_for_element_visible(selector, timeout // 2, retry_count)
            if not visible:
                return False

            remaining_timeout = max(1000, timeout - int((time.time() - start_time) * 1000))
            enabled = self.wait_for_element_enabled(selector, remaining_timeout, retry_count)

            result = visible and enabled
            self._track_wait_performance(start_time, result)

            if result:
                self.logger.debug(f"Element clickable: {selector}")
            else:
                self.logger.warning(f"Element not clickable: {selector}")

            return result

        except Exception as e:
            self.logger.error(f"Wait for clickable failed for {selector}: {str(e)}")
            self._track_wait_performance(start_time, False)
            return False

    def wait_for_page_load_complete(
        self, timeout: Optional[int] = None, check_network_idle: bool = True
    ) -> bool:
        """
        Wait for page to completely load including network activity.

        Args:
            timeout (int, optional): Custom timeout in milliseconds
            check_network_idle (bool): Whether to wait for network idle state

        Returns:
            bool: True if page loaded completely, False otherwise
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()

        try:
            # Wait for DOM content loaded
            self.page.wait_for_load_state("domcontentloaded", timeout=timeout)

            # Wait for all resources to load
            remaining_timeout = max(1000, timeout - int((time.time() - start_time) * 1000))
            self.page.wait_for_load_state("load", timeout=remaining_timeout)

            # Wait for network idle if requested
            if check_network_idle:
                remaining_timeout = max(1000, timeout - int((time.time() - start_time) * 1000))
                self.page.wait_for_load_state("networkidle", timeout=remaining_timeout)

            self._track_wait_performance(start_time, True)
            self.logger.debug("Page load completed successfully")
            return True

        except PlaywrightTimeoutError:
            self._track_wait_performance(start_time, False)
            self.logger.warning(f"Page load timeout after {timeout}ms")
            return False
        except Exception as e:
            self.logger.error(f"Page load wait failed: {str(e)}")
            self._track_wait_performance(start_time, False)
            return False

    def wait_for_custom_condition(
        self,
        condition_func: Callable[[], bool],
        timeout: Optional[int] = None,
        retry_strategy: RetryStrategy = RetryStrategy.LINEAR,
        retry_interval: float = 0.5,
    ) -> bool:
        """
        Wait for custom condition to be met.

        Args:
            condition_func (Callable[[], bool]): Function that returns True when condition is met
            timeout (int, optional): Custom timeout in milliseconds
            retry_strategy (RetryStrategy): Strategy for retry intervals
            retry_interval (float): Base retry interval in seconds

        Returns:
            bool: True if condition is met, False if timeout
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        end_time = start_time + (timeout / 1000)
        attempt = 0

        try:
            while time.time() < end_time:
                try:
                    if condition_func():
                        self._track_wait_performance(start_time, True)
                        self.logger.debug(f"Custom condition met after {attempt + 1} attempts")
                        return True
                except Exception as e:
                    self.logger.debug(f"Condition check failed: {str(e)}")

                # Calculate next retry interval
                interval = self._calculate_retry_interval(attempt, retry_strategy, retry_interval)
                time.sleep(interval)
                attempt += 1

            self._track_wait_performance(start_time, False)
            self.logger.warning(
                f"Custom condition timeout after {timeout}ms and {attempt} attempts"
            )
            return False

        except Exception as e:
            self.logger.error(f"Custom condition wait failed: {str(e)}")
            self._track_wait_performance(start_time, False)
            return False

    def retry_operation(
        self,
        operation: Callable[[], Any],
        max_attempts: int = 3,
        retry_strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        base_delay: float = 1.0,
        exceptions: tuple = (Exception,),
    ) -> Any:
        """
        Retry operation with configurable strategy.

        Args:
            operation (Callable[[], Any]): Operation to retry
            max_attempts (int): Maximum number of attempts
            retry_strategy (RetryStrategy): Retry delay strategy
            base_delay (float): Base delay in seconds
            exceptions (tuple): Exception types to catch and retry

        Returns:
            Any: Result of the operation

        Raises:
            Exception: Last exception if all attempts fail
        """
        last_exception = None

        for attempt in range(max_attempts):
            try:
                result = operation()
                if attempt > 0:
                    self.logger.info(f"Operation succeeded on attempt {attempt + 1}")
                return result

            except exceptions as e:
                last_exception = e

                if attempt < max_attempts - 1:
                    delay = self._calculate_retry_interval(attempt, retry_strategy, base_delay)
                    self.logger.warning(
                        f"Operation failed on attempt {attempt + 1}, retrying in {delay}s: {str(e)}"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(f"Operation failed after {max_attempts} attempts: {str(e)}")

        if last_exception:
            raise last_exception
        raise Exception("Operation failed with no exception captured")

    def get_wait_statistics(self) -> Dict[str, Any]:
        """
        Get performance statistics for wait operations.

        Returns:
            Dict[str, Any]: Wait performance statistics
        """
        stats = self.wait_stats.copy()

        if stats["total_waits"] > 0:
            stats["success_rate"] = (stats["successful_waits"] / stats["total_waits"]) * 100
            stats["average_wait_time"] = stats["total_wait_time"] / stats["total_waits"]
        else:
            stats["success_rate"] = 0
            stats["average_wait_time"] = 0

        return stats

    def reset_statistics(self) -> None:
        """Reset wait performance statistics."""
        self.wait_stats = {
            "total_waits": 0,
            "successful_waits": 0,
            "failed_waits": 0,
            "total_wait_time": 0.0,
        }

    # Private helper methods

    def _wait_for_element_condition(
        self, selector: str, condition: WaitCondition, timeout: Optional[int], retry_count: int
    ) -> bool:
        """Generic method to wait for element condition with retry."""
        timeout = timeout or self.default_timeout
        start_time = time.time()

        try:
            for attempt in range(retry_count + 1):
                try:
                    element = self.page.locator(selector).first

                    if self._check_element_condition(
                        element, condition, timeout // (retry_count + 1)
                    ):
                        self._track_wait_performance(start_time, True)
                        return True

                except PlaywrightTimeoutError:
                    if attempt < retry_count:
                        self.logger.debug(
                            f"Wait attempt {attempt + 1} failed for {selector}, retrying..."
                        )
                        time.sleep(0.5)
                    continue

            self._track_wait_performance(start_time, False)
            self.logger.warning(
                f"Element condition not met after {retry_count + 1} attempts: {selector}"
            )
            return False

        except Exception as e:
            self.logger.error(f"Wait for element condition failed: {str(e)}")
            self._track_wait_performance(start_time, False)
            return False

    def _check_element_condition(
        self, element: Locator, condition: WaitCondition, timeout: int
    ) -> bool:
        """Check if element meets the specified condition."""
        try:
            if condition == WaitCondition.VISIBLE:
                expect(element).to_be_visible(timeout=timeout)
            elif condition == WaitCondition.HIDDEN:
                expect(element).to_be_hidden(timeout=timeout)
            elif condition == WaitCondition.ENABLED:
                expect(element).to_be_enabled(timeout=timeout)
            elif condition == WaitCondition.DISABLED:
                expect(element).to_be_disabled(timeout=timeout)
            elif condition == WaitCondition.EDITABLE:
                expect(element).to_be_editable(timeout=timeout)
            elif condition == WaitCondition.CHECKED:
                expect(element).to_be_checked(timeout=timeout)
            elif condition == WaitCondition.FOCUSED:
                expect(element).to_be_focused(timeout=timeout)
            elif condition == WaitCondition.ATTACHED:
                expect(element).to_be_attached(timeout=timeout)
            else:
                raise ValueError(f"Unsupported condition: {condition}")

            return True

        except PlaywrightTimeoutError:
            return False

    def _calculate_retry_interval(
        self, attempt: int, strategy: RetryStrategy, base_interval: float
    ) -> float:
        """Calculate retry interval based on strategy."""
        if strategy == RetryStrategy.LINEAR:
            return base_interval
        elif strategy == RetryStrategy.EXPONENTIAL:
            return base_interval * (2**attempt)
        elif strategy == RetryStrategy.FIXED:
            return base_interval
        else:
            return base_interval

    def _track_wait_performance(self, start_time: float, success: bool) -> None:
        """Track wait operation performance."""
        duration = time.time() - start_time

        self.wait_stats["total_waits"] += 1
        self.wait_stats["total_wait_time"] += duration

        if success:
            self.wait_stats["successful_waits"] += 1
        else:
            self.wait_stats["failed_waits"] += 1
