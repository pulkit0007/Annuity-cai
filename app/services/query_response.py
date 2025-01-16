import asyncio

from app.logger import get_logger

from common.redis_utils import formatter

logger = get_logger("response_stream")


async def handle_response_stream(tool_func, chat_id: str):
    try:
        response_stream = await tool_func()
        full_response = ""  # Initialize full response
        async for chunk in response_stream:
            if hasattr(chunk.choices[0].delta, "content"):
                content_piece = chunk.choices[0].delta.content
                if content_piece:
                    await formatter(type="stream", chat_id=chat_id, data=content_piece)
                    full_response += content_piece

                await asyncio.sleep(0)

        await formatter(type="ended", chat_id=chat_id, status="Processing completed")
        logger.info(f"Full response: {full_response}")
        return {"status": "success", "response": full_response}
    except Exception as e:
        logger.error(f"Failed to process stream response for {chat_id}: {str(e)}")
        return {"status": "failed", "response": ""}
