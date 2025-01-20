import redis.asyncio as redis
from typing import Any

from Utils.logger import LangLogger


class Broker:
    def __init__(
        self,
        host: str,
        port: str,
    ):
        self._logger = LangLogger("Broker")
        self._host: str = host
        self._port: str = port
        self._conn: Any = None
    
    
    def connection(self):
        try:
            self._conn = redis.Redis(
                host=self._host,
                port=self._port,
                decode_responses=True,
            )
            self._logger.debug("Connected")
        except Exception as e:
            self._logger.error(f"[ERROR] Redis Connection Failed, {e or e.__class__.__name__}")

    
    async def release(self):
        if self._conn:
            await self._conn.close()
            self._logger.debug(f"Close Redis Connection.")
        else:
            self._logger.debug(f"Not connected with redis")

                
    def set_data(
        self,
        key: str,
        data: Any,
        expired_time: int = 3600 # Unit: Sec
    ):
        pass


    async def get_data(
        self,
        key: str
    ):
        return await self._conn.get(key)
    
    async def delete_data(
        self,
        key: str
    ):
        pass


    async def publish(
        self,
    ):
        pass


    async def subscript(
        self,
    ):
        pass