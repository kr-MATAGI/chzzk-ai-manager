from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class BasicState(TypedDict):
    messages: Annotated[list, add_messages]
    question: Annotated[str, "Question"]
    answer: Annotated[str, "Answer"]