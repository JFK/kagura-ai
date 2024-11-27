import asyncio
import inspect
import json
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel
from redis import asyncio as aioredis

from .config import ConfigBase
from .utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


@dataclass
class Message:
    role: str  # "user" or "assistant" or "system"
    content: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        """Convert message to dict format for LLM API"""
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict) -> "Message":
        """Create Message instance from dictionary"""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else None
            ),
        )


class MemoryBackend(ConfigBase):
    _redis = None
    _ram_storage: Dict[str, Dict[str, Any]] = defaultdict(dict)
    _ram_ttl: Dict[str, datetime] = {}
    _cleanup_task: Optional[asyncio.Task] = None
    _running: bool = True

    def __init__(self, base_dir: Optional[str] = None):
        super().__init__(base_dir)
        if self._redis is None:
            self._initialize_from_config()

    async def close(self):
        """Close Redis connection and cleanup resources"""
        logger.debug("Starting MemoryBackend cleanup...")
        self._running = False  # Signal the cleanup task to stop

        # Cancel cleanup task if it's running
        if self._cleanup_task and not self._cleanup_task.done():
            logger.debug(f"Cancelling cleanup task: {self._cleanup_task}")
            try:
                self._cleanup_task.cancel()
                await asyncio.wait_for(self._cleanup_task, timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Cleanup task cancellation timed out")
            except Exception as e:
                logger.error(f"Error cancelling cleanup task: {e}")

        # Disconnect Redis safely
        if self._redis:
            try:
                logger.debug("Closing Redis connection...")
                await self._redis.close()  # Close the connection
                await self._redis.connection_pool.disconnect()
                self._redis = None  # Remove reference to the connection
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
        # Clear RAM storage
        self._ram_storage.clear()
        self._ram_ttl.clear()
        logger.debug("MemoryBackend cleanup completed")

    def _initialize_from_config(self):
        redis_config = self.get_system_backend("redis")

        self.default_ttl = (
            self.system_memory_backend.get("default_ttl_hours", 24) * 3600
        )
        self.cleanup_interval = (
            self.system_memory_backend.get("cleanup_interval_hours", 1) * 3600
        )
        if redis_config:
            try:
                redis_url = f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}"
                self._redis = aioredis.Redis.from_url(
                    redis_url, db=redis_config.get("db", 0), decode_responses=True
                )
                self._running = True
                self._cleanup_task = asyncio.create_task(self._start_cleanup_task())
                logger.debug("Redis connection established")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using RAM storage.")

    async def _start_cleanup_task(self):
        """Start background task for cleaning expired RAM storage items"""
        while self._running:
            try:
                await self._cleanup_expired()
                await asyncio.sleep(self.cleanup_interval)
            except asyncio.CancelledError:
                logger.debug("Cleanup task cancelled")
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)

    async def _cleanup_expired(self):
        """Remove expired items from RAM storage"""
        current_time = datetime.now()
        expired_keys = [
            key
            for key, expire_time in self._ram_ttl.items()
            if current_time > expire_time
        ]
        for key in expired_keys:
            self._ram_storage.pop(key, None)
            self._ram_ttl.pop(key, None)

    async def ping(self) -> bool:
        """Check if Redis is available"""
        if self._redis:
            try:
                return await self._redis.ping()
            except Exception:
                return False
        return False

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value with TTL (default from config)"""
        if ttl is None:
            ttl = self.default_ttl

        try:
            if await self.ping():
                return await self._redis.setex(key, ttl, value)
            else:
                self._ram_storage[key] = value
                self._ram_ttl[key] = datetime.now() + timedelta(seconds=ttl)
                return True
        except Exception as e:
            logger.error(f"Error setting value: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value from storage"""
        try:
            if await self.ping():
                return await self._redis.get(key)
            else:
                if key in self._ram_storage:
                    if datetime.now() <= self._ram_ttl[key]:
                        return self._ram_storage[key]
                    else:
                        self._ram_storage.pop(key, None)
                        self._ram_ttl.pop(key, None)
                return None
        except Exception as e:
            logger.error(f"Error getting value: {e}")
            return None

    async def publish(self, channel: str, message: str) -> bool:
        """Publish message to channel (only works with Redis)"""
        try:
            if await self.ping():
                return await self._redis.publish(channel, message)
            return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

    async def subscribe(self, channel: str):
        """Subscribe to channel (only works with Redis)"""
        if await self.ping():
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        return None


