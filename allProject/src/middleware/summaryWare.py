import os
from typing import List, Tuple, Optional

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain.agents.middleware import SummarizationMiddleware

load_dotenv()
custom_profile = {
    "max_input_tokens": 128_000
}
llm = init_chat_model(
    model=os.getenv("model"),
    base_url=os.getenv("baseUrl"),
    api_key=os.getenv("apiKey"),
    profile=custom_profile
)



class SummaryWareConfig:
    """总结中间件配置类"""
    
    def __init__(
        self,
        trigger: Optional[List[Tuple[str, int]]] = None,
        keep: Optional[Tuple[str, int]] = None
    ):
        """
        初始化中间件配置
        
        Args:
            trigger: 触发总结的条件列表，包含 (条件类型, 阈值) 的元组
                    支持的类型: 
                      - "tokens" (令牌数): 绝对令牌数 (例: 100)
                      - "messages" (消息数): 消息条数 (例: 6)
                      - "fraction" (比例): 相对比例 (例: 0.001 表示 0.1%)
                    示例: [("tokens", 100), ("messages", 6), ("fraction", 0.001)]
            keep: 保持的条件，格式为 (条件类型, 数量)
                  示例: ("messages", 2)
        """
        self.trigger = trigger or [
            ("tokens", 100),
            ("messages", 6),
            ("fraction", 0.001)
        ]
        self.keep = keep or ("messages", 2)
    
    def to_middleware(self, model) -> SummarizationMiddleware:
        """根据配置创建中间件实例"""
        return SummarizationMiddleware(
            model=model,
            trigger=self.trigger,
            keep=self.keep
        )


def create_summary_middleware(
    trigger: Optional[List[Tuple[str, int]]] = None,
    keep: Optional[Tuple[str, int]] = None
) -> SummarizationMiddleware:
    """
    创建可配置的总结中间件
    
    Args:
        trigger: 触发条件列表，默认为 [("tokens", 100), ("messages", 6), ("fraction", 0.001)]
                支持的条件: 
                  - "tokens": 绝对令牌数阈值
                  - "messages": 消息条数阈值
                  - "fraction": 相对令牌比例 (需要模型的 profile 信息)
        keep: 保持条件，默认为 ("messages", 2)
    
    Returns:
        配置好的 SummarizationMiddleware 实例
    
    注意事项:
        - 使用 "fraction" 需要在 init_chat_model 中传入 profile 信息
        - 例: profile={"max_input_tokens": 128_000}
    """
    config = SummaryWareConfig(trigger=trigger, keep=keep)
    return config.to_middleware(llm)
