import os
import pandas as pd
import requests
import urllib
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
    NAMU = "namu"
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
                    self._logger.debug(f"-->\n{value}")
                if "messages" in value:
                    self._logger.debug(value["messages"])


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
        self._graph_flow.add_node("agent", self._agent_call) # 답변 및 구분
        self._graph_flow.add_node("db_node", self._query_search_node) # DB 검색
        self._graph_flow.add_node("namuwiki", self._namuwiki_search_node) # 나무위키 검색

        # Make Edge
        self._graph_flow.add_edge(START, "agent")

        self._graph_flow.add_conditional_edges(
            "agent",
            self._is_normal_question,
            {
                AgentMode.NORMAL.value: END,
                AgentMode.DB.value: "db_node",
                AgentMode.NAMU.value: "namuwiki",
            }
        )

        # END
        self._graph_flow.add_edge("db_node", "agent")
        self._graph_flow.add_edge("namuwiki", "agent")
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
            - NAMU: If a request is made to search for a specific person(or streamer). Answe
            - NORMAL: Organize responses to general user questions or answers to search results.

            User Input: {question}

            Format: {format}
            """)

            prompt = prompt.partial(format=self._parser.get_format_instructions())
            chain = prompt | self._llm

            llm_response = chain.invoke(question)
            structured_output: AgentResponse = self._parser.parse(llm_response.content)

            return {
                "messages": [llm_response],
                "question": structured_output.question,
                "answer": structured_output.answer,
                "search_target": structured_output.search_target,
                "tool": structured_output.tool,
                "error": "",
            }
        
        elif state['error']:
            pass

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
        elif state["tool"].lower() == AgentMode.NAMU.value:
            return AgentMode.NAMU.value
        else:
            return AgentMode.NORMAL.value

    
    def _query_search_node(
        self,
        state: BasicState
    ) -> BasicState:
        prompt: PromptTemplate = PromptTemplate.from_template("""
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
        chain = prompt | self._llm
        
        llm_response = chain.invoke(state["question"])
        structured_output: AgentResponse = self._parser.parse(llm_response.content)
        structured_output.tool = AgentMode.NONE.value
        
        try:
            query: str = structured_output.answer
            conn = psycopg2.connect(**self._db_config)

            cursor = conn.cursor()
            cursor.execute(query)
            db_results: Any = cursor.fetchall()

            pd_df: pd.DataFrame = pd.DataFrame(
                data=db_results,
                # columns=list(ChatLogTableSchemas.model_fields.keys())
            )
            
        except Exception as e:
            return {
                "error": AgentMode.DB.value
            }
        
        finally:
            cursor.close()
            conn.close()

        return {
            "messages": [llm_response],
            "answer": pd_df.to_string(),
            "tool": AgentMode.LAST.value,
            "error": "",
        }
    

    def _namuwiki_search_node(
        self,
        state: BasicState
    ):
        target_user: str = state["search_target"]
        target_user = urllib.parse.quote(target_user)
        try:
            namu_doc: str = requests.get(url=f"https://namu.wiki/w/{target_user}")
            namu_doc = namu_doc.text[:2000] # 데이터 추가 가공 필요

            prompt: PromptTemplate = PromptTemplate.from_template("""
            You are an advanced AI assistant specializing in extracting precise answers from Namuwiki articles.  
            You will be given a passage from Namuwiki that contains relevant information regarding a user's question.  

            ## **Instructions:**
            1. Carefully analyze the provided Namuwiki passage.
            2. Identify the key information that directly answers the user's question.
            3. If multiple relevant parts exist, synthesize them into a clear and concise response.
            4. Ensure that the response is **written in fluent and natural Korean** with proper grammar and formatting.
            5. Do NOT provide unnecessary explanations, metadata, or unrelated information.  

            ## **User Input and Namuwiki Passage**
            - User Question: {question}
            - Namuwiki Passage: {document}

            ## **Response Format (Korean Output)**
            - Format: {format}
            """)

            prompt = prompt.partial(format=self._parser.get_format_instructions())

            chain = prompt | self._llm
            llm_response = chain.invoke({
                "question": state["question"],
                "document": namu_doc,
            })

            structured_output: AgentResponse = self._parser.parse(llm_response.content)
            structured_output.tool = AgentMode.NONE.value
            print(structured_output)

            return {
                "messages": [llm_response],
                "answer": structured_output.answer,
                "tool": AgentMode.LAST.value,
                "error": "",
            }

        except Exception as e:
            return {
                "error": AgentMode.NAMU.value
            }