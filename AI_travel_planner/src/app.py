import os
import textwrap
from typing import Optional
import requests
import json

from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
app = Flask(__name__, template_folder='../templates', static_folder='../static')

def build_prompt(
    city: str,
    days: int,
    budget: str,
    interests: str,
    people: Optional[int] = None,
    pace: Optional[str] = None,
    dietary: Optional[str] = None,
) -> str:
    """为 LLM 创建一个清晰、结构化的 prompt，要求输出 Markdown 格式。"""
    interests_text = interests.strip() or "忽略"
    budget_text = budget.strip() or "尽可能少"
    city_text = city.strip()
    people_text = people if (isinstance(people, int) and people > 0) else 1
    pace_text = (pace or "平衡").strip()
    dietary_text = (dietary or "忽略").strip()

    prompt = f"""
    你是一位专业的旅行规划师。请根据以下要求，为我创建一个详细、实用、按天划分的旅行计划。

    **旅行详情:**
    - **城市:** {city_text}
    - **天数:** {days}
    - **人数:** {people_text}
    - **预算水平:** {budget_text}
    - **兴趣:** {interests_text}
    - **旅行节奏:** {pace_text} (选项: 轻松 | 平衡 | 紧凑)
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
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    city = (request.form.get("city") or "").strip()
    days_raw = (request.form.get("days") or "").strip()
    budget = (request.form.get("budget") or "").strip()
    interests = (request.form.get("interests") or "").strip()
    people_raw = (request.form.get("people") or "").strip()
    pace = (request.form.get("pace") or "").strip()
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

    prompt = build_prompt(city, days, budget, interests, people=people, pace=pace, dietary=dietary)

    try:
        if DEEPSEEK_API_KEY:
            result_text = call_deepseek_api(prompt, model="deepseek-chat")
            return jsonify({'result': result_text})
        else:
            return jsonify({'error': '未找到API密钥。请将 DEEPSEEK_API_KEY 添加到您的 .env 文件中。'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)