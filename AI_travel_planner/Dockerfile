# 使用官方 Python 运行时作为父镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 8080

# 定义环境变量，用于传递密钥
ENV DEEPSEEK_API_KEY=""
ENV XF_APPID=""
ENV XF_API_KEY=""
ENV XF_API_SECRET=""
ENV BAIDU_MAP_KEY=""
ENV SUPABASE_URL=""
ENV SUPABASE_ANON_KEY=""

# 运行 app.py
CMD ["gunicorn", "--worker-class", "gevent", "--bind", "0.0.0.0:8080", "app:app"]