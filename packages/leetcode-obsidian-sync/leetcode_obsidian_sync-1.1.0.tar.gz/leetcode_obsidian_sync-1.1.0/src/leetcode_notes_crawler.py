import os
import sys
import re
import time
import json
import requests
import warnings
from dotenv import load_dotenv

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cookie_validator import CookieValidator

# 解决SSL版本警告
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except:
    pass
warnings.filterwarnings('ignore')

# 加载.env文件中的所有隐私配置（Cookie、路径等）
load_dotenv()

# -------------------------- 配置参数（需根据抓包结果修改） --------------------------
# 1. 从.env读取隐私配置
OBSIDIAN_NOTES_PATH = os.getenv("OBSIDIAN_PATH", "")
MANUAL_COOKIES = {
    "csrftoken": os.getenv("LEETCODE_CSRFTOKEN", ""),
    "slsession": os.getenv("LEETCODE_SLSSESSION", ""),
    "session": os.getenv("LEETCODE_SESSION", "")
}

# 2. LeetCode GraphQL接口（通常无需修改，LeetCode通用）
GRAPHQL_API = "https://leetcode.cn/graphql/"

# 3. 请求间隔（避免反爬）
REQUEST_DELAY = 2

# 4. GraphQL查询语句（从抓包Payload复制，确保与LeetCode一致）
# 笔记列表查询 - 使用真实的noteAggregateNote查询
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

# 笔记内容查询（内容已经在列表中返回了，但保留此查询以备用）
NOTE_CONTENT_QUERY = """
query noteDetail($uuid: String!) {
    note(uuid: $uuid) {
        uuid
        content
        question {
            questionId
            questionFrontendId
            title
            titleSlug
        }
    }
}
"""
# ------------------------------------------------------------------------------

def clean_content(content):
    """清洗内容用于更新对比"""
    return "".join(content.split())

