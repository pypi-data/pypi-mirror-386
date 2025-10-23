"""思维导图数据模型"""

from typing import Optional
from pydantic import BaseModel, Field

class Mind(BaseModel):
    """思维导图生成模型"""
    content: str = Field(..., description="思维导图内容")
    format: Optional[str] = Field(None, description="文本格式，例如markdown")


class MindGenerateResult(BaseModel):
    """思维导图生成结果"""
    url: str = Field("", description="生成的思维导图html链接")