---
name: project-overview
description: cost-agent-poc 项目整体定位：面向中国造价师的 AI Agent PoC，基于 Claude API 辅助完成工程量计算等造价任务
metadata:
  type: project
---

这是一个面向中国建设工程造价师的 AI Agent 概念验证（PoC）项目，项目名称为 cost-agent-poc。

**核心定位**：AI 辅助工具，输出仅作为造价初稿，最终成果必须由注册造价工程师人工复核。

**Why:** 中国造价师日常工作（算量、清单复核、变更签证等）重复性高、依赖专业知识，AI 可提升效率但不能取代专业判断，合规性要求严格。

**How to apply:** 所有功能建议和改进都必须保留"AI 初稿 + 人工复核"的双重机制，不得设计绕过人工确认的流程。

技术栈：Python 3.11+（实为 3.14，见 __pycache__）、Anthropic Claude API (claude-sonnet-4-6)、openpyxl、pypdf、PyYAML、pandas。

六大核心任务类型：
- drawing_review（图纸审阅）
- quantity_takeoff（工程量初算）
- boq_check（清单复核）
- variation_claim（变更签证整理）
- glodon_integration（广联达集成，占位）
- evaluation（AI结果评测）

当前状态：PoC 阶段，核心 Agent 框架和所有 Skill 均已实现；广联达集成、企业微信/Slack 接入为占位预留；案例数据（sample_case_001）为模板，未填写真实项目数据。
