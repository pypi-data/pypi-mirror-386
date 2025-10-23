#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeetCode API 自动探测工具
使用你的Cookie自动尝试各种可能的API接口
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# 从.env读取Cookie
COOKIES = {
    "csrftoken": os.getenv("LEETCODE_CSRFTOKEN", ""),
    "slsession": os.getenv("LEETCODE_SLSSESSION", "")
}

def test_api():
    """测试各种可能的API"""
    
    if not (COOKIES["csrftoken"] and COOKIES["slsession"]):
        print("❌ 请先在.env文件中配置Cookie")
        return
    
    print("🔍 开始探测LeetCode笔记API...\n")
    
    session = requests.Session()
    headers = {
        "X-CSRFToken": COOKIES["csrftoken"],
        "Referer": "https://leetcode.cn/notes/my-notes/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Cookie": f"csrftoken={COOKIES['csrftoken']}; slsession={COOKIES['slsession']}"
    }
    
    # 测试REST API端点
    print("=" * 60)
    print("📡 测试 REST API 端点")
    print("=" * 60)
    
    rest_apis = [
        "https://leetcode.cn/api/notes/",
        "https://leetcode.cn/api/my-notes/",
        "https://leetcode.cn/api/v1/notes/",
        "https://leetcode.cn/api/v1/my-notes/",
        "https://leetcode.cn/api/user/notes/",
        "https://leetcode.cn/notes/api/list/",
        "https://leetcode.cn/list/api/notes/",
        "https://leetcode.cn/u/notes/",
    ]
    
    for api_url in rest_apis:
        try:
            print(f"\n🔗 {api_url}")
            response = session.get(api_url, headers=headers, timeout=10, params={"page": 1, "page_size": 1})
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ 成功！")
                try:
                    data = response.json()
                    print(f"   📦 响应数据结构:")
                    print(f"      {json.dumps(list(data.keys()), ensure_ascii=False)}")
                    print(f"\n   完整响应预览:")
                    print(f"   {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                    print("\n" + "=" * 60)
                    print("🎉 找到可用的API！")
                    print(f"请在代码中使用: NOTES_LIST_API = \"{api_url}\"")
                    print("=" * 60)
                    return api_url
                except:
                    print(f"   响应内容: {response.text[:200]}")
            elif response.status_code == 404:
                print(f"   ❌ 不存在")
            elif response.status_code == 403:
                print(f"   ⚠️ 权限不足，可能Cookie过期")
            else:
                print(f"   ⚠️ 响应: {response.text[:150]}")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:100]}")
    
    # 测试GraphQL查询
    print("\n" + "=" * 60)
    print("📡 测试 GraphQL 查询")
    print("=" * 60)
    
    graphql_url = "https://leetcode.cn/graphql/"
    graphql_headers = headers.copy()
    graphql_headers["Content-Type"] = "application/json"
    
    # 常见的GraphQL查询模式
    graphql_queries = [
        {
            "name": "userNotes",
            "query": """
                query userNotes($input: NoteListInput!) {
                    userNotes(input: $input) {
                        totalNum
                        notes {
                            uuid
                            title
                            question {
                                questionFrontendId
                                title
                                titleSlug
                            }
                        }
                    }
                }
            """,
            "variables": {"input": {"page": 1, "pageSize": 1}}
        },
        {
            "name": "noteList",
            "query": """
                query noteList($page: Int!, $pageSize: Int!) {
                    noteList(page: $page, pageSize: $pageSize) {
                        total
                        notes {
                            uuid
                            title
                        }
                    }
                }
            """,
            "variables": {"page": 1, "pageSize": 1}
        },
        {
            "name": "myNoteList",
            "query": """
                query myNoteList {
                    myNoteList {
                        uuid
                        title
                        question {
                            questionFrontendId
                            title
                            titleSlug
                        }
                    }
                }
            """,
            "variables": {}
        },
    ]
    
    for item in graphql_queries:
        print(f"\n🔍 测试查询: {item['name']}")
        try:
            payload = {
                "query": item["query"].strip(),
                "variables": item["variables"]
            }
            
            response = session.post(graphql_url, json=payload, headers=graphql_headers, timeout=10)
            print(f"   状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "errors" in data:
                    print(f"   ❌ GraphQL错误: {data['errors'][0]['message'][:100]}")
                else:
                    print(f"   ✅ 成功！")
                    print(f"   📦 响应数据:")
                    print(f"   {json.dumps(data, ensure_ascii=False, indent=2)[:500]}")
                    print("\n" + "=" * 60)
                    print("🎉 找到可用的GraphQL查询！")
                    print(f"\n请在代码中添加:")
                    print(f'NOTES_LIST_QUERY = """{item["query"].strip()}"""')
                    print("=" * 60)
                    return item["query"]
            else:
                print(f"   ❌ 响应: {response.text[:150]}")
        except Exception as e:
            print(f"   ❌ 错误: {str(e)[:100]}")
    
    print("\n" + "=" * 60)
    print("😢 未找到可用的API")
    print("=" * 60)
    print("\n💡 建议：")
    print("1. 检查Cookie是否过期（重新获取csrftoken和slsession）")
    print("2. 手动在浏览器中打开 https://leetcode.cn/notes/my-notes/")
    print("3. 按F12打开开发者工具，查看Network标签中的实际请求")
    print("4. 找到加载笔记列表的请求，复制其URL或GraphQL查询")
    return None

if __name__ == "__main__":
    test_api()
