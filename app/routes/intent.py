# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from app.services.intent_classifier import predict_tool

# router = APIRouter()

# class IntentRequest(BaseModel):
#     message: str

# @router.post("/intent")
# async def classify_intent(intent_request: IntentRequest):
#     message = intent_request.message

#     if not message.strip():
#         raise HTTPException(status_code=400, detail="Message cannot be empty")

#     # Predict intent for the message
#     try:
#         intent = predict_tool(message, history="").model_dump().get("intent", "NA")
#     except Exception as e:
#         intent = "NA"
#     return {"intent": intent}
