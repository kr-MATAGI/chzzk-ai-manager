from Utils.logger import LangLogger


class ChatCrawler:
    def __init__(
        self,
        target_streamer: str
    ):
        self._logger = LangLogger("ChatCrawler")
        self._logger.debug(f"Target Streamer: {target_streamer}")