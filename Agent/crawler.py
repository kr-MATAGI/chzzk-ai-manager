import requests
import random
import time
import os
import uuid
from typing import Any, List, Dict
from datetime import datetime
from dotenv import load_dotenv

from Utils.logger import LangLogger
from Agent.headers import CHROME_HEADERS
from Agent.db_helper import DB_Helper
from Agent.broker import Broker
from Agent.query import DB_Query

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
        load_dotenv()
        self._logger = LangLogger("ChatCrawler")
        self._logger.debug(f"Selenium Version: {selenium.__version__}")

        # Set Web Driver
        self.driver = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install())
        )

        # DB
        self.db_helper = DB_Helper(
            database=os.environ["POSTGRES_DB_NAME"],
            host=os.environ["POSTGRES_HOST"],
            user=os.environ["POSTGRES_USER"],
            password=os.environ["POSTGRES_PWD"],
        )

        # Broker
        self.broker = Broker(
            host=os.environ["REDIS_HOST"],
            port=os.environ["REDIS_PORT"],
        )

    
    async def connection(self):
        await self.db_helper.connection()
        await self.broker.connection()


    async def crawl_live_chat(
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
        total_chat_history: Dict[str, List[Dict]] = self._crawling_chatting()
        for live_user, live_chat_list in total_chat_history.items():
            for chat in live_chat_list:
                # To Postgres
                await self.db_helper.execute(
                    DB_Query.INSERT_CHAT_LOGS.value, 
                    target_user, live_user, chat["content"], 0,
                )
                
        # To Redis
        self.broker.set_data(uuid.uuid4(), total_chat_history)
        
        # Live Crawling Loop
        while True:
            time.sleep(1)
            
            # Update Chatting Log
            live_chat_items: Dict[str, List[Dict]] = self._crawling_chatting()

            for live_user, live_chat_list in live_chat_items.items():
                if live_user in total_chat_history.keys():
                    # 저장된 채팅 내역이 업데이트 내역과 같으면 skip
                    # @TODO: 'ㅋㅋㅋㅋ' 와 같은 것 어떻게 처리할지 생각
                    saved_chat_logs: List[str] = [x['content'] for x in total_chat_history[live_user][-50:]]
                    for chat in live_chat_list:
                        if chat['content'] in saved_chat_logs:
                            continue

                        total_chat_history[live_user].append(chat)
                        
                        # # To Postgres
                        # await self.db_helper.execute(
                        #     DB_Query.INSERT_CHAT_LOGS, (
                        #         target_user,
                        #         live_user,
                        #         chat['content'],
                        #         0, # @TODO
                        #     )
                        # )
                else:
                    # 새롭게 유입된 유저
                    total_chat_history[live_user] = live_chat_list

                    # # To Postgres
                    # await self.db_helper.execute(
                    #     DB_Query.INSERT_CHAT_LOGS, (
                    #         target_user,
                    #         live_user,
                    #         chat['content'],
                    #         0, # @TODO
                    #     )
                    # )
            

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
    

    def _crawling_chatting(
        self,
    ):
        chat_log_history: Dict[str, List[Dict]] = {}

        # live_chatting_list_wrapper__a5XTV
        chatting_list_wrapper: WebElement = self.driver.find_element(
            By.XPATH,
            "//div[contains(@class, 'live_chatting_list_wrapper')]"
        )
        self._logger.debug(f"Chatting list wrapper: {True if chatting_list_wrapper else False}")

        # Get chatting after open browser
        chat_list_items: List[WebElement] = chatting_list_wrapper.find_elements(
            By.XPATH, 
            ".//div[contains(@class, 'live_chatting_list_item')]"
        )
        self._logger.debug(f"First Chat Size: {len(chat_list_items)}")
        
        for chat_item in chat_list_items:
            # @TODO: 후원 채팅은 유저는 검색이 됨 '익명의 후원자', 내용과 금액은 다른 Elem 사용하는 것으로 보임
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
                    chat_log_history[user_nick_name_elem.text.strip()].append({
                        "content": user_chat_elem.text.strip(),
                        "added_time": datetime.now().strftime("%Y/%m/%d_%H:%M:%S")
                    })
                else:
                    chat_log_history[user_nick_name_elem.text.strip()] = [{
                        "content": user_chat_elem.text.strip(),
                        "added_time": datetime.now().strftime("%Y/%m/%d_%H:%M:%S")
                    }]

            except Exception as e:
                if user_nick_name_elem:
                    self._logger.error(f"User: {user_nick_name_elem.text.strip()}, {e}")

        return chat_log_history