from common.redis_utils import RedisCache, RedisManager, RedisPubSub, RedisStream
import asyncio
from app.logger import get_logger

class AppState:
    """Class to manage application state and background tasks"""
    def __init__(self):
        self.subscription_task = None
        self.pubsub_manager = RedisPubSub()
        self.redis_stream = RedisStream()
        self.redis_cache = RedisCache()
        self.logger = get_logger("app")

    async def initialize_redis(self):
        """Initialize Redis connections"""
        try:
            await asyncio.gather(
                self.redis_stream.connect(),
                self.redis_cache.connect(),
                self.pubsub_manager.connect()
            )
            self.logger.info("Redis connections established successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Redis connections: {e}")
            raise

    async def cleanup(self):
        """Cleanup resources"""
        if self.subscription_task:
            self.subscription_task.cancel()
            try:
                await self.subscription_task
            except asyncio.CancelledError:
                self.logger.info("Subscription task cancelled successfully")
        
        await RedisManager.close()
        self.logger.info("Redis connections closed successfully")