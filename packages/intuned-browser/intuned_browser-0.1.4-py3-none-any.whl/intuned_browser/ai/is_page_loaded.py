import base64
import logging

import litellm
from playwright.async_api import Page

from intuned_browser.ai.types import SUPPORTED_MODELS
from intuned_browser.intuned_services.api_gateways import GatewayFactory

litellm.set_verbose = False  # type: ignore
logger = logging.getLogger(__name__)


async def is_page_loaded(
    page: Page,
    *,
    model: SUPPORTED_MODELS = "gpt-4o-2024-08-06",
    timeout_s: int = 10,
    api_key: str | None = None,
) -> bool:
    gateway = GatewayFactory.create_ai_gateway(model=model, api_key=api_key)
    screenshot_bytes = await page.screenshot(full_page=False, type="png", timeout=timeout_s * 1000)

    base64_image = base64.b64encode(screenshot_bytes).decode("utf-8")
    response = await gateway.acompletion(
        messages=[
            {
                "role": "system",
                "content": """You are a helpful assistant that determines if a webpage finished loading. If the page finished loading, start your answer with 'True'. If the page is loading, start your answer with 'False'. If you are not sure, start your answer with 'Dont know'. In a new line, add a reason to your response.

Some good cues for determining if a page is loading:
- Loading spinner
- Page is blank
- Some content looks like it's missing
- Not on splash screen
""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": "data:image/png;base64," + base64_image},
                    },
                    {
                        "type": "text",
                        "text": "Look at the screenshot and tell me, is the page loading or has it finished loading?",
                    },
                ],
            },
        ],
    )

    llm_result = response.choices[0].message.content
    # Normalize multiple newlines to one
    llm_result = "\n".join(filter(None, llm_result.split("\n")))
    if llm_result is None:
        raise ValueError("LLM result is None")
    is_true = "True" in llm_result
    is_false = "False" in llm_result
    is_dont_know = "Dont know" in llm_result
    reason = llm_result.split("\n")[1] if len(llm_result.split("\n")) > 1 else None
    result: bool
    if is_true:
        result = True
    elif is_false:
        result = False
    elif is_dont_know:
        result = False
    else:
        raise ValueError("LLM result is not valid")
    if response._response_headers and response._response_headers.get("x-ai-cost-in-cents"):
        logger.info(f"Total LLM Cost In Cents: {response._response_headers['x-ai-cost-in-cents']}")
    else:
        logger.info(f"Total LLM Tokens: {response.usage.total_tokens}")
    logger.debug(f"Reason: {reason}")
    return result
