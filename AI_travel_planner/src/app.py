"""
AI 旅行规划师 - Flask 应用

功能:
- 提供一个表单，用于收集城市、天数、预算和兴趣等信息
- 调用 DeepSeek API 来生成每日行程
- 在同一页面上以基本格式渲染结果

运行方式:
    - python app.py
    - 或者使用: FLASK_APP=app.py flask run
"""

# 导入标准库
import os
import textwrap
from typing import Optional

# 导入第三方库
from flask import Flask, render_template, request, flash
from dotenv import load_dotenv
from openai import OpenAI


# 如果存在 .env 文件，则从中加载环境变量
load_dotenv()

# 初始化 Flask 应用
# static_folder 和 template_folder 参数指定了静态文件和模板文件的位置
app = Flask(__name__, static_folder="../static", template_folder="../templates")
# 设置 Flask 的密钥，用于保护会话和闪现消息，建议使用环境变量进行配置
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-key")


# --- DeepSeek API 配置 ---
# 请在 .env 文件中设置您的 DEEPSEEK_API_KEY
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

"""
创建结构化prompt,要求其输出 HTML 格式的行程时间表。

@param:
    city (str): 目标城市。
    days (int): 旅行天数。
    budget (str): 预算水平（如：经济、适中、舒适）。
    interests (str): 旅行兴趣。
    people (Optional[int]): 旅行人数（可选）。
    pace (Optional[str]): 旅行节奏（可选，如：轻松、均衡、紧凑）。
    dietary (Optional[str]): 饮食偏好（可选）。
@return: 
    str: 结构化prompt
"""
def build_prompt(
    city: str,
    days: int,
    budget: str,
    interests: str,
    people: Optional[int] = None,
    pace: Optional[str] = None,
    dietary: Optional[str] = None,
) -> str:
    
    # 对输入进行清理和设置默认值
    interests_text = interests.strip() or "历史、美食、文化、隐藏的宝藏"
    budget_text = budget.strip() or "适中"
    city_text = city.strip()
    people_text = people if (isinstance(people, int) and people > 0) else 1
    pace_text = (pace or "均衡").strip()
    dietary_text = (dietary or "无").strip()

    # 构建详细的提示，指导 LLM 输出特定格式的 HTML
    prompt = f"""
    你是一个友好的、专注于学生的旅行规划师。请创建一个详细、实用、按天划分的行程。

    城市: {city_text}
    天数: {days}
    人数: {people_text}
    预算水平: {budget_text} (学生友好型)
    兴趣: {interests_text}
    旅行节奏: {pace_text} (选项: 轻松 | 均衡 | 紧凑)
    饮食偏好: {dietary_text}

    输出必须是有效的、最简化的 HTML (不含 markdown 的星号):
    - 使用 <h2> 和 <strong> 作为标题 (任何地方都不要有前导的 * 字符)。
    - 包含一个简短的 <section> 概览。
    - 包含一个 <section> "行程摘要"，其中有一个小型的 <ul> 或 <table> (包含城市、天数、人数、预算、节奏、兴趣、饮食偏好)。
    - 包含一个 <section> "每日时间线"，每天都有一个表格 (Day N)。每一行包括:
        • 时间范围 (例如, 09:00~10:30)
        • 活动 (地名使用 <strong> 标签)
        • 区域 / 社区
        • 美食站 (如果相关，吃什么以及在哪里吃)
        • 交通提示 (地铁站/公交/步行)
        • 大约的学生费用 (当地货币)
    - 包含一个 <section> "美食与交通提示"，其中有一个紧凑的表格，推荐 4-6 个地点 (地点、吃什么、费用、交通提示)。
    - 以一个 <section> "安全与省钱提示" 结尾，包含 3 个简洁的提示。
    - 保持内容简洁但具体。优先使用项目符号表格和短句。
    - 确保标题是粗体的 (如果需要，在 <h2> 中使用 <strong>)，并且不要使用星号作为项目符号。
    - 不要包含外部的 <html>/<body> 标签；只返回用于渲染的内部 HTML。
    """
    return textwrap.dedent(prompt).strip()

"""
    使用 OpenAI Python 客户端调用 DeepSeek API 并返回文本结果。

    参数:
        prompt (str): 发送给模型的提示。
        model (Optional[str]): 要使用的模型名称（可选，默认为 'deepseek-chat'）。

    返回:
        str: 从 API 返回的文本内容。

    异常:
        RuntimeError: 如果缺少 DEEPSEEK_API_KEY 或 API 响应没有内容。
    """
def call_deepseek_api(prompt: str, model: Optional[str] = None) -> str:
    
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY。请将其添加到 .env 文件中。")

    # 初始化 OpenAI 客户端，并配置为使用 DeepSeek
    client = OpenAI(
        base_url="https://api.deepseek.com",
        api_key=DEEPSEEK_API_KEY,
    )
    # 发起 API 请求
    completion = client.chat.completions.create(
        model=model or "deepseek-chat",
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    # 提取并清理响应内容
    content = completion.choices[0].message.content if completion.choices else ""
    content = (content or "").strip()
    if not content:
        raise RuntimeError("DeepSeek 的响应没有消息内容。")
    return content


@app.route("/", methods=["GET"])
def index():
    """渲染主页。"""
    return render_template("index.html", result=None, provider=None)


@app.route("/generate", methods=["POST"])
def generate():
    """处理表单提交，生成并显示行程。"""
    # 从表单中获取用户输入并去除首尾空格
    city = (request.form.get("city") or "").strip()
    days_raw = (request.form.get("days") or "").strip()
    budget = (request.form.get("budget") or "").strip()
    interests = (request.form.get("interests") or "").strip()
    people_raw = (request.form.get("people") or "").strip()
    pace = (request.form.get("pace") or "").strip()
    dietary = (request.form.get("dietary") or "").strip()

    # 基本的输入验证
    if not city:
        flash("请输入一个城市。")
        return render_template("index.html", result=None, provider=None)

    # 将天数和人数转换为整数，并处理无效输入
    try:
        days = max(1, int(days_raw))
    except (ValueError, TypeError):
        days = 3  # 设置一个合理的默认值
    try:
        people = max(1, int(people_raw)) if people_raw else 1
    except (ValueError, TypeError):
        people = 1

    # 构建发送给 LLM 的提示
    prompt = build_prompt(city, days, budget, interests, people=people, pace=pace, dietary=dietary)

    result_text = None
    provider = None
    try:
        # 检查 API 密钥是否存在
        if DEEPSEEK_API_KEY:
            # 调用 DeepSeek API 获取行程结果
            result_text = call_deepseek_api(prompt, model="deepseek-chat")
            provider = "DeepSeek (deepseek-chat)"
        else:
            # 如果没有 API 密钥，则显示闪现消息
            flash("未找到 API 密钥。请将 DEEPSEEK_API_KEY 添加到您的 .env 文件中。")
            return render_template("index.html", result=None, provider=None)
    except Exception as e:
        # 捕获并显示 API 调用过程中的任何异常
        flash(str(e))
        return render_template("index.html", result=None, provider=None)

    # 渲染带有结果的页面
    return render_template("index.html", result=result_text, provider=provider)


# 当该脚本作为主程序运行时执行
if __name__ == "__main__":
    # 从环境变量中获取端口号和调试模式设置
    port = int(os.getenv("PORT", "8080"))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    # 运行 Flask 开发服务器
    app.run(host="0.0.0.0", port=port, debug=debug)