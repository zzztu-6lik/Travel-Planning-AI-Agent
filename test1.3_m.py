import requests
from tavily import TavilyClient
import os
from openai import OpenAI
import re

#定义提示词
System_prompt="""
你是一个航班机票推荐助手。你的任务是分析用户的请求，并使用可用工具一步步地解决问题。

# 可用工具：
- ‘get_weather(city:str)':查询指定城市的天气信息
- ’get_flight(depart_city:str, arrive_city:str)‘:根据城市和天气搜索推荐的航班信息。
- ’get_attraction(city:str,weather:str)‘:根据城市和天气搜索推荐的旅游景点。

# 输出格式要求:
你的每次回复必须严格遵循以下格式，包含一对Thought和Action：

Thought:[你的思考过程和下一步计划]
Action:[你要执行的具体行动]

Action的格式必须是以下之一：
1. 调用工具：function_name(arg_name="arg_value")
2. 结束任务：Finish[最终答案]

# 重要提示:
- 每次只输出一对Thought-Action
- Action必须在同一行，不要换行
- 当收集到足够信息可以回答用户问题时，必须使用 Action: Finish[最终答案] 格式结束

请开始吧！
"""

class OpenAICompatibleClient():
    def __init__(self,model,api_key,base_url):
        self.model = model
        self.client = OpenAI(api_key = api_key,base_url = base_url)

    def generate(self,system_prompt:str,prompt:str)->str:
        """调用LLM API来生成回应。"""
        print("正在调用大预言模型...")
        try:
            messages = [{'role':'system','content':system_prompt},
                        {'role':'user','content':prompt}]
            response = self.client.chat.completions.create(
                model = self.model,
                messages = messages,
                stream = False
            )
            answer = response.choices[0].message.content
            print("LLM响应成功。")
            return answer

        except Exception as e:
            print(f"调用LLM API时发生错误: {e}")
            return "错误:调用语言模型服务时出错。"

def get_flight(depart_city:str, arrive_city:str) -> str:
    """
    查询 【从A城市 → 飞到B城市】 的航班
    depart_city: 出发城市（如 北京）
    arrive_city: 到达城市（如 上海）
    接口文档：https://aviationstack.com/documentation?f_link_type=f_linkinlinenote&flow_extra=eyJpbmxpbmVfZGlzcGxheV9wb3NpdGlvbiI6MCwiZG9jX3Bvc2l0aW9uIjowLCJkb2NfaWQiOiI5YTJmMTU4NjI4YzBiNmQ5LWJiN2QwOTg0YTUzNGMwZWUifQ%3D%3D
    """
    params = {
        'access_key': 'get)your_access_key',
        "limit" : 5
    }

    city_map={
        "北京": "PEK",
        "上海": "SHA",
        "广州": "CAN",
        "深圳": "SZX",
        "成都": "CTU",
        "重庆": "CKG"
    }

    dep_code = city_map[depart_city]
    arr_code = city_map[arrive_city]


    if not dep_code or not arr_code:
        print("暂不支持查询该城市的航班")
    else:
        params["dep_iata" ] = dep_code
        params["arr_iata" ] = arr_code

    try:
        response = requests.get('https://api.aviationstack.com/v1/flights', params=params)
        data = response.json()
        flights = data.get("data",[])

        if not data:
            print(f"暂未找到从{depart_city}->{arrive_city}的航班信息")
        else:
            flight_departure = data["data"][0]["departure"]
            flight_arrive = data["data"][0]["arrival"]

            dep_airport = flight_departure["airport"]
            dep_sche = flight_departure["scheduled"]

            ari_airport = flight_arrive["airport"]
            ari_sche = flight_arrive["scheduled"]

        #格式转化成自然语言返回
        return (f"从{depart_city}到{arrive_city}的航班信息为：起飞机场{dep_airport},起飞时间{dep_sche},"
                f"到达机场{ari_airport}，降落时间{ari_sche}")
    except requests.exceptions.RequestException as e:
        #处理网络错误
        return f"错误：查询航班信息时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        #处理数据解析错误
        return f"错误：解析航班数据失败，可能是城市名称无效 - {e}"

