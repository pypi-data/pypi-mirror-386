import asyncio
from collections.abc import Callable
from typing import Union

from playwright.async_api import Locator
from playwright.async_api import Page

from intuned_browser.helpers.wait_for_network_settled import wait_for_network_settled


@wait_for_network_settled(max_inflight_requests=0, timeout_s=10)
async def _scroll_to_bottom(page: Page, scrollable: Union[Page, Locator]) -> int:
    """Scroll to the bottom of the container and return the new scroll height."""
    if isinstance(scrollable, Page):
        new_height = await scrollable.evaluate("""() => {
            window.scrollTo(0, document.body.scrollHeight);
            return document.body.scrollHeight;
        }""")
    else:
        new_height = await scrollable.evaluate("""
            element => {
                element.scrollTop = element.scrollHeight;
                return element.scrollHeight;
            }
        """)
    return new_height


async def scroll_to_load_content(
    source: Union[Page, Locator],
    *,
    on_scroll_progress: Callable[[], None] = lambda: None,
    max_scrolls: int = 50,
    delay_s: float = 0.1,
    min_height_change: int = 100,
):
    scrollable = source
    if not scrollable:
        raise ValueError("scrollable is required")
    previous_height = -1
    scroll_count = 0
    page = source if isinstance(source, Page) else source.page
    while scroll_count < max_scrolls:
        on_scroll_progress()

        # Get current height and scroll to bottom
        current_height = await _scroll_to_bottom(page, scrollable)

        if abs(current_height - previous_height) < min_height_change:
            break

        # Update tracking variables
        previous_height = current_height
        scroll_count += 1

        # Wait for potential content load
        await asyncio.sleep(delay_s)
