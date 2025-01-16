from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from app.logger import get_logger

from chatbot.response_processor import BotResponseProcessor

router = APIRouter()
logger = get_logger("orchestration")

class ChatRequest(BaseModel):
    message: str
    user_id: str
    chat_id: str

@router.post("/chat")
async def answer(chat_request: ChatRequest) -> JSONResponse:

    query=chat_request.message
    adviser_id = chat_request.user_id
    chat_id = chat_request.chat_id

    # print("query: ", query)

    processor = BotResponseProcessor(query, adviser_id, chat_id)
    await processor.initialize()
    return JSONResponse({"status": "success", "message": ""})
