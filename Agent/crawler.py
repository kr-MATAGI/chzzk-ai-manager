import requests
import random
import time
from typing import Any, List, Dict

from Utils.logger import LangLogger
from Agent.headers import CHROME_HEADERS



import selenium
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from webdriver_manager.chrome import ChromeDriverManager

import urllib.parse


class ChatCrawler:
    def __init__(
        self,
    ):
        self._logger = LangLogger("ChatCrawler")
        self._logger.debug(f"Selenium Version: {selenium.__version__}")

        # Set Driver
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install())
        )


    def crawl_live_chat(
        self,
        target_user: str,
    ):
        self._logger.debug(f"Target User: {target_user}")

        # Get Streamer Info
        streamer_info = self._get_user_info(
            target_username=target_user
        )
        self._logger.debug(f"Streamer Info: {streamer_info}")

        # Open Live Streaming
        live_url: str = f'https://chzzk.naver.com/live/{streamer_info["channel_id"]}'
        self._open_website(url=live_url)

        
        # Crawl live chatting
        time.sleep(5) # Loading
        chatting_list_wrapper: WebElement = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'live_chatting_list_wrapper')]"
        )

        chat_list_items: List[WebElement] = chatting_list_wrapper.find_elements(
            By.XPATH, 
            "//*[contains(@class, 'live_chatting_list_item')]"
        )

        chat_log: Dict = {}
    
        print(len(chat_list_items))
        

    def _open_website(
        self,
        url: str,
    ):
        self._logger.debug(f"Open URL: {url}")
        self.driver.get(url)


    def _get_user_info(
        self,
        target_username: str,
    ):
        self._logger.debug(f"Get UserInfo Target: {target_username}")
        
        # Config
        user_info = {}
        decode_username: Any = urllib.parse.quote(target_username)
        channel_search_url: str = f"https://api.chzzk.naver.com/service/v1/search/channels?keyword={decode_username}&offset=0&size=13&withFirstChannelContent=true"
        headers = {
           'User-Agent': random.choice(CHROME_HEADERS)
        }

        try:
            search_channel_res: Any = requests.get(
                url=channel_search_url,
                verify=False,
                headers=headers
            )
            search_channel_res = search_channel_res.json()
            
            # Parse
            user_info: Dict = self._parse_user_info(
                searched_user_info=search_channel_res,
                target_username=target_username
            )

        except Exception as e:
            self._logger.debug(f"Error: {e or e.__class__.__name__}")  
        
        return user_info

    def _parse_user_info(
        self,
        searched_user_info: Any,
        target_username: str
    ) -> Dict:        
        content: Dict = searched_user_info["content"]
        for data_item in content["data"]:
            channel_info: Dict = data_item["channel"]
            if channel_info["channelName"] == target_username:
                channel_name = channel_info["channelName"]
                channel_id = channel_info["channelId"]
                return {
                    "channel_name": channel_name,
                    "channel_id": channel_id
                }
        
        return {}