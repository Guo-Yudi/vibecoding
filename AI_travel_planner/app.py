from gevent import monkey
monkey.patch_all()

import gevent
import os
import json
from gevent.queue import Queue
import textwrap
from typing import Optional

import requests
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify
from flask_sock import Sock

from src.speech_recognition import ASRClient

# ... (build_prompt 和 call_deepseek_api 函数保持不变)

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
# 科大讯飞 API 密钥
XF_APPID = (os.getenv("XF_APPID") or "").strip()
XF_API_KEY = (os.getenv("XF_API_KEY") or "").strip()
XF_API_SECRET = (os.getenv("XF_API_SECRET") or "").strip()
# 百度地图 API 密钥
BAIDU_MAP_KEY = (os.getenv("BAIDU_MAP_KEY") or "").strip()
# Supabase 配置
SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_ANON_KEY = (os.getenv("SUPABASE_ANON_KEY") or "").strip()

app = Flask(__name__, template_folder='templates', static_folder='static')
sock = Sock(app)

# ... (build_prompt 和 call_deepseek_api 函数保持不变)

def extract_travel_info_from_text(text: str) -> dict:
    """
    使用 LLM 从文本中提取旅行计划的关键信息。
    """
    prompt = f"""
    从以下文本中提取旅行计划的关键信息。文本是：“{text}”。

    你需要提取以下信息：
    - city (目的地城市)
    - days (旅行天数)
    - budget (预算)
    - interests (兴趣爱好)
    - people (人数)
    - dietary (饮食偏好)

    请严格以 JSON 格式返回提取的信息。如果某个信息在文本中没有提到，请将其值设为 null。
    JSON对象应只包含这些键。
    例如:
    {{
        "city": "巴黎",
        "days": 5,
        "budget": "2000元",
        "interests": "历史, 美食",
        "people": null,
        "dietary": null
    }}
    """
    try:
        response_text = call_deepseek_api(prompt, model="deepseek-chat")
        # AI 的返回可能包含在 Markdown 代码块中
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        extracted_info = json.loads(response_text)
        return extracted_info
    except Exception as e:
        print(f"Error during NLU extraction: {e}")
        return {}

@sock.route('/ws/audio')
def audio_socket(ws):
    """Handles the WebSocket connection for audio streaming."""
    print("WebSocket connection established for audio.")
    audio_queue = Queue()
    
    # Start the ASR client thread
    asr_greenlet = ASRClient(
        app_id=XF_APPID,
        api_key=XF_API_KEY,
        api_secret=XF_API_SECRET,
        audio_queue=audio_queue,
        client_ws=ws
    )
    asr_greenlet.start()

    try:
        while True:
            message = ws.receive()
            if message is None:
                audio_queue.put(None) # Signal end of stream
                break

            # Check for JSON message (end signal) vs. binary audio data
            if isinstance(message, str):
                try:
                    data = json.loads(message)
                    if data.get('end_stream'):
                        audio_queue.put(None) # Signal end of stream
                        break
                except json.JSONDecodeError:
                    # Not a json message, likely an error or unexpected string
                    print(f"Received unexpected string message: {message}")
            else:
                # This is binary audio data
                audio_queue.put(message)
    except Exception as e:
        print(f"Error in WebSocket loop: {e}")
    finally:
        # Give the ASR greenlet a moment to send the final result
        gevent.sleep(2)
        print("WebSocket connection closed.")

@app.route("/process-speech-text", methods=["POST"])
def process_speech_text():
    data = request.get_json()
    text = data.get("text")
    if not text:
        return jsonify({"error": "No text provided."}), 400

    extracted_info = extract_travel_info_from_text(text)

    if extracted_info:
        return jsonify({"extracted_info": extracted_info})
    else:
        return jsonify({"error": "Could not extract information from the text."}), 500


@app.route("/extract-info", methods=["POST"])
def extract_info():
    data = request.get_json()
    text = data.get("text")
    if not text:
        return jsonify({"error": "No text provided."}), 400

    extracted_info = extract_travel_info_from_text(text)

    if extracted_info:
        return jsonify({"extracted_info": extracted_info})
    else:
        return jsonify({"error": "Could not extract information from the text."}), 500

