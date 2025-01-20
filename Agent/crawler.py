import requests
import random
import time
from typing import Any, List, Dict
from datetime import datetime

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
        time.sleep(3) # Loading
        # live_chatting_list_wrapper__a5XTV
        chatting_list_wrapper: WebElement = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'live_chatting_list_wrapper')]"
        )
        self._logger.debug(f"Chatting list wrapper: {True if chatting_list_wrapper else False}")

        # Get chatting after open browser
        chat_log_history: Dict = {}

        chat_list_items: List[WebElement] = chatting_list_wrapper.find_elements(
            By.XPATH, 
            ".//div[contains(@class, 'live_chatting_list_item')]"
        )
        self._logger.debug(f"First Chat Size: {len(chat_list_items)}")
        
        for chat_item in chat_list_items:
            # name_ellipsis__Hu9B+->name_text__yQG50, live_chatting_message_text__DyleH
            
            try:
                user_nick_name_elem: WebElement = chat_item.find_element(
                    By.XPATH,
                    ".//span[contains(@class, 'name_text')]"
                )
                user_chat_elem: WebElement = chat_item.find_element(
                    By.XPATH,
                    ".//span[contains(@class, 'live_chatting_message_text')]"
                )

                if user_nick_name_elem.text in chat_log_history.keys():
                    chat_log_history[user_nick_name_elem.text].append({
                        "content": user_chat_elem.text,
                        "added_time": datetime.now().strftime("%Y/%m/%d_%H:%M:%S")
                    })
                else:
                    chat_log_history[user_nick_name_elem.text] = [{
                        "content": user_chat_elem.text,
                        "added_time": datetime.now().strftime("%Y/%m/%d_%H:%M:%S")
                    }]

            except Exception as e:
                if user_nick_name_elem:
                    self._logger.error(f"User: {user_nick_name_elem.text}, {e}")
            
        # Test
        # for k, v in chat_log_history.items():
        #     print(f"{k}:\n{v}\n\n")

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