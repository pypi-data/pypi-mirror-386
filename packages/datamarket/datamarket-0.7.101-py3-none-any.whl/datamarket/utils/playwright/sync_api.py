########################################################################################################################
# IMPORTS

import logging
import time
from datetime import timedelta
from random import randint
from types import TracebackType
from typing import Optional, Self

from camoufox import Camoufox
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    TimeoutError as PlaywrightTimeoutError,
)
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential,
)
from datamarket.interfaces.proxy import ProxyInterface

########################################################################################################################
# SETUP LOGGER

logger = logging.getLogger(__name__)


########################################################################################################################
# HELPER FUNCTIONS
def human_type(page: Page, text: str, delay: int = 100):
    for char in text:
        page.keyboard.type(char, delay=randint(int(delay * 0.5), int(delay * 1.5)))


def human_press_key(page: Page, key: str, count: int = 1, delay: int = 100, add_sleep: bool = True) -> None:
    """Presses a key with a random delay, optionally sleeping between presses."""
    for _ in range(count):
        page.keyboard.press(key, delay=randint(int(delay * 0.5), int(delay * 1.5)))
        if add_sleep:
            time.sleep(randint(int(delay * 1.5), int(delay * 2.5)) / 1000)


########################################################################################################################
# CRAWLER CLASS


class PlaywrightCrawler:
    """A robust, proxy-enabled Playwright crawler with captcha bypass and retry logic."""

    def __init__(self, proxy_interface: Optional[ProxyInterface] = None):
        """
        Initializes the crawler.

        Args:
            proxy_interface (Optional[ProxyInterface], optional): Provider used to fetch
                proxy credentials. Defaults to None. When None, no proxy is configured and
                the browser will run without a proxy.
        """
        self.proxy_interface = proxy_interface
        self.pw: Optional[Camoufox] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def __enter__(self) -> Self:
        """Initializes the browser context when entering the `with` statement."""
        self.init_context()
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        """Safely closes the browser context upon exit."""
        if self.pw:
            self.pw.__exit__(exc_type, exc_val, exc_tb)

    def _build_proxy_config(self) -> Optional[dict]:
        """Builds the proxy configuration dictionary.

        Returns:
            Optional[dict]: Proxy configuration if a proxy_interface is provided; otherwise None.
        """
        if not self.proxy_interface:
            logger.info("Starting browser without proxy.")
            return None

        host, port, user, pwd = self.proxy_interface.get_proxies(raw=True, use_auth=True)
        proxy_url = f"http://{host}:{port}"
        proxy_cfg: dict = {"server": proxy_url}
        if user and pwd:
            proxy_cfg.update({"username": user, "password": pwd})

        logger.info(f"Starting browser with proxy: {proxy_url}")
        return proxy_cfg

    @retry(
        wait=wait_exponential(exp_base=2, multiplier=3, max=90),
        stop=stop_after_delay(timedelta(minutes=10)),
        before_sleep=before_sleep_log(logger, logging.INFO),
        reraise=True,
    )
    def init_context(self) -> Self:
        """
        Initializes a new browser instance and context.

        Behavior:
        - If a proxy_interface is provided, fetches fresh proxy credentials and starts
          the browser using that proxy.
        - If proxy_interface is None, starts the browser without any proxy.

        Returns:
            Self: The crawler instance with active browser, context, and page.
        """
        try:
            proxy_cfg: Optional[dict] = self._build_proxy_config()

            self.pw = Camoufox(headless=True, geoip=True, humanize=True, proxy=proxy_cfg)
            self.browser = self.pw.__enter__()
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
        except Exception as e:
            logger.error(f"Failed to initialize browser context: {e}")
            if self.pw:
                self.pw.__exit__(type(e), e, e.__traceback__)
            raise
        return self

    def restart_context(self) -> None:
        """Closes the current browser instance and initializes a new one."""
        logger.info("Restarting browser context...")
        if self.pw:
            self.pw.__exit__(None, None, None)
        self.init_context()

    @retry(
        retry=retry_if_exception_type((PlaywrightTimeoutError, PlaywrightError)),
        wait=wait_exponential(exp_base=2, multiplier=3, max=90),
        stop=stop_after_delay(timedelta(minutes=10)),
        before_sleep=before_sleep_log(logger, logging.INFO),
        before=lambda rs: rs.args[0].restart_context() if rs.attempt_number > 1 else None,
        reraise=True,
    )
    def _goto_with_retry(self, url: str) -> Page:
        """
        Navigates to a URL with retries for common Playwright errors.
        Restarts the browser context on repeated failures.
        """
        if not (self.page and not self.page.is_closed()):
            logger.warning("Page is not available or closed. Restarting context.")
            self.restart_context()

        # self.page is guaranteed to be valid here by the logic above
        assert self.page is not None
        self.page.goto(url, timeout=30000, wait_until="domcontentloaded")
        return self.page

    def goto(self, url: str) -> Page:
        """
        Ensures the browser is initialized and navigates to the given URL.
        Public wrapper for the internal retry-enabled navigation method.
        """
        if not self.page:
            logger.info("Browser context not found, initializing now...")
            self.init_context()
        return self._goto_with_retry(url)