#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模块 - 支持多种提醒方式
"""

import os
import sys
import subprocess
from datetime import datetime


class Notifier:
    """通知发送器"""
    
    def __init__(self):
        self.platform = sys.platform
    
    def send_notification(self, title, message, urgency="normal"):
        """
        发送系统通知
        
        Args:
            title: 通知标题
            message: 通知内容
            urgency: 紧急程度 (low/normal/critical)
        """
        if self.platform == "darwin":  # macOS
            self._send_macos_notification(title, message)
        elif self.platform.startswith("linux"):  # Linux
            self._send_linux_notification(title, message, urgency)
        elif self.platform == "win32":  # Windows
            self._send_windows_notification(title, message)
        else:
            print(f"⚠️ 不支持的平台: {self.platform}，使用控制台输出")
            print(f"📢 {title}")
            print(f"   {message}")
    
    def _send_macos_notification(self, title, message):
        """发送 macOS 系统通知"""
        try:
            # 使用 osascript 发送通知
            script = f'''
            display notification "{message}" with title "{title}" sound name "default"
            '''
            subprocess.run(
                ["osascript", "-e", script],
                check=True,
                capture_output=True
            )
            print(f"✅ 系统通知已发送: {title}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 发送 macOS 通知失败: {e}")
        except FileNotFoundError:
            print("⚠️ osascript 未找到，无法发送通知")
    
    def _send_linux_notification(self, title, message, urgency="normal"):
        """发送 Linux 系统通知（使用 notify-send）"""
        try:
            subprocess.run(
                ["notify-send", "-u", urgency, title, message],
                check=True,
                capture_output=True
            )
            print(f"✅ 系统通知已发送: {title}")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ 发送 Linux 通知失败: {e}")
        except FileNotFoundError:
            print("⚠️ notify-send 未安装，请安装 libnotify")
    
    def _send_windows_notification(self, title, message):
        """发送 Windows 系统通知（使用 PowerShell）"""
        try:
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $toastXml = [xml] $template.GetXml()
            $toastXml.GetElementsByTagName("text")[0].AppendChild($toastXml.CreateTextNode("{title}")) | Out-Null
            $toastXml.GetElementsByTagName("text")[1].AppendChild($toastXml.CreateTextNode("{message}")) | Out-Null
            $xml = New-Object Windows.Data.Xml.Dom.XmlDocument
            $xml.LoadXml($toastXml.OuterXml)
            $toast = [Windows.UI.Notifications.ToastNotification]::new($xml)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("LeetCode同步").Show($toast)
            '''
            subprocess.run(
                ["powershell", "-Command", ps_script],
                check=True,
                capture_output=True
            )
            print(f"✅ 系统通知已发送: {title}")
        except Exception as e:
            print(f"⚠️ 发送 Windows 通知失败: {e}")
    
    def notify_cookie_expired(self):
        """Cookie 过期专用通知"""
        title = "⚠️ LeetCode Cookie 已过期"
        message = "请打开浏览器更新 Cookie 配置，详见终端提示"
        self.send_notification(title, message, urgency="critical")
    
    def notify_sync_failed(self, reason):
        """同步失败通知"""
        title = "❌ LeetCode 笔记同步失败"
        message = f"失败原因: {reason}"
        self.send_notification(title, message, urgency="normal")
    
    def notify_sync_success(self, count):
        """同步成功通知"""
        title = "✅ LeetCode 笔记同步成功"
        message = f"已同步 {count} 条笔记"
        self.send_notification(title, message, urgency="low")
    
    def create_reminder_file(self, message):
        """在桌面创建提醒文件"""
        try:
            desktop = os.path.expanduser("~/Desktop")
            filename = f"LeetCode_Cookie_过期提醒_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            filepath = os.path.join(desktop, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=" * 60 + "\n")
                f.write("⚠️ LeetCode Cookie 过期提醒\n")
                f.write("=" * 60 + "\n\n")
                f.write(f"提醒时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                f.write(message + "\n\n")
                f.write("如何更新 Cookie：\n")
                f.write("1. 打开浏览器无痕模式\n")
                f.write("2. 访问 https://leetcode.cn/notes/my-notes/\n")
                f.write("3. 登录你的账号\n")
                f.write("4. 按 F12 打开开发者工具\n")
                f.write("5. 切换到 Network 标签\n")
                f.write("6. 刷新页面，找到 graphql 请求\n")
                f.write("7. 复制 Request Headers 中的 Cookie\n")
                f.write("8. 更新 .env 文件中的对应值\n\n")
                f.write("详细步骤请参考《抓包指南.md》\n")
                f.write("=" * 60 + "\n")
            
            print(f"📄 提醒文件已创建: {filepath}")
            
            # 尝试打开文件
            if self.platform == "darwin":
                subprocess.run(["open", filepath])
            elif self.platform.startswith("linux"):
                subprocess.run(["xdg-open", filepath])
            elif self.platform == "win32":
                subprocess.run(["notepad", filepath])
                
        except Exception as e:
            print(f"⚠️ 创建提醒文件失败: {e}")


def test_notification():
    """测试通知功能"""
    notifier = Notifier()
    
    print("📢 测试系统通知...")
    notifier.send_notification(
        "测试通知",
        "这是一条测试消息，如果你看到了，说明通知功能正常！",
        urgency="normal"
    )
    
    print("\n📢 测试 Cookie 过期通知...")
    notifier.notify_cookie_expired()
    
    print("\n📄 测试桌面提醒文件...")
    notifier.create_reminder_file("这是一条测试提醒消息")


if __name__ == "__main__":
    test_notification()
