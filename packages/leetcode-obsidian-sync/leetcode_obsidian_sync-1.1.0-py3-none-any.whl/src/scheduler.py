#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LeetCode 笔记定时同步调度器
使用 schedule 库实现跨平台的定时任务
"""

import os
import sys
import time
import schedule
import subprocess
import logging
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cookie_validator import CookieValidator

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def sync_notes():
    """执行笔记同步任务"""
    logger.info("=" * 60)
    logger.info("🚀 开始执行 LeetCode 笔记同步任务...")
    logger.info("=" * 60)
    
    # 🔐 先验证 Cookie 有效性
    logger.info("🔐 验证 Cookie 有效性...")
    try:
        validator = CookieValidator()
        validation = validator.validate(verbose=False)
        
        if not validation["valid"]:
            logger.error("❌ Cookie 验证失败: %s", validation["message"])
            logger.error("🔧 请更新 .env 文件中的 Cookie 配置")
            logger.error("📖 详细步骤请参考《抓包指南.md》")
            logger.info("=" * 60)
            return
        
        logger.info("✅ Cookie 有效，当前用户: %s", validation["user_info"]["username"])
        
    except Exception as e:
        logger.error("❌ Cookie 验证异常: %s", str(e))
        logger.info("=" * 60)
        return
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    crawler_script = os.path.join(script_dir, 'src', 'leetcode_notes_crawler.py')
    
    try:
        # 执行爬虫脚本
        result = subprocess.run(
            ['python3', crawler_script],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5分钟超时
        )
        
        # 记录输出
        if result.stdout:
            logger.info("📝 同步输出:\n%s", result.stdout)
        
        if result.stderr:
            logger.warning("⚠️ 警告信息:\n%s", result.stderr)
        
        # 检查执行结果
        if result.returncode == 0:
            logger.info("✅ 笔记同步成功完成！")
        else:
            logger.error("❌ 笔记同步失败，退出码: %d", result.returncode)
            
    except subprocess.TimeoutExpired:
        logger.error("❌ 同步任务超时（超过5分钟）")
    except FileNotFoundError:
        logger.error("❌ 找不到爬虫脚本: %s", crawler_script)
    except Exception as e:
        logger.error("❌ 执行出错: %s", str(e), exc_info=True)
    
    logger.info("=" * 60)
    logger.info("下次同步时间: 明天 09:00")
    logger.info("=" * 60)
    logger.info("")


def main():
    """主函数"""
    logger.info("🎯 LeetCode 笔记定时同步调度器启动")
    logger.info("⏰ 同步时间: 每天 09:00")
    logger.info("📋 日志文件: scheduler.log")
    logger.info("")
    
    # 设置定时任务 - 每天9点执行
    schedule.every().day.at("09:00").do(sync_notes)
    
    # 可选：也可以设置其他时间，比如每天下午6点也同步一次
    # schedule.every().day.at("18:00").do(sync_notes)
    
    # 可选：立即执行一次测试
    # logger.info("🧪 执行首次测试同步...")
    # sync_notes()
    
    logger.info("✅ 调度器运行中，等待定时任务...")
    logger.info("💡 提示: 按 Ctrl+C 停止调度器")
    logger.info("")
    
    # 持续运行
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("\n👋 调度器已停止")


if __name__ == "__main__":
    main()
