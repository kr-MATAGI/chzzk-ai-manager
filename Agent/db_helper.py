import asyncio
import asyncpg
from typing import Any, List

from Utils.logger import LangLogger


class DB_Helper:
    def __init__(
        self,
        database: str,
        user: str,
        password: str,
        host: str,
        port: str = "5432",
    ):
        self._database: str = database
        self._user: str = user
        self._password: str = password
        self._host: str = host
        self._port: str = port
        
        self._logger = LangLogger("DB_Helper")
        self._conn: Any = None 

    async def connection(self):
        try:
            self._conn = await asyncpg.connect(
                database=self._database,
                user=self._user,
                password=self._password,
                host=self._host,
                port=self._port,
            )
        except Exception as e:
            self._logger.error(f"[ERROR] Failed DB Connection:\n{e or e.__class__.__name__}")
        finally:
            if self._conn:
                self._conn.close()


    async def release(self):
        try:
            await self._conn.close()
        except Exception as e:
            self._logger.error(f"[ERROR] Postgres close.")


    async def execute(
        self,
        query: str,
        *data: Any,
    ):
        await self._conn.execute(query, *data)


    async def executemany(
        self,
        query: str,
        data: List,
    ):
        await self._conn.executemany(query, data)


    async def fetch(
        self,
        query: str,
    ):
        return await self._conn.fetch(query)