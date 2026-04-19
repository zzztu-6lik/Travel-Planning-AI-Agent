# Travel-Planning-AI-Agent
本项目是一个基于大语言模型 (LLM) 构建的旅游规划智能体 (Agent)。它能够分析用户的自然语言请求，并通过自主调用外部 API 工具，一步步地为用户提供完整的出行建议。

## 核心功能
* **多工具协同调用**：集成了航班查询 (`aviationstack`)、天气查询 (`wttr.in`) 以及景点推荐 (`Tavily Search API`)。
* **ReAct 推理框架**：基于 `Thought` (思考) 和 `Action` (行动) 的循环逻辑，模型能够根据当前获取到的信息决定下一步的操作，直到收集齐所有信息并给出最终答案。
* **兼容 OpenAI API**：使用标准的 OpenAI SDK 构建，可轻松对接任何支持 OpenAI 格式的大模型服务。

## 环境准备
在运行代码之前，请确保安装了以下依赖库：
`pip install requests tavily-python openai`

## 环境变量与配置
本项目依赖于第三方 API 来获取实时数据，运行前需配置以下参数：
1. **Tavily API Key**：用于景点搜索。需在系统环境变量中设置 `TAVILY_API_KEY`。
2. **LLM 配置**：在代码的 `__main__` 部分，填入你使用的 API Key、Base URL 以及模型名称。
3. **Aviationstack API Key**：用于航班查询。

## 快速启动
直接运行 Python 脚本即可启动测试：
`python test1.3_m.py`

程序将输出模型完整的思考过程 (`Thought`)、工具调用 (`Action`)、观察结果 (`Observation`) 以及最终的总结回答。
