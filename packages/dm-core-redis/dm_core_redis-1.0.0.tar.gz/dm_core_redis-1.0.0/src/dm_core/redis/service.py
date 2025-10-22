from django.core.cache import cache as dm_cache
from django.core.cache import caches as dm_trace_cache
from django.core.cache import caches as dm_session
from django.core.cache import caches as dm_lock
from django_redis import get_redis_connection
from django_redis.util import CacheKey
from django.conf import settings
from .utils import singleton
import logging

logger = logging.getLogger()


# We mainly use 4 types of caches:
# 0 - DM Cache - Generic purpose
# 1 - DM Lock - Global distribued locks
# 2 - DM Session - To maintain user sessions
# 3 - DM Socket - For maintaining web socket connections
# 4 - DM Worker - For RQ

@singleton
class RedisClient(object):

    def __init__(self):
        self.__redis = dm_cache

    def set(self, key, value, timeout=None):
        return self.__redis.set(key, value, timeout)

    def get(self, key):
        return self.__redis.get(key)

    def delete(self, key) -> bool:
        return self.__redis.delete(key)

    def delete_pattern(self, key):
        return self.__redis.delete_pattern(key)

    def ttl(self, key):
        return self.__redis.ttl(key)


def cache(static_key, static_cache_timeout=None):
    """
    Upsert Cache Operation
    """

    def wrapper(func):
        def f(*args, **kwargs):
            """
            func: Function passed to decorator
            cache_key: Named argument of the function to set 'cache' key
            cache_refresh: Named argument of the function force the cache to 'refresh'
            :param args: Unnamed arguments of the Function func
            :param kwargs: Named arguments of the Function func
            :return:
            """
            redis = RedisClient()
            # Note: We are doing kwars.get deliberately as we want to pass the
            # values to underlying func, so that they can be asserted if required
            if 'cache_key' in kwargs and kwargs['cache_key'] is not None:
                key = '{}.{}'.format(static_key, kwargs.get('cache_key'))
            else:
                key = '{}'.format(static_key)
            result = redis.get(key)

            if static_cache_timeout is not None:
                timeout = static_cache_timeout
            else:
                timeout = kwargs.get('cache_timeout', None)

            if kwargs.get('cache_refresh', False) is True or result is None:
                result = func(*args, **kwargs)
                redis.set(key, result, timeout)
                logger.debug("Set cache key: {}".format(key))
            else:
                logger.debug("Retrieved cache key: {}".format(key))
            return result

        return f

    return wrapper


def cache_read(static_key):
    """
    Read Cache Operation
    """

    def wrapper(func):
        def f(*args, **kwargs):
            """
            func: Function passed to decorator
            cache_key: Named argument of the function to set 'cache' key
            :param args: Unnamed arguments of the Function func
            :param kwargs: Named arguments of the Function func
            :return: None or Object
            """
            redis = RedisClient()
            if 'cache_key' in kwargs and kwargs['cache_key'] is not None:
                key = '{}.{}'.format(static_key, kwargs.pop('cache_key'))
            else:
                key = '{}'.format(static_key)
            cached_data = redis.get(key)
            logger.info("Retrieved cache key: {}".format(key))
            kwargs['cache_data'] = cached_data
            result = func(*args, **kwargs)
            return result

        return f

    return wrapper


def cache_remove(static_key):
    """
    Remove Cache Operation
    """

    def wrapper(func):
        def f(*args, **kwargs):
            """
            func: Function passed to decorator
            cache_key: Named argument of the function to set 'cache' key
            :param args: Unnamed arguments of the Function func
            :param kwargs: Named arguments of the Function func
            :return: None or Object
            """
            redis = RedisClient()
            if 'cache_key' in kwargs and kwargs['cache_key'] is not None:
                key = '{}.{}'.format(static_key, kwargs.pop('cache_key'))
            else:
                key = '{}'.format(static_key)
            cache_deleted = redis.delete(key)
            logger.info("Deleting cache key: {}".format(key))
            kwargs['cache_delete'] = cache_deleted
            result = func(*args, **kwargs)
            return result

        return f

    return wrapper


@singleton
class RedisSessionManager(object):

    def __init__(self):
        self.cache = dm_session['session']

    def set_session(self, key: str, data: bytes, expires: int):
        complete_key = CacheKey('{}:{}'.format(settings.CACHES['session']['KEY_PREFIX'], key))
        return self.cache.set(complete_key, data, expires)

    def unset_session(self, key: str):
        complete_key = CacheKey('{}:{}'.format(settings.CACHES['session']['KEY_PREFIX'], key))
        return self.cache.delete(complete_key)

    def get(self, key):
        complete_key = CacheKey('{}:{}'.format(settings.CACHES['session']['KEY_PREFIX'], key))
        return self.cache.get(complete_key)


@singleton
class RedisLock(object):

    def __init__(self):
        self._redis = dm_lock['lock']
        self._service = settings.SERVICE

    def lock(self, key, expire=30, auto_renewal=True, lock_id=None):
        """
        Acquire lock
        """
        if lock_id is None:
            return self._redis.lock(f"{self._service}.{key}", expire=expire, auto_renewal=auto_renewal)
        else:
            return self._redis.lock(f"{self._service}.{key}", expire=expire, auto_renewal=auto_renewal, id=f"{self._service}.{lock_id}")

    def release(self, lock):
        """
        Release lock
        """
        return lock.release()


@singleton
class RedisListManager:
    """
    Designed/Developed for managing redis lists

    __init__ cache_alias: can be 'socket' or 'default' or 'lock'
    """

    def __init__(self, cache_alias):
        self._redis = get_redis_connection(cache_alias)

    def add(self, key: str, value: str) -> str:
        """
        Add value to the list if it doesn't already exist.
        Uses Redis LPOS to check presence, and RPUSH to append.
        """
        if self._redis.lpos(key, value) is None:
            self._redis.rpush(key, value)
        return value

    def remove(self, key: str, value: str) -> bool:
        """
        Remove value from list. If list becomes empty, delete the key.
        Uses Redis LREM.
        """
        removed = self._redis.lrem(key, 1, value)
        if self._redis.llen(key) == 0:
            self._redis.delete(key)
        return removed > 0

    def get(self, key: str) -> list[str] | None:
        """
        Get the entire list for a key, or None if it doesn't exist.
        """
        if not self._redis.exists(key):
            return None
        return [item.decode() for item in self._redis.lrange(key, 0, -1)]
