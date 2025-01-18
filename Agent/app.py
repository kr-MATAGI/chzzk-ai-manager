import os
from typing import Dict, List, Any

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI

from Utils.logger import LangLogger, set_langsmith
from Utils.grpah_viewer import show_graph_flow
from Agent.state import BasicState

class ChzzkAgent:
    def __init__(
        self,
        llm_model: str,
        use_langsmith: bool = False,
        langsmith_trace_name: str = "Default"
    ):
        # Init
        self._logger = LangLogger("ChzzkAgent")
        self._graph = None
        self._graph_flow = None
        
        if use_langsmith:
            set_langsmith(langsmith_trace_name)

        # Load LLM
        try:
            if "gpt-4o" == llm_model:
                self._llm = ChatOpenAI(model=llm_model)
            elif "Claude3.5" == llm_model:
                pass
            self._logger.debug(f"Load LLM: {llm_model}")
        except Exception as e:
            self._logger.error(f"{e.__class__.__name__}: {e}")


    def invoke_graph(
        self,
        question: str,
        stream_mode="updates"
    ) -> str:
        for chunk in self._graph.stream({"question": question}, stream_mode=stream_mode):
            for node, value in chunk.items():
                if node:
                    self._logger.debug(f"====[{node}]====")
                if "messages" in value:
                    self._logger.debug(value["messages"])


    def build_graph(
        self,
        tools: List[Any] = []
    ):
        self._logger.debug(f"Tools: {tools}")
        self._graph_flow = StateGraph(BasicState)

        # if tools:
        #     self._llm

        # Make Graph
        self._graph_flow.add_node("User_Req", self._user_question)
        

        self._graph_flow.add_edge("User_Req", END)
        
        # Set Start point
        self._graph_flow.set_entry_point("User_Req")

        # Build Graph
        # memory = MemorySaver()
        self._graph = self._graph_flow.compile()

    
    def show_graph(self):
        show_graph_flow(self._graph)


    def _user_question(
        self,
        state: BasicState
    ) -> BasicState:
        llm_response = self._llm.invoke(state["question"])
        return BasicState(messages=llm_response)