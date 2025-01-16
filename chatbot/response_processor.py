from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Literal, Optional, Dict, Any

from app.logger import get_logger
from functools import partial
from core.utils import retrieve_context
from common.redis_utils import formatter
from common.redis_utils import (
    RedisCache,
    RedisStream,
    formatter,
)
from app.services.query_response import handle_response_stream
from chatbot.intent_classifier import predict_tool
from chatbot.tools import get_faq_answer, get_rag_answer

router = APIRouter()
logger = get_logger("")


class BotResponseProcessor:
    def __init__(
        self,
        query: str,
        adviser_id: str,
        chat_id: str,
        redis_stream: RedisStream = RedisStream(),
        redis_cache: RedisCache = RedisCache(),
    ):
        self.query = query.strip()
        self.adviser_id = adviser_id
        self.chat_id = chat_id
        self.redis_stream = redis_stream
        self.redis_cache = redis_cache
        self.user_context = None

    async def _initialize(
        self,
        adviser_id: str | None = None,
    ) -> None:
        if not adviser_id and not self.adviser_id:
            raise ValueError("Adviser ID cannot be empty")
        _adviser_id = adviser_id or self.adviser_id
        self.user_context = await retrieve_context(_adviser_id)
        self.user_context = self.user_context or {}
        if self.user_context:
            return self.user_context

    async def _initialize_context(
        self,
        adviser_id: str | None = None,
    ):
        return await self._initialize(adviser_id)

    async def process(
        self, response_type: Literal["stream", "api"] = "stream"
    ) -> Optional[Dict[str, Any]]:
        """Process the bot response with improved error handling and logging"""

        # print("First time process initialize")
        try:
            user_context = await self._initialize_context()
            print("\n \n #######User context: #######\n\n", user_context)
            # Access the 'history' key
            history = user_context.get("history", [])
            # Combine all history records into a single dictionary
            history_string = ""
            for record in history[::-1][:2]:
                for k, v in record.items():
                    history_string += f"Question: {k}\nAnswer: {v}\n"

            products = user_context.get("products", [])
            if not user_context:
                products = []

            tool_spec = await predict_tool(self.query, history_string)
            print("\n \n #######Tool spec: #######\n\n", tool_spec)
            predicted_intent = tool_spec.get("intent", "AnnuitiesFAQ")

            if predicted_intent == "ProductInfo":
                logger.info(f"The query is product based.")
                tool_func = partial(
                    get_rag_answer,
                    question=self.query,
                    products=products,
                    history=history_string,
                    tool_spec=tool_spec,
                )
            else:
                logger.info(f"The query is general FAQ.")
                tool_func = partial(
                    get_faq_answer,
                    message=self.query,
                )

            response = await handle_response_stream(tool_func, self.chat_id)
            return JSONResponse(content=response)

        except Exception as e:
            error_msg = f"Error processing bot response: {str(e)}"
            logger.error(error_msg, exc_info=True)

            await formatter(
                type="error", chat_id=self.chat_id, status="Processing failed"
            )

            if response_type == "api":
                return {"status": "error", "message": error_msg}
            return None
