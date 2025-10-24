# src/dochain_block/prompt_block.py
from prefect.blocks.core import Block
from pydantic import Field
from jinja2 import Template

class PromptBlock(Block):
    _block_type_name = "Prompt Template"
    _logo_url = "https://cdn-icons-png.flaticon.com/512/2920/2920277.png"
    keywords: list[str] = Field([], description="模板中使用的变量列表")
    template: str = Field(..., description="Jinja2 模板字符串")
    def render(self, **kwargs) -> str:
        return Template(self.template).render(**kwargs)

    def test(self) -> str:
        try:
            return self.render()
        except Exception as e:
            return f"❌ 模板错误: {e}"
