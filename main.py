import os
import time
import asyncio
from dotenv import load_dotenv

from Agent.app import ChzzkAgent
from Agent.crawler import ChatCrawler
### MAIN ###
async def main():
    load_dotenv()

    agent = ChzzkAgent(llm_model="gpt-4o")
    agent.build_graph()
    # agent.show_graph()

    answer = agent.invoke_graph(question="탬탬버린의 최근 5개 채팅내역을 보여줘.")
    print("==" * 20)
    print(answer)
    print("==" * 20)

    # chat = ChatCrawler()
    # await chat.connection()
    # await chat.crawl_live_chat(target_user="탬탬버린")

    # time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())