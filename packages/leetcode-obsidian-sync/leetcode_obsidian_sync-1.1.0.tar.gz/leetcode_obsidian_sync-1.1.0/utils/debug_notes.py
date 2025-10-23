#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeetCode 笔记调试工具
帮助诊断为什么获取不到笔记
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

GRAPHQL_API = "https://leetcode.cn/graphql/"

# 完整的GraphQL查询
NOTES_LIST_QUERY = """
query noteAggregateNote($aggregateType: AggregateNoteEnum!, $keyword: String, $orderBy: AggregateNoteSortingOrderEnum, $limit: Int = 100, $skip: Int = 0) {
  noteAggregateNote(aggregateType: $aggregateType, keyword: $keyword, orderBy: $orderBy, limit: $limit, skip: $skip) {
    count
    userNotes {
      config
      content
      id
      noteType
      status
      summary
      targetId
      updatedAt
      ... on NoteAggregateLeetbookNoteNode {
        notePage {
          bookTitle
          coverImg
          linkTemplate
          parentTitle
          title
          __typename
        }
        __typename
      }
      ... on NoteAggregateQuestionNoteNode {
        noteQuestion {
          linkTemplate
          questionFrontendId
          questionId
          title
          translatedTitle
          __typename
        }
        __typename
      }
      __typename
    }
    __typename
  }
}
"""

def debug_notes():
    """调试笔记获取"""
    
    if not (COOKIES["csrftoken"] and COOKIES["slsession"]):
        print("❌ Cookie未配置，请检查.env文件")
        return
    
    print("🔍 开始调试LeetCode笔记获取...\n")
    print(f"📝 Cookie信息:")
    print(f"   csrftoken: {COOKIES['csrftoken'][:20]}... (长度: {len(COOKIES['csrftoken'])})")
    print(f"   slsession: {COOKIES['slsession'][:20]}... (长度: {len(COOKIES['slsession'])})\n")
    
    session = requests.Session()
    
    # 测试不同的笔记类型
    note_types = ["QUESTION_NOTE", "LEETBOOK_NOTE"]
    
    for note_type in note_types:
        print("=" * 70)
        print(f"📋 测试笔记类型: {note_type}")
        print("=" * 70)
        
        headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": COOKIES["csrftoken"],
            "Referer": "https://leetcode.cn/notes/my-notes/",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Cookie": f"csrftoken={COOKIES['csrftoken']}; slsession={COOKIES['slsession']}"
        }
        
        payload = {
            "operationName": "noteAggregateNote",
            "query": NOTES_LIST_QUERY.strip(),
            "variables": {
                "aggregateType": note_type,
                "limit": 10,
                "skip": 0,
                "orderBy": "DESCENDING"
            }
        }
        
        try:
            response = session.post(GRAPHQL_API, json=payload, headers=headers, timeout=15)
            
            print(f"\n📊 响应状态码: {response.status_code}")
            print(f"📝 响应头:")
            for key in ['content-type', 'set-cookie']:
                if key in response.headers:
                    print(f"   {key}: {response.headers[key][:100]}")
            
            if response.status_code == 200:
                data = response.json()
                
                # 检查是否有错误
                if "errors" in data:
                    print(f"\n❌ GraphQL错误:")
                    print(json.dumps(data["errors"], ensure_ascii=False, indent=2))
                else:
                    print(f"\n✅ 请求成功！")
                    
                    # 提取笔记数据
                    note_data = data.get("data", {}).get("noteAggregateNote", {})
                    count = note_data.get("count", 0)
                    notes = note_data.get("userNotes", [])
                    
                    print(f"\n📈 统计信息:")
                    print(f"   总笔记数: {count}")
                    print(f"   本次返回: {len(notes)} 条")
                    
                    if notes:
                        print(f"\n📝 笔记列表预览:")
                        for i, note in enumerate(notes[:3]):  # 只显示前3条
                            print(f"\n   [{i+1}] 笔记信息:")
                            print(f"      ID: {note.get('id')}")
                            print(f"      类型: {note.get('__typename')}")
                            print(f"      状态: {note.get('status')}")
                            print(f"      摘要: {note.get('summary', '')[:50]}")
                            
                            if note.get("__typename") == "NoteAggregateQuestionNoteNode":
                                question = note.get("noteQuestion", {})
                                print(f"      题目: {question.get('questionFrontendId')}. {question.get('translatedTitle') or question.get('title')}")
                                print(f"      链接: {question.get('linkTemplate')}")
                            elif note.get("__typename") == "NoteAggregateLeetbookNoteNode":
                                page = note.get("notePage", {})
                                print(f"      教程: {page.get('bookTitle')} - {page.get('title')}")
                            
                            # 显示内容预览
                            content = note.get("content", "")
                            if content:
                                print(f"      内容预览: {content[:100]}...")
                        
                        # 显示完整的第一条笔记JSON
                        if len(notes) > 0:
                            print(f"\n📄 完整JSON示例（第1条）:")
                            print(json.dumps(notes[0], ensure_ascii=False, indent=2)[:1000])
                    else:
                        print(f"\n⚠️ 该类型没有笔记")
                        print(f"\n完整响应:")
                        print(json.dumps(data, ensure_ascii=False, indent=2))
            else:
                print(f"\n❌ HTTP错误:")
                print(f"   状态码: {response.status_code}")
                print(f"   响应内容: {response.text[:500]}")
        
        except Exception as e:
            print(f"\n❌ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n")
    
    print("=" * 70)
    print("💡 调试建议:")
    print("=" * 70)
    print("1. 如果所有类型都返回0条，请检查:")
    print("   - 是否使用了正确账号的Cookie")
    print("   - 在浏览器中访问 https://leetcode.cn/notes/my-notes/ 确认有笔记")
    print("   - Cookie是否过期（重新获取csrftoken和slsession）")
    print("\n2. 如果看到GraphQL错误:")
    print("   - 可能是查询语句需要更新")
    print("   - 可能是权限问题")
    print("\n3. 获取最新Cookie的方法:")
    print("   - 浏览器访问 https://leetcode.cn/notes/my-notes/")
    print("   - 按F12打开开发者工具")
    print("   - 在Network标签找到graphql请求")
    print("   - 复制请求头中的Cookie值")

if __name__ == "__main__":
    debug_notes()