def asyncclassmethod(method):
    """Decorator for async class methods"""

    @wraps(method)
    def wrapper(cls, *args, **kwargs):
        return method(cls, *args, **kwargs)

    wrapper.__isabstractmethod__ = getattr(method, "__isabstractmethod__", False)
    return classmethod(wrapper)


class MessageHistory(MemoryBackend):
    def __init__(self, system_prompt: str = None, base_dir: Optional[str] = None):
        super().__init__(base_dir)
        self.conversation_id = self.system_memory_history_uuid or str(uuid.uuid4())
        self.window_size = self.system_memory_message_history.get("window_size", 20)
        self.context_window = self.system_memory_message_history.get(
            "context_window", 5
        )
        self.ttl_hours = self.system_memory_message_history.get("ttl_hours", 24)
        self.messages: deque = deque(maxlen=self.window_size)
        self._redis_key_prefix = "kagura:message_history:"
        self._system_prompt = system_prompt  # Not stored in Redis

    @asyncclassmethod
    async def factory(
        cls, system_prompt: str = None, base_dir: Optional[str] = None
    ) -> "MessageHistory":
        """Factory method to create and initialize a MessageHistory instance"""
        instance = cls(system_prompt, base_dir)
        await instance._load_from_redis()
        return instance

    async def _save_to_redis(self) -> bool:
        """system_prompt以外のメッセージのみをRedisに保存"""
        try:
            messages_data = []

            for msg in self.messages:
                if msg.role != "system":  # Skip system messages
                    msg_dict = asdict(msg)
                    msg_dict["timestamp"] = msg_dict["timestamp"].isoformat()
                    messages_data.append(msg_dict)

            data = {
                "window_size": self.window_size,
                "messages": messages_data,
                "updated_at": datetime.now().isoformat(),
            }

            key = f"{self._redis_key_prefix}{self.conversation_id}"
            return await self.set(key, json.dumps(data), ttl=self.ttl_hours * 3600)
        except Exception as e:
            logger.error(f"Failed to save message history to Redis: {e}")
            return False

    async def _load_from_redis(self) -> bool:
        """Redisからメッセージを読み込む（system_promptは含まない）"""
        try:
            key = f"{self._redis_key_prefix}{self.conversation_id}"
            data = await self.get(key)
            if not data:
                return False

            stored_data = json.loads(data)
            self.window_size = stored_data["window_size"]

            # 保存されたメッセージを読み込む
            new_messages = deque(maxlen=self.window_size)
            for msg_data in stored_data["messages"]:
                message = Message.from_dict(msg_data)
                new_messages.append(message)

            self.messages = new_messages
            return True

        except Exception as e:
            logger.error(f"Failed to load message history from Redis: {e}")
            return False

    async def add_message(self, role: str, content: str) -> None:
        """Add a new message to the history and save to Redis if available"""
        message = Message(role=role, content=content)
        self.messages.append(message)
        await self._save_to_redis()

    async def get_messages(self, use_context_window: bool = True) -> List[Dict]:
        """
        メッセージ履歴を取得。use_context_window=Trueの場合は直近のやり取りのみを返す
        """
        await self._load_from_redis()

        messages_for_llm = []
        if self._system_prompt:
            messages_for_llm.append({"role": "system", "content": self._system_prompt})

        if use_context_window:
            recent_messages = list(self.messages)[-self.context_window * 2 :]
            messages_for_llm.extend([msg.to_dict() for msg in recent_messages])
        else:
            # 全履歴を取得
            messages_for_llm.extend([msg.to_dict() for msg in self.messages])

        return messages_for_llm

    async def close(self):
        # Close any additional resources if necessary
        await super().close()

    async def clear(self) -> None:
        """Clear the message history from both memory and Redis"""
        try:
            self.messages.clear()

            key = f"{self._redis_key_prefix}{self.conversation_id}"
            if await self.ping():
                await self._redis.delete(key)

            logger.debug("Message history cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing message history: {e}")
            raise


