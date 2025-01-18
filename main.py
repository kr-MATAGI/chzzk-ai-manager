import os
from dotenv import load_dotenv

from Agent.app import ChzzkAgent

### MAIN ###
if __name__ == "__main__":
    load_dotenv()

    agent = ChzzkAgent(llm_model="gpt-4o")
    agent.build_graph()
    answer = agent.invoke_graph(
        question="What is the capital of France?"
    )