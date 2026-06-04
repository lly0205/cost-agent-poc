"""
附件上传管理 Skill

职责：
  每次文件上传时，在 .cc-connect/attachments/ 下创建以当前时间戳命名的临时文件夹，
  将本次上传的所有文件统一归入该文件夹，每次上传必须生成全新的文件夹。

文件夹命名规则：yyyyMMdd_HHmmss（例：20260604_143022）
基础路径：<PROJECT_ROOT>/.cc-connect/attachments/

使用方式：
  skill = AttachmentUploadSkill()
  upload_dir = skill.create_upload_dir()                  # 仅建目录
  results = skill.receive_files(file_paths)               # 传入源文件路径列表
  results = skill.receive_bytes({"filename.pdf": b"..."}) # 传入字节内容
"""

from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from agent.context import PROJECT_ROOT

# 附件根目录，固定路径
ATTACHMENTS_ROOT: Path = PROJECT_ROOT / ".cc-connect" / "attachments"

# 时间戳格式
TIMESTAMP_FORMAT: str = "%Y%m%d_%H%M%S"


class AttachmentUploadSkill:
    """附件上传管理：为每次上传创建独立的时间戳目录并接收文件。"""

    @property
    def task_type(self) -> str:
        return "attachment_upload"

    # ------------------------------------------------------------------ #
    # 核心：目录管理                                                        #
    # ------------------------------------------------------------------ #

    def create_upload_dir(self, timestamp: Optional[datetime] = None) -> Path:
        """
        在 ATTACHMENTS_ROOT 下创建本次上传专用的临时文件夹。

        参数：
            timestamp: 可选；不传则自动取当前时间。
                       测试时可传入固定时间以保证可重复性。

        返回：
            已创建的目录 Path，格式为 .../attachments/yyyyMMdd_HHmmss/

        规则：
            - 每次调用必须生成全新文件夹（哪怕同一秒内多次调用，
              会在末位追加序号 _1 / _2 … 保证唯一）
            - 目录不存在时自动递归创建
        """
        ts = timestamp or datetime.now()
        folder_name = ts.strftime(TIMESTAMP_FORMAT)
        upload_dir = ATTACHMENTS_ROOT / folder_name

        # 同一秒内多次上传：追加自增序号保证唯一
        if upload_dir.exists():
            counter = 1
            while True:
                candidate = ATTACHMENTS_ROOT / f"{folder_name}_{counter}"
                if not candidate.exists():
                    upload_dir = candidate
                    break
                counter += 1

        upload_dir.mkdir(parents=True, exist_ok=False)
        return upload_dir

    # ------------------------------------------------------------------ #
    # 接收文件：来自本地路径                                                 #
    # ------------------------------------------------------------------ #

    def receive_files(
        self,
        source_paths: list[str | Path],
        *,
        move: bool = False,
        timestamp: Optional[datetime] = None,
    ) -> dict:
        """
        将一批本地文件复制（或移动）到新建的上传目录。

        参数：
            source_paths: 源文件路径列表（字符串或 Path 均可）
            move:         True=移动，False=复制（默认复制）
            timestamp:    可选；不传则取当前时间

        返回：
            {
              "upload_dir": str,          # 生成的上传目录绝对路径
              "timestamp": str,           # yyyyMMdd_HHmmss
              "files": [                  # 每个文件的结果
                {"source": str, "dest": str, "status": "ok" | "error", "error": str},
                ...
              ],
              "success_count": int,
              "error_count": int,
            }
        """
        upload_dir = self.create_upload_dir(timestamp)
        results = []

        for src in source_paths:
            src_path = Path(src)
            dest_path = upload_dir / src_path.name
            try:
                if move:
                    shutil.move(str(src_path), dest_path)
                else:
                    shutil.copy2(src_path, dest_path)
                results.append({"source": str(src_path), "dest": str(dest_path), "status": "ok"})
            except Exception as exc:
                results.append(
                    {"source": str(src_path), "dest": str(dest_path), "status": "error", "error": str(exc)}
                )

        success_count = sum(1 for r in results if r["status"] == "ok")
        return {
            "upload_dir": str(upload_dir),
            "timestamp": upload_dir.name,
            "files": results,
            "success_count": success_count,
            "error_count": len(results) - success_count,
        }

    # ------------------------------------------------------------------ #
    # 接收文件：来自内存字节流（适用于 API / 消息附件场景）                    #
    # ------------------------------------------------------------------ #

    def receive_bytes(
        self,
        file_map: dict[str, bytes],
        *,
        timestamp: Optional[datetime] = None,
    ) -> dict:
        """
        将字节内容直接写入新建的上传目录。

        参数：
            file_map:  {文件名: 字节内容} 字典
            timestamp: 可选；不传则取当前时间

        返回：与 receive_files() 格式相同
        """
        upload_dir = self.create_upload_dir(timestamp)
        results = []

        for filename, content in file_map.items():
            dest_path = upload_dir / filename
            try:
                dest_path.write_bytes(content)
                results.append({"source": f"<bytes:{filename}>", "dest": str(dest_path), "status": "ok"})
            except Exception as exc:
                results.append(
                    {"source": f"<bytes:{filename}>", "dest": str(dest_path), "status": "error", "error": str(exc)}
                )

        success_count = sum(1 for r in results if r["status"] == "ok")
        return {
            "upload_dir": str(upload_dir),
            "timestamp": upload_dir.name,
            "files": results,
            "success_count": success_count,
            "error_count": len(results) - success_count,
        }

    # ------------------------------------------------------------------ #
    # 工具方法                                                              #
    # ------------------------------------------------------------------ #

    def list_uploads(self) -> list[dict]:
        """
        列出所有已存在的上传目录，按时间戳升序排列。

        返回：
            [{"timestamp": str, "path": str, "file_count": int}, ...]
        """
        if not ATTACHMENTS_ROOT.exists():
            return []

        entries = []
        for d in sorted(ATTACHMENTS_ROOT.iterdir()):
            if d.is_dir():
                file_count = sum(1 for f in d.iterdir() if f.is_file())
                entries.append({"timestamp": d.name, "path": str(d), "file_count": file_count})
        return entries

    def get_latest_upload_dir(self) -> Optional[Path]:
        """返回最新一次上传的目录 Path，若尚无任何上传则返回 None。"""
        uploads = self.list_uploads()
        if not uploads:
            return None
        return Path(uploads[-1]["path"])
