# -*- coding: utf-8 -*-
"""
该文件包含一个用于调用百度地图Web服务API中路线规划功能的函数。

主要功能:
- get_driving_route: 根据指定的起点和终点，请求驾车路线规划数据。

使用此模块前，请确保您已在百度地图开放平台申请了有效的AK (API Key)，
并已为该AK开通了路线规划服务权限。
"""

import requests
import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

# 从环境变量中获取百度地图的AK
BAIDU_MAP_AK = os.getenv("BAIDU_MAP_AK")

def get_driving_route(origin, destination, ak=BAIDU_MAP_AK):
    """
    调用百度地图驾车路线规划API，获取从起点到终点的驾车路线。

    :param origin: str, 起点位置，格式为"纬度,经度"或"城市名"。
    :param destination: str, 终点位置，格式为"纬度,经度"或"城市名"。
    :param ak: str, 用户的百度地图API密钥 (AK)。如果未提供，则从环境变量加载。
    :return: dict, 包含路线规划信息的字典。如果请求失败，则返回None。
    """
    # 百度地图路线规划API的URL
    url = "http://api.map.baidu.com/direction/v2/driving"

    # API请求参数
    params = {
        "origin": origin,
        "destination": destination,
        "ak": ak,
        "output": "json"  # 指定返回格式为json
    }

    try:
        # 发起GET请求
        response = requests.get(url, params=params)
        response.raise_for_status()  # 如果请求失败（状态码非2xx），则抛出异常

        # 解析返回的JSON数据
        result = response.json()

        # 检查API返回的状态码
        if result.get("status") == 0:
            print("成功获取驾车路线规划。")
            return result.get("result", {})
        else:
            print(f"调用百度地图API失败: {result.get('message')}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"请求百度地图API时发生网络错误: {e}")
        return None

# --- 示例用法 ---
if __name__ == '__main__':
    # 请确保您已经在.env文件中设置了 BAIDU_MAP_AK
    if not BAIDU_MAP_AK:
        print("错误：请在项目根目录下的.env文件中设置您的百度地图AK，格式为 BAIDU_MAP_AK=your_ak_here")
    else:
        # 示例：从北京天安门到北京鸟巢的驾车路线
        start_point = "40.003034,116.39159"
        end_point = "39.915, 116.404"
        
        route_info = get_driving_route(start_point, end_point)

        if route_info and 'routes' in route_info:
            # 简要打印路线信息
            for i, route in enumerate(route_info['routes']):
                print(f"\n--- 路线方案 {i+1} ---")
                print(f"距离: {route.get('distance', 'N/A')} 米")
                print(f"预计耗时: {route.get('duration', 'N/A')} 秒")
                print("\n步骤:")
                if 'steps' in route:
                    for j, step in enumerate(route['steps']):
                        # 清理HTML标签
                        instructions = step.get('instructions', '无具体指示').replace('<b>', '').replace('</b>', '')
                        print(f"  {j+1}. {instructions} (行驶 {step.get('distance', 'N/A')} 米)")
        else:
            print("未能获取到有效的路线信息。")