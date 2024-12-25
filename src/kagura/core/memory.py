import asyncio
import inspect
import json
import uuid
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
from pathlib import Path
import weakref

from pydantic import BaseModel
from redis import asyncio as aioredis

from .config import ConfigBase
from .utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T", bound=BaseModel)


@dataclass
class Message:
    role: str  # "user" or "assistant" or "system"
    content: str
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dict format for LLM API"""
        return {"role": self.role, "content": self.content}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Message":
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
    _instances = weakref.WeakSet()
    _redis: Optional[aioredis.Redis] = None
    _ram_storage: Dict[str, Dict[str, Any]] = defaultdict(dict)
    _ram_ttl: Dict[str, datetime] = {}
    _default_ttl: int = 86400

    def __init__(self, base_dir: Optional[Union[str, Path]] = None):
        if isinstance(base_dir, str):
            base_dir = Path(base_dir)
        super().__init__(base_dir)
        self._cleanup_task = None
        self._running = True
        self._redis_instance = None
        self._instances.add(self)
        self._initialize_from_config()

    def _initialize_from_config(self):
        redis_config = self.get_system_backend("redis")
        self._default_ttl = (
            self.system_memory_backend.get("default_ttl_hours", 24) * 3600
        )
        self.cleanup_interval = (
            self.system_memory_backend.get("cleanup_interval_hours", 1) * 3600
        )

        if redis_config:
            try:
                redis_url = f"redis://{redis_config.get('host', 'localhost')}:{redis_config.get('port', 6379)}"
                self._redis_instance = aioredis.Redis.from_url(
                    redis_url, db=redis_config.get("db", 0), decode_responses=True
                )
                self._redis = self._redis_instance
                logger.debug("Redis connection established")

                if not self._cleanup_task:
                    self._cleanup_task = asyncio.create_task(self._start_cleanup_task())
                    self._cleanup_task.set_name(f"cleanup_task_{id(self)}")
            except Exception as e:
                logger.warning(f"Failed to connect to Redis: {e}. Using RAM storage.")

    async def _start_cleanup_task(self):
        try:
            while self._running:
                if not self._running:
                    break

                try:
                    await self._cleanup_expired()
                    await asyncio.sleep(self.cleanup_interval)
                except asyncio.CancelledError:
                    logger.debug("Cleanup task cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
                    await asyncio.sleep(1)
        finally:
            self._running = False

    async def close(self):
        """Close Redis connection and cleanup resources"""
        if not self._running:
            return

        self._running = False
        logger.debug("Starting MemoryBackend cleanup...")

        # Cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            try:
                self._cleanup_task.cancel()
                await asyncio.wait_for(asyncio.shield(self._cleanup_task), timeout=1.0)
            except (asyncio.TimeoutError, asyncio.CancelledError, Exception) as e:
                logger.debug(f"Cleanup task cancelled: {e}")
            finally:
                self._cleanup_task = None

        # Redis connection
        if self._redis_instance:
            try:
                await self._redis_instance.close()
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._redis_instance = None
                if self._redis is self._redis_instance:
                    self._redis = None

        # Clear storage
        self._ram_storage.clear()
        self._ram_ttl.clear()
        self._instances.discard(self)
        logger.debug("MemoryBackend cleanup completed")

    @classmethod
    async def cleanup_all(cls):
        """Clean up all instances"""
        instances = list(cls._instances)
        for instance in instances:
            await instance.close()

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
        if self._redis is not None:
            try:
                return await self._redis.ping()
            except Exception:
                return False
        return False

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        try:
            ttl = self._default_ttl if ttl is None else ttl
            if await self.ping() and self._redis is not None:
                await self._redis.setex(key, ttl, value)
                return True
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
            if await self.ping() and self._redis is not None:
                return await self._redis.get(key)
            else:
                if key in self._ram_storage:
                    if datetime.now() <= self._ram_ttl[key]:
                        return str(self._ram_storage[key])
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
            if await self.ping() and self._redis is not None:
                await self._redis.publish(channel, message)
                return True
            return False
        except Exception as e:
            logger.error(f"Error publishing message: {e}")
            return False

    async def subscribe(self, channel: str):
        """Subscribe to channel (only works with Redis)"""
        if await self.ping() and self._redis is not None:
            pubsub = self._redis.pubsub()
            await pubsub.subscribe(channel)
            return pubsub
        return None


def asyncclassmethod(method):
    """Decorator for async class methods"""

    @wraps(method)
    def wrapper(cls, *args, **kwargs):
        return method(cls, *args, **kwargs)

    return classmethod(wrapper)


class MessageHistory(MemoryBackend):
    def __init__(self, system_prompt: Optional[str] = None):
        super().__init__()
        self.conversation_id = self.system_memory_history_uuid or str(uuid.uuid4())
        self.window_size = self.system_memory_message_history.get("window_size", 20)
        self.context_window = self.system_memory_message_history.get(
            "context_window", 5
        )
        self.ttl_hours = self.system_memory_message_history.get("ttl_hours", 24)
        self.messages: deque[Message] = deque(maxlen=self.window_size)
        self._redis_key_prefix = "kagura:message_history:"
        self._system_prompt = system_prompt  # Not stored in Redis

    @classmethod
    async def factory(cls, system_prompt: Optional[str] = None) -> "MessageHistory":
        """Factory method to create and initialize a MessageHistory instance"""
        instance = cls(system_prompt)
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

    async def get_messages(
        self, use_context_window: bool = True
    ) -> List[Dict[str, Any]]:
        """
        メッセージ履歴を取得。use_context_window=Trueの場合は直近のやり取りのみを返す
        """
        await self._load_from_redis()

        messages_for_llm: List[Dict[str, Any]] = []
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
            if await self.ping() and self._redis is not None:
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

    async def get(self, key: str, model_class: type[T]) -> Optional[Union[T, List[T]]]:
        try:
            cache_key = self._get_cache_key(key)
            cached_data = await self._backend.get(cache_key)
            if cached_data:
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

    async def set(self, key: str, value: Union[T, List[T]]) -> bool:
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

    async def delete(self, key: str) -> bool:
        try:
            cache_key = self._get_cache_key(key)
            if await self._backend.ping() and self._backend._redis is not None:
                await self._backend._redis.delete(cache_key)
            else:
                if cache_key in self._backend._ram_storage:
                    self._backend._ram_storage.pop(cache_key, None)
                    self._backend._ram_ttl.pop(cache_key, None)
            return True
        except Exception as e:
            logger.error(f"Memory delete error for key {key}: {e}")
            return False


class MemoryStats:
    """Class for tracking memory operation statistics"""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self._backend = MemoryBackend()

    async def increment_hits(self):
        try:
            hits = int(await self._backend.get(f"{self.namespace}:hits") or 0) + 1
            await self._backend.set(f"{self.namespace}:hits", str(hits))
        except Exception as e:
            logger.error(f"Failed to increment hits: {e}")

    async def increment_misses(self):
        try:
            misses = int(await self._backend.get(f"{self.namespace}:misses") or 0) + 1
            await self._backend.set(f"{self.namespace}:misses", str(misses))
        except Exception as e:
            logger.error(f"Failed to increment misses: {e}")

    async def increment_errors(self):
        try:
            errors = int(await self._backend.get(f"{self.namespace}:errors") or 0) + 1
            await self._backend.set(f"{self.namespace}:errors", str(errors))
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


def with_memory(
    namespace: str, ttl_hours: int = 24, key_generator: Optional[Callable] = None
):
    def _get_cache_key(func: Callable, *args, **kwargs) -> str:
        if key_generator:
            return key_generator(*args, **kwargs)
        argspec = inspect.getfullargspec(func)
        first_arg = args[0] if args else kwargs.get(argspec.args[0], "")
        return str(first_arg)

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return_type = func.__annotations__.get("return")
            if not return_type or not issubclass(return_type, BaseModel):
                logger.warning(
                    f"Return type for {func.__name__} must be a subclass of BaseModel"
                )
                return await func(*args, **kwargs)

            memory = Memory[return_type](namespace, ttl_hours)
            stats = MemoryStats(namespace)

            cache_key = _get_cache_key(func, *args, **kwargs)
            cached_result = await memory.get(cache_key, return_type)
            if cached_result is not None:
                await stats.increment_hits()
                return cached_result

            await stats.increment_misses()
            await func(*args, **kwargs)
