from typing import Any

from Utils.logger import LangLogger


class Broker:
    def __init__(self):
        self._logger: Any = LangLogger("Broker")
    
    
    def connection(self):
        pass

    
    def release(self):
        pass

    
    def set_data(
        self,
        key: str,
        data: Any,
        expired_time: int = 3600 # Unit: Sec
    ):
        pass


    def get_data(
        self,
        key: str
    ):
        pass
    

    def delete_data(
        self,
        key: str
    ):
        pass