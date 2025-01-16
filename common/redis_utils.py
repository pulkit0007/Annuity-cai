import redis.asyncio as aioredis
from typing import Union
import json
from app.config import REDIS_ENDPOINT, REDIS_SSL, REDIS_PREFIX
from app.logger import get_logger
from common.abstract_classes import QueueService

logger = get_logger("caching")

class RedisManager:
    """
    Singleton class to manage Redis connections across different services
    """
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    async def get_client(cls):
        """Get or create Redis client"""
        if cls._client is None:
            try:

                REDIS_URL = f"redis://{REDIS_ENDPOINT}"

                redis_config = {
                    'socket_connect_timeout': 10,       # Set connection timeout
                    'retry_on_timeout': True,           # Retry on timeout errors
                    'socket_keepalive': True,
                }

                cls._client = aioredis.from_url(
                    REDIS_URL,
                    **redis_config
                )
                await cls._client.ping()
                logger.info(f"Connected to Redis at {REDIS_URL}")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return cls._client

    @classmethod
    async def close(cls):
        """Close Redis connection"""
        if cls._client is not None:
            await cls._client.close()
            cls._client = None
            logger.info("Redis connection closed")


class RedisStream(QueueService):
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        if self.redis_client is None:
            self.redis_client = await RedisManager.get_client()

    async def push_item(self, stream_name: str, message: dict) -> None:
        # Ensure the client is connected before pushing the message
        if not self.redis_client:
            await self.connect()

        try:
            await self.redis_client.xadd(stream_name, message)
            #logger.info(f"Message added to stream '{stream_name}': {message}")
        except Exception as e:
            logger.error(f"Error pushing item to stream {stream_name}: {e}")
            raise

    async def read_items(self, stream_name: str, count: int = 1, block_time: int = 0, last_id: str = "$"):
        if not self.redis_client:
            await self.connect()

        try:
            stream_data = await self.redis_client.xread(
                {stream_name: last_id}, count=count, block=block_time
            )

            messages = []
            if stream_data:
                for stream, entries in stream_data:
                    for entry_id, fields in entries:
                        message = {fields[i]: fields[i + 1]
                                   for i in range(0, len(fields), 2)}
                        messages.append({
                            "id": entry_id,
                            "message": message
                        })
            logger.info(f"Read {len(messages)} items from stream '{stream_name}'")
            return messages
        except Exception as e:
            logger.error(f"Error reading items from stream {stream_name}: {e}")
            raise


class RedisCache:
    def __init__(self):
        self.redis_client = None

    async def connect(self):
        self.redis_client = await RedisManager.get_client()

    async def set(self, key, value, expiry=None):
        if not self.redis_client:
            await self.connect()

        await self.redis_client.set(key, value)
        logger.info(f"Set key {key} with value {value}")

    async def get(self, key):
        if not self.redis_client:
            await self.connect()

        try:
            value = await self.redis_client.get(key)
            if value:
                logger.info(f"Retrieved value for key {key}")
            return value if value else None
        except (ConnectionError, TimeoutError):
            logger.exception("Error retrieving cached value from Redis.")
            return None

    async def delete(self, key):
        await self.redis_client.delete(key)


class RedisPubSub:
    def __init__(self):
        self.redis_client = None
        self.pubsub = None

    async def connect(self):
        # Ensure Redis client is connected before calling subscribe or publish
        if self.redis_client is None:
            self.redis_client = await RedisManager.get_client()
        self.pubsub = self.redis_client.pubsub()

    async def publish(self, channel: str, message: dict) -> None:
        try:
            if not self.redis_client:
                # Ensure the client is connected before attempting to publish
                await self.connect()

            message_json = json.dumps(message)
            subscribers_count = await self.redis_client.publish(channel, message_json)
            logger.info(f"Message successfully published to 'cai_stream', received by {subscribers_count} subscribers.")

            return subscribers_count
        except Exception as e:
            logger.exception(f"Error publishing message to channel {channel}: {str(e)}")

    async def subscribe(self, channel: str, callback):
        try:
            if not self.pubsub:
                # Ensure the client is connected before attempting to subscribe
                await self.connect()

            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel: {channel}")

            async for message in self.pubsub.listen():
                if message and message['type'] == 'message':
                    decoded_message = json.loads(message['data'])
                    # print("decoded_message: ", decoded_message)
                    await callback(decoded_message)
        except Exception as e:
            logger.exception(f"Error subscribing to channel {channel}: {str(e)}")


async def formatter(type, chat_id: str, data=None, status=None):
    """Format the payload and push it to the Redis stream."""
    payload = {
        "type": type,
        "chat_id": chat_id,
    }

    if data is not None:
        payload["data"] = data

    if status is not None:
        payload["status"] = status

    await push_stream_response(payload)


async def push_stream_response(payload: dict):
    """Push the formatted payload to the Redis stream."""
    try:
        redis_stream = RedisStream()
        await redis_stream.push_item(f'{REDIS_PREFIX}_{payload["chat_id"]}_response', payload)
    except Exception as e:
        logger.exception(f"Error pushing stream response to Redis: {e}")


async def push_debug_info(chat_id: str, data: Union[str, dict]) -> None:
    """Push debug information to a Redis stream."""
    try:
        redis_stream = RedisStream()
        await redis_stream.push_item(f'{REDIS_PREFIX}_{chat_id}_debug', data)
        logger.info(f"Pushed debug info to Redis for chat_id {chat_id}: {data}")
    except Exception as e:
        logger.exception(f"Error pushing debug info to Redis: {e}")
