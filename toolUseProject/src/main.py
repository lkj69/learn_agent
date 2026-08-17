import os
import time

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import AIMessage, HumanMessage


from myTools import TOOLS


load_dotenv()

llm = init_chat_model(
    model=os.getenv("model"),
    base_url=os.getenv("baseUrl"),
    api_key=os.getenv("apiKey"),
)


class SmartAssistant:
    def __init__(self):
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

        self.agent = create_agent(
            model=self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
        )
        self.messages = []

    def chat(self, message: str) -> str:
        self.messages.append(HumanMessage(content=message))

        for attempt in range(1, self.max_retries + 1):
            try:
                result = self.agent.invoke({"messages": self.messages})
                reply = result["messages"][-1].content
                self.messages.append(AIMessage(content=reply))
                return reply
            except Exception as exc:
                if attempt == self.max_retries:
                    error_reply = (
                        f"抱歉，这次处理请求时连续失败了 {self.max_retries} 次。"
                        f"最后一次错误是：{exc}"
                    )
                    self.messages.append(AIMessage(content=error_reply))
                    return error_reply

                time.sleep(0.5)

        # 理论上不会走到这里，保留兜底返回，避免返回 None。
        fallback_reply = "抱歉，处理请求时发生未知错误。"
        self.messages.append(AIMessage(content=fallback_reply))
        return fallback_reply

    def reset(self):
        self.messages = []


def main():
    smart_assistant = SmartAssistant()
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
            print("已重置聊天记录！")
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