def get_note_problems(session):
    """通过GraphQL接口获取笔记列表"""
    print("\n📋 正在通过GraphQL API爬取笔记题目列表...")
    
    # 尝试不同类型的笔记
    note_types = ["QUESTION_NOTE", "LEETBOOK_NOTE", "ALL"]
    all_problems = []
    
    for note_type in note_types:
        print(f"\n🔍 尝试获取类型: {note_type}")
        try:
            skip = 0
            limit = 100  # 每次获取100条
            type_notes = []
            
            while True:
                print(f"   请求中（已获取: {skip}）...")
                
                # 构造请求头（模拟浏览器）
                headers = {
                    "Content-Type": "application/json",
                    "X-CSRFToken": MANUAL_COOKIES["csrftoken"],
                    "Referer": "https://leetcode.cn/notes/my-notes/",
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
                    "Cookie": f"csrftoken={MANUAL_COOKIES['csrftoken']}; sl-session={MANUAL_COOKIES['slsession']}; LEETCODE_SESSION={MANUAL_COOKIES['session']}"
                }
                
                # 构造GraphQL请求体
                payload = {
                    "operationName": "noteAggregateNote",
                    "query": NOTES_LIST_QUERY.strip(),
                    "variables": {
                        "aggregateType": note_type,
                        "limit": limit,
                        "skip": skip,
                        "orderBy": "DESCENDING"
                    }
                }
                
                # 发送请求
                response = session.post(
                    GRAPHQL_API,
                    json=payload,
                    headers=headers,
                    timeout=15
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    print(f"   ❌ 请求失败，状态码：{response.status_code}")
                    break
                
                # 解析JSON响应
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    print("   ❌ 响应不是JSON格式")
                    break
                
                # 处理GraphQL错误
                if "errors" in data:
                    print(f"   ❌ GraphQL错误：{data['errors'][0]['message'][:100] if data['errors'] else 'Unknown'}")
                    break
                
                # 提取笔记列表
                note_data = data.get("data", {}).get("noteAggregateNote", {})
                notes = note_data.get("userNotes", [])
                total = note_data.get("count", 0)
                
                print(f"   📈 当前类型共 {total} 条笔记")
                
                if not notes:
                    break
                
                type_notes.extend(notes)
                print(f"   累计获取 {len(type_notes)}/{total} 条")
                
                # 判断是否继续分页
                if len(type_notes) >= total:
                    break
                skip = len(type_notes)  # 使用已获取的数量作为下一次的skip
                time.sleep(REQUEST_DELAY)
            
            # 提取有效题目信息
            for note in type_notes:
                # 处理题目笔记
                if note.get("__typename") == "NoteAggregateQuestionNoteNode":
                    question = note.get("noteQuestion", {})
                    if not question:
                        continue
                    
                    # 提取核心字段
                    problem_id = question.get("questionFrontendId")
                    problem_title = question.get("translatedTitle") or question.get("title")
                    # 从 linkTemplate 提取 slug，例如: "/problems/two-sum/"
                    link_template = question.get("linkTemplate", "")
                    problem_slug = link_template.strip("/").split("/")[-1] if link_template else ""
                    
                    # 笔记ID和内容
                    note_id = note.get("id")
                    note_content = note.get("content", "")
                    
                    if not (problem_id and problem_title and problem_slug and note_id):
                        print(f"   ⚠️ 跳过信息不完整的笔记")
                        continue
                    
                    all_problems.append({
                        "id": str(problem_id),
                        "title": problem_title,
                        "slug": problem_slug,
                        "note_id": str(note_id),
                        "content": note_content
                    })
                    print(f"   📌 已识别：{problem_id}. {problem_title}")
        
        except Exception as e:
            print(f"   ❌ 获取{note_type}类型笔记失败：{str(e)[:100]}")
            continue
    
    print(f"\n✅ 共爬取到 {len(all_problems)} 个有效笔记题目")
    return all_problems

def get_note_content(session, note_id):
    """通过GraphQL接口获取单条笔记内容"""
    try:
        print(f"🔍 正在获取笔记{note_id}内容...")
        
        headers = {
            "Content-Type": "application/json",
            "X-CSRFToken": MANUAL_COOKIES["csrftoken"],
            "Referer": f"https://leetcode.cn/notes/{note_id}/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/119.0.0.0 Safari/537.36",
            "Cookie": f"csrftoken={MANUAL_COOKIES['csrftoken']}; slsession={MANUAL_COOKIES['slsession']}"
        }
        
        # 构造请求体
        payload = {
            "query": NOTE_CONTENT_QUERY.strip(),
            "variables": {"uuid": note_id}
        }
        
        # 发送请求
        response = session.post(
            GRAPHQL_API,
            json=payload,
            headers=headers,
            timeout=15
        )
        response.raise_for_status()
        data = response.json()
        
        # 处理GraphQL错误
        if "errors" in data:
            print(f"⚠️ 笔记内容请求错误：{data['errors']}")
            return ""
        
        # 提取笔记内容（与响应字段对应）
        content = data.get("data", {}).get("note", {}).get("content", "").strip()
        return content
    
    except Exception as e:
        print(f"⚠️ 获取笔记{note_id}内容失败：{str(e)[:100]}")
        return ""

def crawl_leetcode_notes():
    # 验证隐私配置
    if not OBSIDIAN_NOTES_PATH:
        print("❌ 未读取到Obsidian路径，请在.env文件中添加：")
        print("   OBSIDIAN_PATH='你的笔记路径'")
        return
    
    if not (MANUAL_COOKIES["csrftoken"] and MANUAL_COOKIES["slsession"]):
        print("❌ 未读取到Cookie，请在.env文件中添加：")
        print("   LEETCODE_CSRFTOKEN='你的csrftoken'")
        print("   LEETCODE_SLSSESSION='你的slsession'")
        return
    
    # 🔐 验证 Cookie 有效性（新增）
    print("\n🔐 开始验证 Cookie 有效性...")
    validator = CookieValidator()
    validation_result = validator.validate(verbose=False)
    
    if not validation_result["valid"]:
        print("\n" + "=" * 60)
        print(validation_result["message"])
        print("=" * 60)
        print("\n🔧 如何更新 Cookie：")
        print("   1. 打开浏览器无痕模式")
        print("   2. 访问 https://leetcode.cn/notes/my-notes/")
        print("   3. 登录你的账号")
        print("   4. 按 F12 打开开发者工具，切换到 Network 标签")
        print("   5. 刷新页面，找到 graphql 请求")
        print("   6. 复制 Request Headers 中的 Cookie 字段")
        print("   7. 更新 .env 文件中的对应值\n")
        print("📖 详细步骤请参考《抓包指南.md》\n")
        return
    
    print(f"✅ Cookie 验证通过！当前用户: {validation_result['user_info']['username']}")
    
    # 检查笔记访问权限
    notes_check = validator.check_notes_access(verbose=False)
    if not notes_check["accessible"]:
        print(f"\n❌ {notes_check['message']}")
        print("请确认 Cookie 对应的账号有访问权限\n")
        return
    
    if notes_check['notes_count'] == 0:
        print(f"⚠️ {notes_check['message']}")
        print("如果你的账号有笔记但这里显示0条，请检查 Cookie 是否对应正确的账号\n")
    else:
        print(f"✅ 笔记访问正常，检测到 {notes_check['notes_count']} 条笔记\n")
    
    # 验证并创建笔记目录
    if not os.path.exists(OBSIDIAN_NOTES_PATH):
        try:
            os.makedirs(OBSIDIAN_NOTES_PATH)
            print(f"✅ 创建笔记文件夹：{OBSIDIAN_NOTES_PATH}")
        except Exception as e:
            print(f"❌ 无法创建笔记文件夹：{e}")
            return
    
    # 初始化会话
    session = requests.Session()
    print("✅ 隐私配置加载完成，开始爬取...")

    # 获取笔记列表
    problems = get_note_problems(session)
    if not problems:
        print("❌ 未找到任何笔记，程序退出")
        return

    # 同步笔记内容到Obsidian
    for i, problem in enumerate(problems):
        problem_id = problem["id"]
        problem_title = problem["title"]
        problem_slug = problem["slug"]
        note_id = problem["note_id"]
        markdown_text = problem.get("content", "")  # 内容已经在列表中返回
        
        print(f"\n📝 处理第 {i+1}/{len(problems)} 个：{problem_id}. {problem_title}")

        # 控制请求频率，避免反爬（虽然不再需要请求，但保留以防万一）
        if i > 0 and i % 10 == 0:
            time.sleep(1)

        # 检查笔记内容
        if not markdown_text:
            print(f"❌ 跳过：未获取到笔记内容")
            continue

        # 构建Markdown内容（带元数据）
        metadata = f"""---
id: {problem_id}
title: {problem_title}
source: https://leetcode.cn/problems/{problem_slug}/
tags: [LeetCode, 算法]
---

"""
        new_content = metadata
        new_content += f"# {problem_id}. {problem_title}\n\n"
        new_content += f"## 题目链接\n[{problem_title}](https://leetcode.cn/problems/{problem_slug}/)\n\n"
        new_content += f"## 解题笔记\n{markdown_text}\n"

        # 保存/更新文件
        filename = f"{problem_id}. {problem_title}.md"
        filepath = os.path.join(OBSIDIAN_NOTES_PATH, filename)

        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                old_content = f.read()
            if clean_content(new_content) == clean_content(old_content):
                print(f"✅ 无更新，跳过")
                continue
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ 已更新")
        else:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"✅ 已创建")

    print("\n🎉 所有笔记同步完成！")

if __name__ == "__main__":
    crawl_leetcode_notes()