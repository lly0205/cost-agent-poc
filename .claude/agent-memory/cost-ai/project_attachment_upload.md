---
name: project-attachment-upload
description: 附件上传目录约定——每次上传在 .cc-connect/attachments/yyyyMMdd_HHmmss/ 下创建新目录，由 AttachmentUploadSkill 统一管理
metadata:
  type: project
---

每次用户上传文件时，统一由 `skills/attachment_upload_skill.py` 中的 `AttachmentUploadSkill` 创建目标目录：

- 基础路径：`<PROJECT_ROOT>/.cc-connect/attachments/`
- 目录格式：`yyyyMMdd_HHmmss`（例：`20260604_143022`）
- 每次上传必须新建目录，禁止复用旧目录
- 同一秒内多次上传：自动追加序号后缀 `_1`/`_2`... 保证唯一

**Why:** 用户明确要求每次上传的文件必须隔离，避免不同批次文件混用导致上下文混乱。

**How to apply:** 任何需要接收附件的功能必须调用 `AttachmentUploadSkill.receive_files()` 或 `receive_bytes()`，不得手动拼接路径或写入 attachments 根目录。

See also: [[project-skill-rules-2026-06-03]]
