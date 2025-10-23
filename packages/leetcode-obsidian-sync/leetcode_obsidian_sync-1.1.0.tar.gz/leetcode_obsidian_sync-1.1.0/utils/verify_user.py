#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证Cookie对应的用户信息
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

COOKIES = {
    "csrftoken": os.getenv("LEETCODE_CSRFTOKEN", ""),
    "slsession": os.getenv("LEETCODE_SLSSESSION", ""),
    "session": os.getenv("LEETCODE_SESSION", "")
}

def verify_user():
    """验证当前Cookie对应的用户"""
    
    print("🔍 验证Cookie对应的用户信息...\n")
    
    session = requests.Session()
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": COOKIES["csrftoken"],
        "Referer": "https://leetcode.cn/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Cookie": f"csrftoken={COOKIES['csrftoken']}; sl-session={COOKIES['slsession']}; LEETCODE_SESSION={COOKIES['session']}"
    }
    
    # 获取当前用户信息
    query = """
    query globalData {
        userStatus {
            username
            realName
            isSignedIn
            isPremium
        }
    }
    """
    
    try:
        response = session.post(
            "https://leetcode.cn/graphql/",
            json={"query": query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get("data", {}).get("userStatus", {})
            
            print("✅ 当前Cookie对应的用户:")
            print(f"   用户名: {user.get('username')}")
            print(f"   真实姓名: {user.get('realName')}")
            print(f"   是否登录: {user.get('isSignedIn')}")
            print(f"   是否会员: {user.get('isPremium')}\n")
            
            # 直接访问笔记页面，看HTML中是否有笔记数据
            print("📝 尝试访问笔记页面...")
            notes_page = session.get(
                "https://leetcode.cn/notes/my-notes/",
                headers=headers,
                timeout=10
            )
            
            if "noteAggregateNote" in notes_page.text:
                print("✅ 笔记页面中包含笔记数据")
            else:
                print("⚠️ 笔记页面中未找到笔记数据")
                
            # 查找页面中的笔记计数
            if '"count":' in notes_page.text:
                import re
                counts = re.findall(r'"count":(\d+)', notes_page.text)
                print(f"   页面中找到的count值: {counts}")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text[:200]}")
    
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    verify_user()
