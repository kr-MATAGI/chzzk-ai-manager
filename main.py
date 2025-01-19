import os
import time
from dotenv import load_dotenv

from Agent.app import ChzzkAgent
from Agent.crawler import ChatCrawler

### MAIN ###
if __name__ == "__main__":
    load_dotenv()

    # agent = ChzzkAgent(llm_model="gpt-4o")
    # agent.build_graph()
    # agent.show_graph()
    # # answer = agent.invoke_graph(
    # #     question="What is the capital of France?"
    # # )

    chat = ChatCrawler()
    a = chat.crawl_live_chat(target_user="강퀴88")

    time.sleep(10)