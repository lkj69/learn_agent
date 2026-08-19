import asyncio
import os
import sys
import uuid
from pathlib import Path

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_mcp_adapters.client import MultiServerMCPClient


from middleware import create_summary_middleware,create_tool_retry_middleware

load_dotenv()
DB_URL = os.getenv("DB_URL")


class ThreadPostgresSaver(PostgresSaver):
    """同步 PostgresSaver 的异步包装器。

    在 Windows 上存在事件循环冲突：psycopg 异步需要 WindowsSelectorEventLoop，
    而 MCP stdio 客户端需要拉起子进程（仅 ProactorEventLoop 支持）。
    本类通过 `asyncio.to_thread` 把同步 psycopg 调用放到线程池执行，
    主事件循环保持 ProactorEventLoop 供 MCP stdio 使用，从而规避该冲突。
    同步方法内部使用 `threading.Lock` 串行化，线程池并发调用安全。
    """

    async def aget_tuple(self, config):
        return await asyncio.to_thread(self.get_tuple, config)

    async def aput(self, config, checkpoint, metadata, new_versions):
        return await asyncio.to_thread(
            self.put, config, checkpoint, metadata, new_versions
        )

    async def aput_writes(self, config, writes, task_id, task_path=""):
        return await asyncio.to_thread(
            self.put_writes, config, writes, task_id, task_path
        )

    async def alist(self, config, *, filter=None, before=None, limit=None):
        items = await asyncio.to_thread(
            lambda: list(self.list(config, filter=filter, before=before, limit=limit))
        )
        for item in items:
            yield item

# myTools 包所在的源码目录，用于以子进程方式启动 MCP 服务器
SRC_DIR = str(Path(__file__).resolve().parent)

# MCP 服务器连接配置：通过 stdio 启动 `python -m myTools`
MCP_SERVER_CONFIG = {
    "smart-assistant-tools": {
        "transport": "stdio",
        "command": sys.executable,
        "args": ["-m", "myTools"],
        "cwd": SRC_DIR,
    }
}


async def load_mcp_tools():
    """连接 MCP 服务器并加载所有 LangChain 工具。

    MCP 工具为异步调用型，必须配合 `agent.ainvoke` 使用；每次调用时会
    新建一个到 MCP 服务器的会话。
    """
    client = MultiServerMCPClient(MCP_SERVER_CONFIG)
    return await client.get_tools()


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
        # MCP 工具在 __aenter__ 中异步加载
        self.tools = None
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
        # checkpointer 相关资源在 __aenter__ 中初始化
        self._checkpointer_ctx = None
        self.checkpointer = None
        self.agent = None

    async def __aenter__(self):
        """进入异步上下文管理器：加载 MCP 工具、初始化 ThreadPostgresSaver 并创建 agent"""
        self.tools = await load_mcp_tools()
        # ThreadPostgresSaver 继承同步的 from_conn_string 上下文管理器，
        # 在此同步进入其上下文以保持连接打开；异步方法通过线程池执行同步 DB 调用
        self._checkpointer_ctx = ThreadPostgresSaver.from_conn_string(DB_URL)
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

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """退出异步上下文管理器，关闭 ThreadPostgresSaver 连接"""
        if self._checkpointer_ctx is not None:
            self._checkpointer_ctx.__exit__(exc_type, exc_val, exc_tb)
            self._checkpointer_ctx = None
            self.checkpointer = None
            self.agent = None
            self.tools = None
        return False

    async def chat(self, message: str) -> str:
        try:
            if self.agent is None:
                return "错误：智能助手未正确初始化，请使用 `async with SmartAssistant() as sa:` 上下文管理器。"
            result = await self.agent.ainvoke(
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
        self.thread_id = str(uuid.uuid4())
        self.config["configurable"]["thread_id"] = self.thread_id
        print(f"已创建新的对话线程，ID: {self.thread_id[:8]}...")


async def main():
    async with SmartAssistant() as smart_assistant:
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
                response = await smart_assistant.chat(user_input)
                print(f"助手: {response}")
            except Exception as exc:
                print(f"助手: 程序已拦截异常，没有退出。错误信息：{exc}")


if __name__ == "__main__":
    asyncio.run(main())
