#在使用模板prompt的时候需要注意，我们直接传递的Message类型的数据，他并不会被正常的识别并替换。
# 因为他内部有机制，当监测到以及为message类型时就不做处理，但检测到为元组等需要进一步封装为message的数据就会在封装时进行替换
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage,AIMessage
prompt=ChatPromptTemplate.from_messages([
    HumanMessage(content="你好，{name}"),
    AIMessage(content="你好，请问有什么事吗")
    ])
full_prompt=prompt.invoke({"name":"小明"})
print(full_prompt)