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
    # agent.show_graph()
    # # answer = agent.invoke_graph(
    # #     question="What is the capital of France?"
    # # )

    chat = ChatCrawler()
    await chat.connection()
    await chat.crawl_live_chat(target_user="김호러")

    time.sleep(10)

if __name__ == "__main__":
    asyncio.run(main())