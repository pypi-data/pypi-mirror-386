from prefect.blocks.core import Block
from openai import OpenAI

class OpenAPIBlock(Block):
    _block_type_name = "OpenAPI Connection"
    _logo_url = "https://www.openapis.org/img/logo.png"
    base_url: HttpUrl = Field(..., description="OpenAPI base URL")
    api_key: SecretStr = Field(..., description="OpenAPI API key")
    model: str = Field(..., description="OpenAPI model name")
    temperature: float = Field(0, ge=0, le=2)
    timeout: int = Field(30)

    def ping(self) -> str:
        try:
            client = OpenAI(
                api_key=self.api_key.get_secret_value(),
                base_url=self.base_url,
                model=self.model,
            )
            # 发送 你好
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "你好"}],
                temperature=self.temperature,
                timeout=self.timeout,
            )
            # 检查响应是否包含内容
            if response.choices and response.choices[0].message.content:
                return f"✅ Ping successful, response: {response.choices[0].message.content[:20]}…"
            else:
                return "❌ Ping failed, no content in response"
        except Exception as e:
            return f"❌ {e}"
