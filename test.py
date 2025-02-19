import os
import time
import asyncio
from dotenv import load_dotenv

from Agent.app import ChzzkAgent
from Agent.crawler import ChatCrawler


async def crawler_test():
    chat = ChatCrawler()
    await chat.connection()
    await chat.crawl_live_chat(target_user="하나코 나나")

    await asyncio.sleep(10)


async def agent_test():
    agent = ChzzkAgent(llm_model="gpt-4o")
    agent.build_graph()
    # # agent.show_graph()

    # answer = agent.invoke_graph(question="탬탬버린 방송의 채팅에서 가장 많은 채팅을 한 사람은?")
    answer = agent.invoke_graph(question="이재용은 언제 태어났는가?")

    await asyncio.sleep(10)

if __name__ == "__main__":
    load_dotenv()

    # asyncio.run(crawler_test())
    asyncio.run(agent_test())