def get_weather(city:str)->str:
    """
    通过调用wttr.in API查询天气信息
    :param city:
    :return:
    """
    #API端点，我们请求JSON格式的数据，格式列表参考https://github.com/chubin/wttr.in#json-format
    url = f"http://wttr.in/{city}?format=j1"

    try:
        #发起请求
        response = requests.get(url)
        response.raise_for_status()

        #解析返回的JSON数据
        data = response.json()

        #获取当天的天气状况
        current_condition=data["current_condition"][0]
        weather_desc = current_condition["weatherDesc"][0]["value"]
        tempC = current_condition["temp_C"]

        #格式转化成自然语言返回
        return f"{city}当前天气:{weather_desc},气温{tempC}摄氏度"
    except requests.exceptions.RequestException as e:
        #处理网络错误
        return f"错误：查询天气时遇到网络问题 - {e}"
    except (KeyError, IndexError) as e:
        #处理数据解析错误
        return f"错误：解析天气数据失败，可能是城市名称无效 - {e}"

def get_attraction(city:str, weather:str) -> str:
    """
    根据城市和天气，使用Tavily Search API搜索并返回优化后的景点推荐。
    """
    #1.从环境变量中读取API密钥
    api_key = os.environ.get("TAVILY_API_KEY")
    if not api_key:
        return "错误：未配置TAVILY_API_KEY环境变量。"

    #2.初始化Tavily客户端
    tavily = TavilyClient()

    #3.构造一个精确的查询
    query=f"'{city}'在'{weather}'天气下最值得去的旅游景点推荐及理由"

    try:

        #response的返回内容格式在https://docs.tavily.com/documentation/api-reference/endpoint/search
        response = tavily.search(query = query, search_depth="basic",include_answer=True)

        #5.Tavily返回的结果已经非常干净，可以直接使用
        if response.get("answer"):
            return response.get("answer")

        #没有综合性回答，则格式化原始结果
        formatted_results = []
        for result in response.get("results"):
            formatted_results.append(f"- {result['title']}: {result['content']}")
        if not formatted_results:

            return "抱歉，没有找到相关的旅游经典推荐。"

        return "根据搜索，为您找到以下信息:\n" + "\n".join(formatted_results)

    except Exception as e:
        return f"错误:执行Tavily搜索时出现问题 - {e}"


available_tools= {
    'get_flight':get_flight,
    'get_weather':get_weather,
"get_attraction": get_attraction
}

if __name__ == '__main__':
    API_KEY = "your_api"
    BASE_URL = "your_base_url"
    MODEL_ID = "your_model_id"

    llm = OpenAICompatibleClient(api_key=API_KEY,model=MODEL_ID,base_url=BASE_URL)

    user_prompt = "您好，帮我查一下北京的天气，并且搜索从上海到北京的航班，相应的根据天气给我推荐路由路线"

    prompt_history = [f"用户请求：{user_prompt}"]

    print(f"用户输入: {user_prompt}\n" + "=" * 40)

    for i in range(5):
        current_prompt = "\n".join(prompt_history)
        response = llm.generate(System_prompt,current_prompt)

        match = re.search(r'(Thought:.*?Action:.*?)(?=\n\s*(?:Thought:|Action:|Observation:)|\Z)', response,
                          re.DOTALL)
        if match :
            truncated = match.group(1).strip()
            response = truncated
        print(f"模型输出:\n{response}\n")

        prompt_history.append(response)

        action_match = re.search(r"Action: (.*)", response, re.DOTALL)
        if not action_match:
            observation = "错误: 未能解析到 Action 字段。请确保你的回复严格遵循 'Thought: ... Action: ...' 的格式。"
            observation_str = f"Observation: {observation}"
            print(f"{observation_str}\n" + "=" * 40)
            prompt_history.append(observation_str)
            continue
        action_str = action_match.group(1).strip()

        if action_str.startswith("Finish"):
            final_answer = re.match(r"Finish\[(.*)\]", action_str).group(1)
            print(f"任务完成，最终答案: {final_answer}")
            break

        # 工具名(参数="值")
        #1.拿到工具名
        tool_name = re.search(r"(\w+)\(",action_str).group(1)
        #2.拿到参数
        args_str = re.search(r"\((.*)\)",action_str).group(1)
        #3.转成字典
        kwargs = dict(re.findall(r'(\w+)="([^"]*)"', args_str))

        if tool_name in available_tools:
            observation = available_tools[tool_name](**kwargs)
        else:
            observation = f"错误:未定义的工具 '{tool_name}'"

        observation_str = f"Observation:{observation}"
        print(f"{observation_str}\n" + "=" * 40)
        prompt_history.append(observation_str)


