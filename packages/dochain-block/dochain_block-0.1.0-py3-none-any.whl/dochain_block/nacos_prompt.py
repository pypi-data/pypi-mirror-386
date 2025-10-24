from prefect.blocks.core import Block
from pydantic import Field
from jinja2 import Template

class NacosPromptBlock(Block):
    _block_type_name = "Nacos Prompt Template"
    _logo_url = "https://nacos.io/img/nacos-logo.png"

    nacos_block: str = Field(..., description="NacosBlock 连接实例名称")
    data_id: str = Field(..., description="配置 data-id")
    group: str = Field("DEFAULT_GROUP", description="配置 group")
    cache_seconds: int = Field(60, description="本地缓存秒数（0=不缓存）")

    def get_prompt(self, **kwargs) -> str:
        """从 Nacos 拉模板 → Jinja2 渲染 → 返回字符串"""
        from dochain_block.nacos import NacosBlock

        client = NacosBlock.load(self.nacos_block).get_client()
        template_str = client.get_config(self.data_id, self.group)

        return Template(template_str).render(**kwargs)

    def test(self) -> str:
        try:
            txt = self.get_prompt()  # 无变量渲染
            return f"✅ got {len(txt)} chars"
        except Exception as e:
            return f"❌ failed: {e}"
