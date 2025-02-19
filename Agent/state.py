from typing import Annotated, TypedDict, List
from langgraph.graph.message import add_messages


class BasicState(TypedDict):
    messages: Annotated[list, add_messages]
    question: Annotated[str, "Question"]
    answer: Annotated[str, "Answer"]
    tool: Annotated[str, "tool"]
    search_target: Annotated[str, "search_target"]
    error: Annotated[str, "latest error"]