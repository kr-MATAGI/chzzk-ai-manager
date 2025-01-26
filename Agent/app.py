import os
import pandas as pd
from dotenv import load_dotenv
from typing import Dict, List, Any
from enum import StrEnum

# 비동기
# https://langchain-ai.github.io/langgraph/how-tos/persistence_postgres/
import psycopg2

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import PromptTemplate

from langgraph.graph import START, END, StateGraph
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_openai import ChatOpenAI

from Utils.logger import LangLogger, set_langsmith
from Utils.grpah_viewer import show_graph_flow
from Agent.state import BasicState
from Agent.response_model import AgentResponse, ChatLogTableSchemas

class AgentMode(StrEnum):
    NONE = "none"
    NORMAL = "normal"
    DB = "db"
    LAST = "last"

class ChzzkAgent:
    def __init__(
        self,
        llm_model: str,
        use_langsmith: bool = False,
        langsmith_trace_name: str = "Default"
    ):
        # Init
        self._logger = LangLogger("ChzzkAgent")
        self._llm_model: str = llm_model
        self._graph = None
        self._graph_flow = None

        self._parser = PydanticOutputParser(pydantic_object=AgentResponse)

        self._db_config: Dict[str, str] = {
            "dbname": os.environ["POSTGRES_DB_NAME"],
            "user": os.environ["POSTGRES_USER"],
            "password": os.environ["POSTGRES_PWD"],
            "host": os.environ["POSTGRES_HOST"],
            "port": os.environ["POSTGRES_PORT"]
        }
        
        if use_langsmith:
            set_langsmith(langsmith_trace_name)
        

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
                if {"question", "answer"}.issubset(value):
                    self._logger.debug(
                        f"질문: {value['question']}\n답변: {value['answer']}"
                    )


    def build_graph(
        self,
    ):
        # Init
        self._graph_flow = StateGraph(BasicState)

        # Tools

        # Load LLM
        try:
            if "gpt-4o" == self._llm_model:
                self._llm = ChatOpenAI(model=self._llm_model)
            elif "Claude3.5" == self._llm_model:
                pass
            self._logger.debug(f"Load LLM: {self._llm_model}")
        except Exception as e:
            self._logger.error(f"{e.__class__.__name__}: {e}")

        # Make Node
        self._graph_flow.add_node("agent", self._agent_call)
        self._graph_flow.add_node("db_node", self._query_search_node)

        # Make Edge
        self._graph_flow.add_edge(START, "agent")

        self._graph_flow.add_conditional_edges(
            "agent",
            self._is_normal_question,
            {
                AgentMode.NORMAL.value: END,
                AgentMode.DB.value: "db_node",
            }
        )

        self._graph_flow.add_edge("db_node", "agent")
        self._graph_flow.add_edge("agent", END)
        
        # Build Graph
        # memory = MemorySaver()
        self._graph = self._graph_flow.compile()

    
    def show_graph(self):
        show_graph_flow(self._graph)


    def _agent_call(
        self,
        state: BasicState
    ) -> BasicState:
        question: str = state["question"]
        
        if not "tool" in state.keys():
            prompt = PromptTemplate.from_template("""
            You are an AI Agent. 
            Respond to the user's question, considering the possibility of using the following tools when necessary:
            <Tool Types>
            - DB: If data retrieval is required, make use of the this.
            - NORMAL: Organize responses to general user questions or answers to search results.

            User Input: {question}

            Format: {format}
            """)

            prompt = prompt.partial(format=self._parser.get_format_instructions())
            chain = prompt | self._llm | self._parser

            llm_response: AgentResponse = chain.invoke(question)
            
            return {
                "messages": [llm_response.model_dump_json()],
                "question": question,
                "answer": llm_response.answer,
                "tool": llm_response.tool,
            }
        
        elif AgentMode.LAST.value == state["tool"]:
            prompt = PromptTemplate.from_template("""
            You are an AI Agent.
            Organize it into a response to show the user.
            Answer in Korean.
                                                  
            User Input: {question}
            Information: {information}
            """)
            prompt = prompt.partial(
                information=state["answer"]
            )
            chain = prompt | self._llm
            llm_response = chain.invoke(state["question"])
            
            return {
                "messages": [llm_response],
                "answer": llm_response.content
            }
        
        # else:
        #     llm_response = self._llm_model.invoke(state["question"])
        #     return BasicState(
        #         messages=llm_response["messages"],
        #         answer=llm_response
        #     )
    
    def _is_normal_question(
        self,
        state: BasicState
    ) -> BasicState:
        if state["tool"].lower() == AgentMode.DB.value:
            return AgentMode.DB.value
        else:
            return AgentMode.NORMAL.value

    
    def _query_search_node(
        self,
        state: BasicState
    ) -> BasicState:
        prompt: str = PromptTemplate.from_template("""
        You are an expert SQL assistant. Generate a valid SQL query based on the user's input.
        Ensure the query is safe and assumes a table named 'tbl_chat_log' with the following columns:
        - idx (integer): A unique identifier for each record.
        - streamer (text): The name of the live streamer.
        - chat_user (text): The name of the user who sent the chat.
        - chat_content (text): The content of the chat message.
        - add_date (timestamp): The date and time when the chat was added.
        - spon_cost (integer): The amount of money sponsored.

        User Input: {question}
        Format: {format}
        """)

        prompt = prompt.partial(format=self._parser.get_format_instructions())
        chain = prompt | self._llm | self._parser
        
        llm_response: AgentResponse = chain.invoke(state["question"])
        llm_response.tool = AgentMode.NONE.value
        
        try:
            query: str = llm_response.answer

            conn = psycopg2.connect(**self._db_config)

            cursor = conn.cursor()
            cursor.execute(query)
            db_results: Any = cursor.fetchall()

            pd_df: pd.DataFrame = pd.DataFrame(
                data=db_results,
                columns=list(ChatLogTableSchemas.model_fields.keys())
            )
            
        except Exception as e:
            return {
                "error": AgentMode.DB.value
            }
        
        finally:
            cursor.close()
            conn.close()

        return {
            "messages": [llm_response.model_dump_json()],
            "answer": pd_df.to_string(),
            "tool": AgentMode.LAST.value
        }