import re
from pydantic import BaseModel, Field
from typing import Literal, Optional
from datetime import datetime

from common.openai_client import async_openai_client
from common.rag_db import pinecone_index, PineconeIdx1536_Namespaces
from chatbot.prompts import TOOL_SYS_PROMPT, TOOL_USER_TEMPLATE

from app.logger import get_logger

logger = get_logger("intent_classifier")


class ToolResponse(BaseModel):
    thought: str = Field(
        description="4-5 words as chain of thought before deciding on the tool."
    )
    intent: Literal["ProductInfo", "AnnuitiesFAQ"] = Field(
        description="The intent of the user's message."
    )
    product_name: str = Field(
        description="Product name that the user may be asking about. Leave blank for AnnuitiesFAQ."
    )


def _clean_product_names(tool_spec):
    """Check and clean the product_names list in tool_spec for special characters."""
    if "product_name" in tool_spec:
        # Clean each product name in the list
        tool_spec["product_name"] = re.sub(r"[^\w\s.\d]", "", tool_spec["product_name"])

    return tool_spec


async def get_user_embedding(user_message):
    response = await async_openai_client.embeddings.create(
        input=user_message, model="text-embedding-3-small"
    )
    return response.data[0].embedding


async def predict_tool(user_message: str, history: Optional[str] = ""):
    user_embedding = await get_user_embedding(user_message)

    matches = pinecone_index.query(
        namespace=PineconeIdx1536_Namespaces.intent_classifier,
        vector=user_embedding,
        top_k=20,
        include_values=False,
        include_metadata=True,
    ).get("matches", [])
    examples = [item.get("metadata", {}).get("payload", "") for item in matches]
    example_string = "\n".join(examples)
    date_today = datetime.today().strftime("%Y-%m-%d")

    sys_prompt = TOOL_SYS_PROMPT.format(examples=example_string)

    user_message = TOOL_USER_TEMPLATE.format(
        date_today=date_today, history=history, question=user_message
    )

    response = await async_openai_client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_message},
        ],
        response_format=ToolResponse,
        temperature=0,
    )
    predicted_tool_spec = response.choices[0].message.parsed.model_dump()

    predicted_tool_spec = _clean_product_names(predicted_tool_spec)
    logger.info(f"Predicted tool spec: {predicted_tool_spec}")
    return predicted_tool_spec
