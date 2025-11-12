AI Travel Planner

# 一、核心功能（实现的功能）：
|           | 作业要求                                                                    | 实现效果                                                                                      |
| --------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| 智能行程规划    | 用户可以通过语音或文字输入旅行目的地、日期、预算、同行人数、旅行偏好，AI 会自动生成个性化的旅行路线，包括交通、住宿、景点、餐厅等详细信息。 | 用户可以通过语音或文字输入（目的地、**旅行天数**、预算、同行人数、旅行偏好，饮食习惯）AI 会自动生成**详细的旅游计划**，包括旅行路线、交通、住宿、景点、餐厅等详细信息。 |
| 费用预算与管理   | 由 AI 进行预算分析，记录旅行开销。                                                     | **用户给出预算，AI生成贴近预算的计划**。                                                                   |
| 用户管理与数据存储 | 注册登录系统: 用户可以保存和管理多份旅行计划。云端行程同步: 旅行计划、偏好设置、费用记录等数据云端同步，方便多设备查看和修改。       | 注册登录系统: 用户可以保存和管理多份旅行计划。云端行程同步: **用户可以修改旅行计划内容**。                                         |

# 二、暂未实现的功能
1. 用户不能设置旅行的日期
2. 没有规划旅行线路，即没有实现在地图上的导航功能，仅有文字内容。
3. 用户不能记录实时旅行开销

# 三、技术栈
讯飞语音听写（流式版） API 提供语音识别功能
百度地图 API 提供地理位置服务和导航功能
Supabase 提供数据库和认证服务
Deepseek API 完成旅行规划

# 五、运行方式
1.  **拉取 Docker 镜像**:
    `docker pull crpi-arx8fmno0tqe2xbe.cn-hangzhou.personal.cr.aliyuncs.com/guoyudi/vibecoding:latest`

2.  **运行 Docker 容器**:
    运行以下命令来启动容器。请务必将 -e 后的参数替换为实际密钥（具体命令在Pdf文件）。
    ```bash
    docker run -p 8080:8080 \
      -e DEEPSEEK_API_KEY="your_deepseek_api_key" \
      -e XF_APPID="your_xf_appid" \
      -e XF_API_KEY="your_xf_api_key" \
      -e XF_API_SECRET="your_xf_api_secret" \
      -e BAIDU_MAP_KEY="your_baidu_map_key" \
      -e SUPABASE_URL="your_supabase_url" \
      -e SUPABASE_ANON_KEY="your_supabase_anon_key" \
      ai-travel-planner
    ```
3.  **访问应用**:
    在浏览器中打开 `http://localhost:8080`。