def build_prompt(
    city: str,
    days: int,
    budget: str,
    interests: str,
    people: Optional[int] = None,
    dietary: Optional[str] = None,
) -> str:
    """为 LLM 创建一个清晰、结构化的 prompt，要求输出 Markdown 格式。"""
    interests_text = interests.strip() or "忽略"
    budget_text = budget.strip() or "尽可能少"
    city_text = city.strip()
    people_text = people if (isinstance(people, int) and people > 0) else 1
    dietary_text = (dietary or "忽略").strip()

    prompt = f"""
    你是一位专业的旅行规划师。请根据以下要求，为我创建一个详细、实用、按天划分的旅行计划。

    **旅行详情:**
    - **城市:** {city_text}
    - **天数:** {days}
    - **人数:** {people_text}
    - **预算水平:** {budget_text}
    - **兴趣:** {interests_text}
    - **饮食偏好:** {dietary_text}

    **输出要求（必须严格遵守，生成格式清晰的 Markdown 文本）：**
    1.  **行程概览:** 在开头部分，提供一个简短的行程概览。
    2.  **行程摘要:** 使用无序列表简要列出上述所有旅行详情。
    3.  **每日行程:**
        - 为每一天（例如，`### 第一天`）创建一个三级标题。
        - 使用 Markdown 表格展示每日计划。
        - 表格应包含以下列：`时间`, `活动`, `区域`, `餐饮推荐`, `交通`, `大致费用`。
        - 活动或地点名称请用粗体（例如 `**外滩**`）。
    4.  **美食与交通建议:** 使用 Markdown 表格推荐 4–6 个特色美食地点。
    5.  **安全与省钱技巧:** 提供 3 条简洁实用的建议。
    - 所有一级和二级标题都应使用 Markdown 标题格式（`## 标题`）。
    - 内容需简洁而具体，优先使用表格和列表。
    """
    return textwrap.dedent(prompt).strip()


def call_deepseek_api(prompt: str, model: Optional[str] = None) -> str:
    """直接调用DeepSeek API并返回文本。"""
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY。请将其添加到 .env 文件中。")

    url = "https://api.deepseek.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
    }
    data = {
        "model": model or "deepseek-chat",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data), timeout=180)
        response.raise_for_status()  # 如果请求失败 (状态码 4xx or 5xx), 则会抛出异常
        completion = response.json()
        content = completion['choices'][0]['message']['content'] if completion.get('choices') else ""
        content = (content or "").strip()
        if not content:
            raise RuntimeError("DeepSeek API响应中没有消息内容。")
        return content
    except requests.exceptions.RequestException as e:
        # 处理网络层面的错误，例如超时、连接错误等
        raise RuntimeError(f"调用 DeepSeek API 时发生网络错误: {e}")
    except (KeyError, IndexError) as e:
        # 处理解析响应时的错误
        raise RuntimeError(f"解析 DeepSeek API 响应时出错: {e}")


@app.route("/", methods=["GET"])
def index():
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_ANON_KEY")
    return render_template(
        "index.html",
        baidu_map_key=BAIDU_MAP_KEY,
        supabase_url=SUPABASE_URL,
        supabase_anon_key=SUPABASE_ANON_KEY,
    )


@app.route("/generate", methods=["POST"])
def generate():
    city = (request.form.get("city") or "").strip()
    days_raw = (request.form.get("days") or "").strip()
    budget = (request.form.get("budget") or "").strip()
    interests = (request.form.get("interests") or "").strip()
    people_raw = (request.form.get("people") or "").strip()
    dietary = (request.form.get("dietary") or "").strip()

    if not city:
        return jsonify({'error': '请输入一个城市。'}), 400

    try:
        days = max(1, int(days_raw))
    except (ValueError, TypeError):
        days = 3
    try:
        people = max(1, int(people_raw)) if people_raw else 1
    except (ValueError, TypeError):
        people = 1

    prompt = build_prompt(city, days, budget, interests, people=people, dietary=dietary)

    try:
        if DEEPSEEK_API_KEY:
            result_text = call_deepseek_api(prompt, model="deepseek-chat")
            return jsonify({'plan': result_text})
        else:
            return jsonify({'error': '未找到API密钥。请将 DEEPSEEK_API_KEY 添加到您的 .env 文件中。'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    from gevent import pywsgi
    server = pywsgi.WSGIServer(('127.0.0.1', 8080), app)
    print("Server starting on http://127.0.0.1:8080")
    server.serve_forever()