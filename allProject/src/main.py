import os
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langchain.messages import HumanMessage
from langgraph.checkpoint.postgres import PostgresSaver


from myTools import TOOLS
from middleware import create_summary_middleware,create_tool_retry_middleware

load_dotenv()
DB_URL = os.getenv("DB_URL")
llm = init_chat_model(
    model=os.getenv("model"),
    base_url=os.getenv("baseUrl"),
    api_key=os.getenv("apiKey"),
)

# checkpointer = InMemorySaver()
class SmartAssistant:
    def __init__(self, thread_id: str = "default"):
        """
        初始化智能助手
        
        Args:
            thread_id: 对话线程ID，用于管理消息历史。不同的thread_id会有独立的消息历史
        """
        self.thread_id = thread_id
        self.config = {
            "configurable": {
                "thread_id": thread_id
            }
        }
        self.model = llm
        self.tools = TOOLS
        self.max_retries = 3
        self.system_prompt = """你是一个多功能智能助手，可以帮助用户：
1. 查询天气：使用 get_weather 工具
2. 数学计算：使用 calculator 工具
3. 时间查询：使用 get_time_info 工具
4. 货币转换：使用 convert_currency 工具
5. 信息搜索：使用 search_info 工具

重要提示：
1. 仔细阅读用户问题，确定需要使用哪个工具
2. 如果需要多个工具，按顺序调用
3. 总是用友好、专业的语气回答
4. 如果工具返回了数据，要用通俗易懂的语言解释给用户
5. 如果无法完成任务，诚实地告诉用户原因
6. 请始终使用中文回答
"""
        # checkpointer 相关资源在 __enter__ 中初始化
        self._checkpointer_ctx = None
        self.checkpointer = None
        self.agent = None

    def __enter__(self):
        """进入上下文管理器，初始化 PostgresSaver 并创建 agent"""
        # 创建 PostgresSaver 并手动进入其上下文（保持连接打开）
        self._checkpointer_ctx = PostgresSaver.from_conn_string(DB_URL)
        self.checkpointer = self._checkpointer_ctx.__enter__()
        self.checkpointer.setup()
        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            middleware=[ 
                create_tool_retry_middleware(),
                create_summary_middleware(),
            ],
            checkpointer=self.checkpointer
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文管理器，关闭 PostgresSaver 连接"""
        if self._checkpointer_ctx is not None:
            self._checkpointer_ctx.__exit__(exc_type, exc_val, exc_tb)
            self._checkpointer_ctx = None
            self.checkpointer = None
            self.agent = None
        return False

    def chat(self, message: str) -> str:
        try:
            if self.agent is None:
                return "错误：智能助手未正确初始化，请使用 `with SmartAssistant() as sa:` 上下文管理器。"
            result = self.agent.invoke(
                {"messages": [HumanMessage(content=message)]},
                config=self.config,
            )
            return result["messages"][-1].content
        except Exception as exc:
            return f"抱歉，服务暂时不可用，请稍后再试。{exc}"

    def reset(self):
        """
        重置对话历史（创建新的thread_id）
        """
        import uuid
        self.thread_id = str(uuid.uuid4())
        self.config["configurable"]["thread_id"] = self.thread_id
        print(f"已创建新的对话线程，ID: {self.thread_id[:8]}...")


def main():
    with SmartAssistant() as smart_assistant:
        print("=" * 40)
        print("多功能智能助手")
        print("=" * 40)
        print("我可以帮你：")
        print("1. 查询天气")
        print("2. 数学计算")
        print("3. 时间查询")
        print("4. 货币转换")
        print("5. 信息搜索")
        print("\n输入 'quit' 退出，输入 'reset' 重置对话\n")

        while True:
            try:
                user_input = input("\n你: ")
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break

            if user_input.lower() == "quit":
                print("\n再见！")
                break

            if user_input.lower() == "reset":
                smart_assistant.reset()
                print("✅ 已清空对话历史，开始新的对话")
                continue

            if not user_input.strip():
                continue

            try:
                response = smart_assistant.chat(user_input)
                print(f"助手: {response}")
            except Exception as exc:
                print(f"助手: 程序已拦截异常，没有退出。错误信息：{exc}")


if __name__ == "__main__":
    main()
