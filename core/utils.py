from app.config import REDIS_PREFIX
from common.redis_utils import RedisCache
import json
from app.logger import get_logger

logger = get_logger("utils")

redis_cache = RedisCache()


async def retrieve_context(adviser_id: str) -> list:
    try:
        context_data = await redis_cache.get(f"{REDIS_PREFIX}_{adviser_id}_context")
        if context_data:
            json_obj = json.loads(context_data)
            return json_obj
        else:
            return {}
    except json.JSONDecodeError as json_err:
        logger.error(f"JSON decoding failed for adviser_id {adviser_id}: {json_err}")
    except Exception as err:
        logger.exception(
            f"Failed to retrieve context for adviser_id {adviser_id}: {err}"
        )
