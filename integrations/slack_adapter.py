"""
Slack 集成适配器 — 预留占位

功能：接收 Slack 消息 → 转换为 AgentTask → 调用 Orchestrator → 回复结果

TODO:
- [ ] 安装 Slack SDK: pip install slack-sdk
- [ ] 在 Slack 创建 Bot App，获取 Bot Token 和 Signing Secret
- [ ] 实现 webhook 或 Socket Mode 监听
- [ ] 将 Slack 消息解析为 TaskContext
- [ ] 将 Orchestrator 结果格式化为 Slack Block Kit 消息
"""
import os
from typing import Optional


class SlackAdapter:
    """
    Slack Bot 适配器。
    入口：receive_message(event) → orchestrator.run(context) → send_reply()
    """

    def __init__(self):
        self.bot_token = os.environ.get("SLACK_BOT_TOKEN")
        self.signing_secret = os.environ.get("SLACK_SIGNING_SECRET")

    def receive_message(self, event: dict) -> Optional[dict]:
        """
        接收来自 Slack 的消息事件，解析为 TaskContext 参数。
        TODO: 实现消息解析逻辑。
        """
        raise NotImplementedError(
            "Slack 消息接收尚未实现。请配置 SLACK_BOT_TOKEN 和 SLACK_SIGNING_SECRET 环境变量。"
        )

    def parse_task_from_message(self, text: str, files: list) -> dict:
        """
        将 Slack 消息文本和附件解析为任务参数。
        示例消息格式：
          "@造价AI 图纸审阅 [附件：图纸.pdf]"
          "@造价AI 工程量初算 案例编号：proj_001"

        TODO: 实现消息解析，调用 task_classifier.classify_task()
        """
        raise NotImplementedError("Slack 消息任务解析尚未实现。")

    def send_reply(self, channel: str, thread_ts: str, result: dict):
        """
        将 Orchestrator 结果格式化并回复到 Slack。
        TODO: 使用 Block Kit 格式化消息，附上结果文件。
        """
        raise NotImplementedError("Slack 消息回复尚未实现。")

    def start_listener(self, port: int = 3000):
        """
        启动 Slack 事件监听服务（Socket Mode 或 HTTP Webhook）。
        TODO: 使用 slack-sdk 实现。
        """
        raise NotImplementedError(
            "Slack 监听服务尚未实现。\n"
            "参考：https://slack.dev/python-slack-sdk/socket-mode/"
        )
