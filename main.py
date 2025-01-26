import os
import time
import asyncio
from dotenv import load_dotenv

from Agent.app import ChzzkAgent
from Agent.crawler import ChatCrawler
### MAIN ###
async def main():
    load_dotenv()

    # agent = ChzzkAgent(llm_model="gpt-4o")
    # agent.build_graph()
    # # agent.show_graph()

    # answer = agent.invoke_graph(question="탬탬버린 방송의 채팅에서 가장 많은 채팅을 한 사람은?")

    chat = ChatCrawler()
    await chat.connection()
    await chat.crawl_live_chat(target_user="이춘향")

    time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())