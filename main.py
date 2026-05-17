import requests
import ollama
import schedule
import time
from fastapi import FastAPI

# 初始化接口服务
app = FastAPI(title="天气查询智能体")

# 1. 天气API配置（免费稳定接口）
WEATHER_API_URL = "http://wttr.in/"
# 城市编码/城市名
DEFAULT_CITY = "beijing"

# 2. 原始天气数据获取
def get_raw_weather(city: str = DEFAULT_CITY) -> str:
    """调用第三方天气接口拿到原始天气信息"""
    try:
        # 格式化返回纯文本天气数据
        resp = requests.get(f"{WEATHER_API_URL}{city}?format=3")
        if resp.status_code == 200:
            return resp.text
        return "天气数据查询失败"
    except Exception as e:
        return f"接口请求异常：{str(e)}"

# 3. Ollama智能整理播报文案
def ai_weather_voice_broadcast(city: str = DEFAULT_CITY) -> str:
    weather_data = get_raw_weather(city)
    prompt = f"""
请根据以下实时天气数据，生成简洁通顺的日常天气播报，
并合理给出出行、穿衣简短建议，语气自然亲切：
天气原始数据：{weather_data}
只输出播报内容，不要多余解释
"""
    res = ollama.chat(
        model="gemma2:2b",  # ✅ 这里改成 gemma2:2b 了
        messages=[{"role":"user","content":prompt}]
    )
    return res["message"]["content"]

# 4. 定时自动实时推送天气
def auto_real_time_weather_push():
    print("【智能体定时实时天气播报】")
    content = ai_weather_voice_broadcast()
    print(content)
    print("-"*50)

# 5. 对外API接口调用
@app.get("/weather/query")
def query_weather(city: str = DEFAULT_CITY):
    """外部直接调用接口获取AI天气播报"""
    return {
        "city": city,
        "weather_broadcast": ai_weather_voice_broadcast(city)
    }

# 6. 自然语言指令解析执行
def command_parse():
    print("\n天气智能体已就绪，输入指令：查天气/城市名天气/退出")
    while True:
        user_input = input("请下达指令：")
        if user_input in ["退出","quit","exit"]:
            print("智能体休眠")
            break
        if "天气" in user_input:
            if len(user_input) > 2:
                city = user_input.replace("天气","").strip()
                print(ai_weather_voice_broadcast(city))
            else:
                print(ai_weather_voice_broadcast())

# 主入口
if __name__ == "__main__":
    # 设置每30分钟自动实时查询推送
    schedule.every(30).minutes.do(auto_real_time_weather_push)
    
    # 后台运行定时任务
    import threading
    def run_schedule():
        while True:
            schedule.run_pending()
            time.sleep(1)
    threading.Thread(target=run_schedule, daemon=True).start()

    # 开启指令交互 + 可同时启动接口服务
    command_parse()