class Memory(Generic[T]):
    """Generic memory class for storing any type of data"""

    def __init__(self, namespace: str, ttl_hours: int = 24):
        self.namespace = namespace
        self.ttl = ttl_hours * 3600
        self._backend = MemoryBackend()

    def _get_cache_key(self, key: str) -> str:
        safe_key = str(key).replace(" ", "_")
        return f"{self.namespace}:{safe_key}"

    async def get(self, key: str, model_class: type[T]) -> Optional[T]:
        try:
            cache_key = self._get_cache_key(key)
            if cached_data := await self._backend.get(cache_key):
                data = json.loads(cached_data)
                if not issubclass(model_class, BaseModel):
                    raise TypeError(
                        f"Model class must be a subclass of BaseModel, got {model_class}"
                    )

                try:
                    if isinstance(data, list):
                        return [model_class(**item) for item in data]
                    return model_class(**data)
                except Exception as e:
                    logger.error(f"Failed to construct model from cache: {e}")
                    await self.delete(key)
                    return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
        except Exception as e:
            logger.error(f"Memory get error: {e}")
        return None

    async def set(self, key: str, value: T | List[T]) -> bool:
        try:
            cache_key = self._get_cache_key(key)
            if isinstance(value, list):
                if not all(isinstance(item, BaseModel) for item in value):
                    raise TypeError(
                        "All items in the list must be instances of BaseModel"
                    )
                data = [item.dict() for item in value]
            else:
                if not isinstance(value, BaseModel):
                    raise TypeError("Value must be an instance of BaseModel")
                data = value.dict()

            return await self._backend.set(cache_key, json.dumps(data), ttl=self.ttl)
        except Exception as e:
            logger.error(f"Memory set error for key {key}: {e}")
            return False


class MemoryStats:
    """Class for tracking memory operation statistics"""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self._backend = MemoryBackend()

    async def increment_hits(self):
        try:
            await self._backend.set(
                f"{self.namespace}:hits",
                str(int(await self._backend.get(f"{self.namespace}:hits") or 0) + 1),
            )
        except Exception as e:
            logger.error(f"Failed to increment hits: {e}")

    async def increment_misses(self):
        try:
            await self._backend.set(
                f"{self.namespace}:misses",
                str(int(await self._backend.get(f"{self.namespace}:misses") or 0) + 1),
            )
        except Exception as e:
            logger.error(f"Failed to increment misses: {e}")

    async def increment_errors(self):
        try:
            await self._backend.set(
                f"{self.namespace}:errors",
                str(int(await self._backend.get(f"{self.namespace}:errors") or 0) + 1),
            )
        except Exception as e:
            logger.error(f"Failed to increment errors: {e}")

    async def get_stats(self) -> Dict[str, int]:
        try:
            hits = int(await self._backend.get(f"{self.namespace}:hits") or 0)
            misses = int(await self._backend.get(f"{self.namespace}:misses") or 0)
            errors = int(await self._backend.get(f"{self.namespace}:errors") or 0)

            return {
                "hits": hits,
                "misses": misses,
                "errors": errors,
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"hits": 0, "misses": 0, "errors": 0}


def with_memory(namespace: str, ttl_hours: int = 24, key_generator: Callable = None):
    def _get_cache_key(func: Callable, *args, **kwargs) -> str:
        if key_generator:
            return key_generator(*args, **kwargs)
        return (
            str(args[0])
            if args
            else str(kwargs.get(inspect.getfullargspec(func).args[0]))
        )

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return_type = func.__annotations__.get("return")
                if not return_type or not issubclass(return_type, BaseModel):
                    logger.warning(
                        f"Return type for {func.__name__} must be a subclass of BaseModel"
                    )
                    return await func(*args, **kwargs)

                memory = Memory[return_type](namespace, ttl_hours)
                stats = MemoryStats(namespace)

                cache_key = _get_cache_key(func, *args, **kwargs)

                if cached_result := await memory.get(cache_key, return_type):
                    await stats.increment_hits()
                    return cached_result

                await stats.increment_misses()
                result = await func(*args, **kwargs)

                if result is not None:
                    await memory.set(cache_key, result)
                return result

            except Exception as e:
                logger.error(f"Memory decorator error in {func.__name__}: {e}")
                try:
                    await stats.increment_errors()
                except Exception:
                    pass
                raise

        return wrapper

    return decorator
