from flask import Flask, render_template, request, jsonify
import openai
import os

app = Flask(__name__, template_folder='../templates', static_folder='../static')

# 从环境变量或配置文件中获取 API Key
# openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/plan', methods=['POST'])
def plan_trip():
    data = request.get_json()
    destination = data.get('destination')
    duration = data.get('duration')
    budget = data.get('budget')
    preferences = data.get('preferences')

    if not all([destination, duration, budget, preferences]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        # 构建发送给 GPT 的 prompt
        prompt = f"""
        请为我规划一个旅行计划，具体要求如下：
        目的地：{destination}
        天数：{duration}
        预算：{budget}
        偏好：{preferences}
        请提供详细的每日行程安排，包括景点、餐厅和住宿建议。
        """

        # 调用 OpenAI API
        # response = openai.Completion.create(
        #     engine="text-davinci-003",
        #     prompt=prompt,
        #     max_tokens=1500
        # )
        # plan = response.choices[0].text.strip()

        # 模拟一个计划，因为我们没有 API 密钥
        plan = f"""
        ### {destination} {duration}天旅行计划

        **预算:** {budget}

        **偏好:** {preferences}

        ---

        #### 第一天

        - **上午:** 抵达{destination}，入住酒店。
        - **中午:** 在酒店附近品尝当地特色午餐。
        - **下午:** 参观市中心的主要景点。
        - **晚上:** 享受一顿丰盛的晚餐，然后逛逛夜市。

        ---

        #### 第二天

        - **上午:** 前往著名的自然风光区。
        - **中午:** 在景区内的餐厅用餐。
        - **下午:** 继续探索，可以进行一些户外活动，如徒步或划船。
        - **晚上:** 返回市区，选择一家评价不错的餐厅。

        ---

        ... (更多天的行程) ...
        """

        return jsonify({'plan': plan})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=8080)