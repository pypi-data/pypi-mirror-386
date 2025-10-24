from prefect.blocks.core import Block
from pydantic import Field, SecretStr
from langchain_openai import ChatOpenAI

class ChatOpenAIBlock(Block):
    _block_type_name = "LangChain OpenAI"
    api_key: SecretStr = Field(...)
    base_url: str = Field("https://api.openai.com/v1")
    temperature: float = Field(0, ge=0, le=2)
    timeout: int = Field(30)

    def get_client(self) -> ChatOpenAI:
        return ChatOpenAI(
            api_key=self.api_key.get_secret_value(),
            base_url=self.base_url,
            temperature=self.temperature,
            timeout=self.timeout,
        )

    def test(self) -> str:
        llm = self.get_client()
        ans = llm.invoke("Hi")
        return f"✅ {ans.content[:20]}…"
