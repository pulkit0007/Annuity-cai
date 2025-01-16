from openai import OpenAI, AsyncOpenAI
from app.config import OPENAI_API_KEY


openai_client = OpenAI(api_key=OPENAI_API_KEY)
async_openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
