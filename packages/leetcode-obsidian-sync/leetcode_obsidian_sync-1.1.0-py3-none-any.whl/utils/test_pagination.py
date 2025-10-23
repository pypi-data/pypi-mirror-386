#!/usr/bin/env python3
"""测试分页逻辑"""

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

GRAPHQL_API = "https://leetcode.cn/graphql/"

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

session = requests.Session()

skip = 0
limit = 10  # 先测试小批量

print("🔍 测试分页获取笔记...\n")

for page in range(3):
    print(f"第 {page+1} 次请求:")
    print(f"  参数: skip={skip}, limit={limit}")
    
    headers = {
        "Content-Type": "application/json",
        "X-CSRFToken": COOKIES["csrftoken"],
        "Referer": "https://leetcode.cn/notes/my-notes/",
        "User-Agent": "Mozilla/5.0",
        "Cookie": f"csrftoken={COOKIES['csrftoken']}; sl-session={COOKIES['slsession']}; LEETCODE_SESSION={COOKIES['session']}"
    }
    
    payload = {
        "operationName": "noteAggregateNote",
        "query": NOTES_LIST_QUERY.strip(),
        "variables": {
            "aggregateType": "QUESTION_NOTE",
            "limit": limit,
            "skip": skip,
            "orderBy": "DESCENDING"
        }
    }
    
    response = session.post(GRAPHQL_API, json=payload, headers=headers, timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        note_data = data.get("data", {}).get("noteAggregateNote", {})
        notes = note_data.get("userNotes", [])
        total = note_data.get("count", 0)
        
        print(f"  总数: {total}")
        print(f"  本次返回: {len(notes)} 条")
        
        if notes:
            print(f"  笔记ID列表:")
            for note in notes:
                q = note.get("noteQuestion", {})
                print(f"    - {note.get('id')}: {q.get('questionFrontendId')}. {q.get('translatedTitle')}")
        
        if len(notes) == 0:
            print("  ✅ 没有更多笔记了")
            break
    else:
        print(f"  ❌ 请求失败: {response.status_code}")
        break
    
    skip += limit
    print()
