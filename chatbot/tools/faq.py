import traceback
from chatbot.prompts import GENERATOR_SYS_PROMPT
from common.openai_client import async_openai_client
from app.logger import get_logger

logger = get_logger("tools")


async def get_faq_answer(message: str):
    try:
        response_stream = await async_openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": GENERATOR_SYS_PROMPT},
                {"role": "user", "content": message},
            ],
            stream=True,
            max_tokens=1024,
        )
        return response_stream
    except Exception as e:
        logger.error(f"Error processing FAQ answer: {e}")
        logger.error(traceback.format_exc())
        raise
