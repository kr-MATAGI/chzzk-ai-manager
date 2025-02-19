from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    question: str = Field(description="User input")
    answer: str = Field(description="AI Agent's response")
    search_target: str = Field(description="The extracted result of the main subject in a Namuwiki search tool query.")
    tool: str = Field(description="The name of the tool to be used")


class ChatLogTableSchemas(BaseModel):
    idx: int = Field(description="A unique identifier for each record.")
    streamer: str = Field(description="The name of the live streamer.")
    chat_user: str = Field(description="The name of the user who sent the chat.")
    chat_content: str = Field(description="The content of the chat message.")
    add_date: str = Field(description="The date and time when the chat was added.")
    spon_cost: int = Field(description="The amount of money sponsored.")