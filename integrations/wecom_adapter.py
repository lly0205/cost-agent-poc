"""
企业微信（WeCom）集成适配器 — 预留占位

功能：接收企业微信消息 → 转换为 AgentTask → 调用 Orchestrator → 回复结果

TODO:
- [ ] 在企业微信管理后台创建自建应用，获取 CorpID / AgentID / Secret
- [ ] 实现消息接收（企业微信使用 callback URL + 加密验证）
- [ ] 将企业微信消息解析为 TaskContext
- [ ] 将 Orchestrator 结果格式化为企业微信消息（支持 Markdown / 卡片）
- [ ] 支持接收图片/文件附件
"""
import os
from typing import Optional


class WeComAdapter:
    """
    企业微信 Bot 适配器。
    入口：receive_message(xml_data) → orchestrator.run(context) → send_reply()
    """

    def __init__(self):
        self.corp_id = os.environ.get("WECOM_CORP_ID")
        self.agent_id = os.environ.get("WECOM_AGENT_ID")
        self.secret = os.environ.get("WECOM_SECRET")
        self.token = os.environ.get("WECOM_TOKEN")
        self.encoding_aes_key = os.environ.get("WECOM_ENCODING_AES_KEY")

    def verify_callback(self, msg_signature: str, timestamp: str, nonce: str, echostr: str) -> str:
        """
        验证企业微信 callback URL（GET 请求验证）。
        TODO: 实现签名验证逻辑。
        """
        raise NotImplementedError("企业微信 callback 验证尚未实现。")

    def receive_message(self, xml_data: str, msg_signature: str, timestamp: str, nonce: str) -> Optional[dict]:
        """
        接收并解密企业微信消息（POST 请求）。
        TODO: 使用 wxcrypt 或 wechatpy 实现解密。
        """
        raise NotImplementedError(
            "企业微信消息接收尚未实现。\n"
            "参考：企业微信开发文档 - 接收消息与事件"
        )

    def parse_task_from_message(self, msg: dict) -> dict:
        """
        将企业微信消息解析为任务参数。
        支持消息类型：text（文字指令）、file（上传图纸/清单）

        TODO: 实现消息解析，调用 task_classifier.classify_task()
        """
        raise NotImplementedError("企业微信消息任务解析尚未实现。")

    def send_text_message(self, to_user: str, content: str):
        """
        发送文本消息给指定用户。
        TODO: 调用企业微信消息发送 API。
        """
        raise NotImplementedError("企业微信文本消息发送尚未实现。")

    def send_markdown_message(self, to_user: str, content: str):
        """
        发送 Markdown 格式消息（在企业微信中展示为富文本）。
        TODO: 调用企业微信 Markdown 消息 API。
        """
        raise NotImplementedError("企业微信 Markdown 消息发送尚未实现。")

    def send_file(self, to_user: str, file_path: str):
        """
        发送文件（如 AI 输出报告 PDF）。
        TODO: 先上传文件获取 media_id，再发送文件消息。
        """
        raise NotImplementedError("企业微信文件发送尚未实现。")

    def start_server(self, host: str = "0.0.0.0", port: int = 5000):
        """
        启动 HTTP 服务器，接收企业微信 callback。
        TODO: 使用 Flask 或 FastAPI 实现。
        """
        raise NotImplementedError(
            "企业微信服务器尚未实现。\n"
            "参考：企业微信开发文档 - 企业内部开发 - 接收消息与事件"
        )
