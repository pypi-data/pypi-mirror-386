#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cookie 有效性验证模块
自动检测 LeetCode Cookie 是否过期，并在失效时提供更新指引
"""

import os
import sys
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from src.notifier import Notifier
    NOTIFIER_AVAILABLE = True
except ImportError:
    NOTIFIER_AVAILABLE = False

load_dotenv()

class CookieValidator:
    """Cookie 验证器"""
    
    def __init__(self, enable_notification=True):
        self.cookies = {
            "csrftoken": os.getenv("LEETCODE_CSRFTOKEN", ""),
            "slsession": os.getenv("LEETCODE_SLSSESSION", ""),
            "session": os.getenv("LEETCODE_SESSION", "")
        }
        self.graphql_url = "https://leetcode.cn/graphql/"
        self.enable_notification = enable_notification and NOTIFIER_AVAILABLE
        self.notifier = Notifier() if self.enable_notification else None
    
    def validate(self, verbose=True):
        """
        验证 Cookie 是否有效
        
        Args:
            verbose: 是否输出详细信息
            
        Returns:
            dict: {"valid": bool, "message": str, "user_info": dict}
        """
        result = {
            "valid": False,
            "message": "",
            "user_info": {}
        }
        
        # 检查 Cookie 是否配置
        if not all(self.cookies.values()):
            missing = [k for k, v in self.cookies.items() if not v]
            result["message"] = f"❌ Cookie 配置不完整，缺少: {', '.join(missing)}"
            if verbose:
                print(result["message"])
                print("\n📖 请参考《抓包指南.md》重新获取 Cookie")
            return result
        
        try:
            if verbose:
                print("🔍 正在验证 Cookie 有效性...")
            
            # 构造请求头
            headers = {
                "Content-Type": "application/json",
                "X-CSRFToken": self.cookies["csrftoken"],
                "Referer": "https://leetcode.cn/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Cookie": f"csrftoken={self.cookies['csrftoken']}; sl-session={self.cookies['slsession']}; LEETCODE_SESSION={self.cookies['session']}"
            }
            
            # 查询用户状态
            query = """
            query globalData {
                userStatus {
                    username
                    realName
                    isSignedIn
                    isPremium
                    checkedInToday
                }
            }
            """
            
            response = requests.post(
                self.graphql_url,
                json={"query": query},
                headers=headers,
                timeout=10
            )
            
            # 检查响应状态
            if response.status_code != 200:
                result["message"] = f"❌ 请求失败，状态码: {response.status_code}"
                if verbose:
                    print(result["message"])
                return result
            
            # 解析响应数据
            data = response.json()
            
            # 检查是否有错误
            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown error")
                result["message"] = f"❌ GraphQL 错误: {error_msg}"
                if verbose:
                    print(result["message"])
                return result
            
            # 获取用户信息
            user_status = data.get("data", {}).get("userStatus", {})
            
            # 检查是否已登录
            if not user_status.get("isSignedIn"):
                result["message"] = "❌ Cookie 已失效，用户未登录"
                
                # 发送通知
                if self.enable_notification and self.notifier:
                    self.notifier.notify_cookie_expired()
                    self.notifier.create_reminder_file("Cookie 已过期，请及时更新以继续同步笔记")
                
                if verbose:
                    print(result["message"])
                    print("\n🔧 请执行以下步骤更新 Cookie:")
                    print("   1. 打开浏览器无痕模式")
                    print("   2. 访问 https://leetcode.cn/notes/my-notes/")
                    print("   3. 登录你的账号")
                    print("   4. 按 F12 打开开发者工具")
                    print("   5. 参考《抓包指南.md》获取新的 Cookie")
                    print("   6. 更新 .env 文件中的 Cookie 配置")
                    print("\n📢 系统通知和桌面提醒文件已发送")
                return result
            
            # Cookie 有效
            result["valid"] = True
            result["user_info"] = {
                "username": user_status.get("username"),
                "realName": user_status.get("realName"),
                "isPremium": user_status.get("isPremium"),
                "checkedInToday": user_status.get("checkedInToday")
            }
            result["message"] = "✅ Cookie 有效"
            
            if verbose:
                print(f"\n✅ Cookie 验证通过！")
                print(f"   用户名: {result['user_info']['username']}")
                if result['user_info']['realName']:
                    print(f"   真实姓名: {result['user_info']['realName']}")
                print(f"   会员状态: {'是' if result['user_info']['isPremium'] else '否'}")
                print(f"   今日打卡: {'是' if result['user_info']['checkedInToday'] else '否'}")
                print(f"   验证时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            return result
            
        except requests.exceptions.Timeout:
            result["message"] = "❌ 请求超时，请检查网络连接"
            if verbose:
                print(result["message"])
            return result
        except requests.exceptions.RequestException as e:
            result["message"] = f"❌ 网络请求错误: {str(e)[:100]}"
            if verbose:
                print(result["message"])
            return result
        except Exception as e:
            result["message"] = f"❌ 未知错误: {str(e)[:100]}"
            if verbose:
                print(result["message"])
            return result
    
    def check_notes_access(self, verbose=True):
        """
        检查是否能访问笔记数据
        
        Returns:
            dict: {"accessible": bool, "message": str, "notes_count": int}
        """
        result = {
            "accessible": False,
            "message": "",
            "notes_count": 0
        }
        
        try:
            if verbose:
                print("📝 检查笔记访问权限...")
            
            headers = {
                "Content-Type": "application/json",
                "X-CSRFToken": self.cookies["csrftoken"],
                "Referer": "https://leetcode.cn/notes/my-notes/",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                "Cookie": f"csrftoken={self.cookies['csrftoken']}; sl-session={self.cookies['slsession']}; LEETCODE_SESSION={self.cookies['session']}"
            }
            
            # 使用与主程序相同的查询
            query = """
            query noteAggregateNote($aggregateType: AggregateNoteEnum!, $keyword: String, $orderBy: AggregateNoteSortingOrderEnum, $limit: Int = 100, $skip: Int = 0) {
              noteAggregateNote(aggregateType: $aggregateType, keyword: $keyword, orderBy: $orderBy, limit: $limit, skip: $skip) {
                count
                __typename
              }
            }
            """
            
            payload = {
                "operationName": "noteAggregateNote",
                "query": query.strip(),
                "variables": {
                    "aggregateType": "QUESTION_NOTE",  # 使用QUESTION_NOTE而不ALL
                    "limit": 1,
                    "skip": 0,
                    "orderBy": "DESCENDING"
                }
            }
            
            response = requests.post(
                self.graphql_url,
                json=payload,
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                # 调试信息：打印响应内容
                try:
                    error_detail = response.json()
                    result["message"] = f"❌ 笔记接口请求失败，状态码: {response.status_code}, 详情: {error_detail}"
                except:
                    result["message"] = f"❌ 笔记接口请求失败，状态码: {response.status_code}, 响应: {response.text[:200]}"
                if verbose:
                    print(result["message"])
                return result
            
            data = response.json()
            
            if "errors" in data:
                result["message"] = f"❌ 笔记接口错误: {data['errors'][0].get('message', 'Unknown')}"
                if verbose:
                    print(result["message"])
                return result
            
            note_data = data.get("data", {}).get("noteAggregateNote", {})
            notes_count = note_data.get("count", 0)
            
            result["accessible"] = True
            result["notes_count"] = notes_count
            
            if notes_count == 0:
                result["message"] = "⚠️ 笔记访问正常，但当前账号没有笔记数据"
            else:
                result["message"] = f"✅ 笔记访问正常，共有 {notes_count} 条笔记"
            
            if verbose:
                print(result["message"])
            
            return result
            
        except Exception as e:
            result["message"] = f"❌ 检查笔记访问失败: {str(e)[:100]}"
            if verbose:
                print(result["message"])
            return result
    
    def full_check(self):
        """
        完整检查：验证 Cookie + 检查笔记访问
        
        Returns:
            bool: 是否通过所有检查
        """
        print("=" * 60)
        print("🔐 LeetCode Cookie 完整性检查")
        print("=" * 60)
        
        # 第一步：验证 Cookie
        validation = self.validate(verbose=True)
        if not validation["valid"]:
            print("\n❌ Cookie 验证失败，请更新后重试")
            return False
        
        # 第二步：检查笔记访问
        notes_check = self.check_notes_access(verbose=True)
        if not notes_check["accessible"]:
            print("\n❌ 无法访问笔记数据，请检查 Cookie 权限")
            return False
        
        print("\n" + "=" * 60)
        print("✅ 所有检查通过，可以开始同步笔记！")
        print("=" * 60 + "\n")
        return True


def main():
    """命令行入口"""
    validator = CookieValidator()
    validator.full_check()


if __name__ == "__main__":
    main()
