#!/usr/bin/env python3
"""
Hitun.io 自动签到脚本
每天北京时间8点自动签到

使用方法：
1. 首次运行前，请手动登录 https://hitun.io/user/
2. 在浏览器开发者工具中获取cookies（F12 -> Application -> Cookies -> https://hitun.io）
3. 将cookies复制到下面的 COOKIES 变量中，格式为 "name1=value1; name2=value2"
4. 或者直接在浏览器中访问 https://hitun.io/user/checkin 并观察请求头
"""

import requests
import json
import re
import os
from datetime import datetime
import notify

# 配置信息
LOGIN_URL = "https://hitun.io/user/"
CHECKIN_URL = "https://hitun.io/user/checkin"

USERNAME = os.getenv("HITUN_USERNAME")
PASSWORD = os.getenv("HITUN_PASSWORD")

PROXY = {
    "http": os.getenv("PROXY"),
    "https": os.getenv("PROXY")
}

COOKIES = os.getenv("hitun_cookie")

def log_message(message):
    print(message)

def parse_cookies(cookie_string):
    """解析cookie字符串"""
    cookies = {}
    if not cookie_string:
        return cookies
    
    for item in cookie_string.split(';'):
        item = item.strip()
        if '=' in item:
            key, value = item.split('=', 1)
            cookies[key.strip()] = value.strip()
    
    return cookies

def checkin():
    """执行签到操作"""
    session = requests.Session()
    
    # 设置代理
    session.proxies.update(PROXY)
    log_message(f"使用代理: {PROXY['http']}")
    
    # 设置User-Agent模拟浏览器
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://hitun.io/user/",
        "X-Requested-With": "XMLHttpRequest",
    }
    session.headers.update(headers)
    
    # 如果配置了cookies，使用它们
    if COOKIES:
        cookie_dict = parse_cookies(COOKIES)
        session.cookies.update(cookie_dict)
        log_message(f"使用配置的cookies: {list(cookie_dict.keys())}")
    
    try:
        # 步骤1: 如果没有配置cookies，尝试登录
        if not COOKIES:
            log_message("未配置cookies，尝试自动登录...")
            
            # 访问登录页面
            login_page = session.get(LOGIN_URL, timeout=10)
            login_page.raise_for_status()
            
            # 尝试登录
            login_data = {
                "email": USERNAME,
                "password": PASSWORD,
            }
            
            # 尝试不同的登录端点
            login_endpoints = [
                "https://hitun.io/user/login",
                "https://hitun.io/login",
                LOGIN_URL,
            ]
            
            login_success = False
            for endpoint in login_endpoints:
                log_message(f"尝试登录端点: {endpoint}")
                login_response = session.post(endpoint, data=login_data, timeout=10)
                
                if login_response.status_code == 200:
                    response_text = login_response.text
                    if "签到" in response_text or "checkin" in response_text.lower():
                        log_message("登录成功！")
                        login_success = True
                        break
                    elif "success" in response_text.lower() or "登录成功" in response_text:
                        log_message("登录成功！")
                        login_success = True
                        break
            
            if not login_success:
                log_message("自动登录失败，请手动配置cookies")
                return {"success": False, "error": "登录失败，请配置cookies"}
        else:
            log_message("使用配置的cookies，跳过登录步骤")
        
        # 步骤2: 发送签到请求
        log_message("发送签到请求...")
        
        checkin_response = session.post(CHECKIN_URL, timeout=10)
        
        # 记录签到结果
        log_message(f"签到响应状态码: {checkin_response.status_code}")
        log_message(f"响应头: {dict(checkin_response.headers)}")
        
        # 处理压缩响应
        response_text = checkin_response.content.decode('utf-8', errors='ignore')
        
        # 尝试解析JSON响应
        try:
            result_json = json.loads(response_text)
            log_message(f"签到结果 (JSON): {json.dumps(result_json, ensure_ascii=False, indent=2)}")
            notify.send("Hitun", f"签到结果 (JSON): {json.dumps(result_json, ensure_ascii=False, indent=2)}")
            return {"success": True, "data": result_json}
        except:
            log_message(f"签到响应内容: {response_text[:1000]}")
            notify.send("Hitun", f"签到响应内容: {response_text[:1000]}")
            return {"success": False, "message": "签到结果未知"}
        
    except requests.exceptions.RequestException as e:
        error_msg = f"网络错误: {str(e)}"
        log_message(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"未知错误: {str(e)}"
        log_message(error_msg)
        return {"success": False, "error": error_msg}

def main():
    """主函数"""
    log_message("=" * 50)
    log_message("开始执行自动签到任务")
    
    if not COOKIES:
        log_message("⚠️ 警告: 未配置cookies，自动登录可能失败")
        log_message("建议手动配置cookies以提高成功率")
    
    result = checkin()

    log_message("签到任务完成")
    log_message("=" * 50)
    
    return result

if __name__ == "__main__":
    main()
