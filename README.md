# Cost Engineer AI Agent — PoC

> 面向中国造价师日常工作的本地 AI Agent 框架。
> **当前阶段：Phase 0 / Phase 1 骨架，持续迭代中。**

---

## 项目目标

帮助造价师提升以下工作的效率：
- 图纸审阅与问题梳理
- 工程量初算（装修、土建、安装）
- 工程量清单复核
- 变更单/签证资料整理
- 广联达操作辅助（预留）

**重要原则：AI 输出只作为初稿，不替代造价师专业判断，所有成果必须经人工复核。**

---

## 目录结构

```
cost-agent-poc/
├── run_agent.py                    # CLI 入口
├── requirements.txt
│
├── agent/
│   ├── orchestrator.py             # 主编排器（入口无关）
│   ├── task_classifier.py          # 任务分类
│   └── context.py                  # 任务上下文
│
├── skills/                         # 造价任务 Skill
│   ├── base_skill.py               # 基类
│   ├── drawing_review_skill.py     # 图纸审阅
│   ├── quantity_takeoff_skill.py   # 工程量初算
│   ├── boq_check_skill.py          # 工程量清单复核
│   ├── variation_claim_skill.py    # 变更单/签证整理
│   ├── glodon_integration_skill.py # 广联达集成
│   └── evaluation_skill.py         # AI 结果评测
│
├── guidance/                       # 算量指导文档（造价师补充）
│   ├── general_principles.md
│   ├── decoration_quantity.md
│   ├── door_window_quantity.md
│   ├── drawing_boq_consistency.md
│   ├── uncertainty_handling.md
│   └── human_review_rules.md
│
├── knowledge/                      # 知识库
│   ├── china_cost_engineering_tasks.md
│   ├── company_rules/              # 公司算量规则（待补充）
│   ├── project_rules/              # 项目级规则（待补充）
│   └── standards/                  # 行业标准摘要（待补充）
│
├── cases/
│   └── sample_case_001/
│       ├── case_meta.yaml
│       ├── input/                  # 图纸、清单、说明
│       ├── golden_answer/          # 人工标准答案
│       ├── ai_output/              # AI 输出存档
│       ├── evaluation/             # 评测结果
│       └── lessons_learned.md
│
├── evaluation/
│   ├── evaluate_case.py            # 评测主脚本
│   ├── metrics.py                  # 8 项评测指标
│   └── sample_data/                # 示例数据
│
├── integrations/
│   ├── glodon_adapter.py           # 广联达（三种路径预留）
│   ├── slack_adapter.py            # Slack（预留）
│   └── wecom_adapter.py            # 企业微信（预留）
│
├── file_io/
│   ├── readers.py                  # PDF/Excel/CSV/MD/JSON 读取
│   └── writers.py                  # 输出写入
│
└── outputs/                        # 所有运行结果
    └── sample_case_001/
```

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 设置 API Key

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY = "sk-ant-..."

# 或写入 .env（不要提交到 Git）
```

### 3. 运行 Demo（存根模式，无需 API Key）

```bash
# 查看可用任务
python run_agent.py --list-tasks

# 查看可用案例
python run_agent.py --list-cases

# 存根模式运行（不调用 AI，验证流程）
python run_agent.py --task quantity_takeoff --case sample_case_001

# Dry Run（只预览 prompt，不调用 AI）
python run_agent.py --task drawing_review --case sample_case_001 --dry-run
```

### 4. 真实 AI 运行（需要 ANTHROPIC_API_KEY）

将图纸 PDF 和清单 Excel 放入 `cases/sample_case_001/input/`，然后：

```bash
python run_agent.py --task drawing_review  --case sample_case_001
python run_agent.py --task quantity_takeoff --case sample_case_001
python run_agent.py --task boq_check        --case sample_case_001
python run_agent.py --task variation_claim  --case sample_case_001
```

### 5. 运行评测

先填写 `cases/sample_case_001/golden_answer/human_answer.json`，然后：

```bash
python evaluation/evaluate_case.py --case sample_case_001
```

---

## 如何添加新的 Skill

1. 在 `skills/` 下新建 `my_new_skill.py`，继承 `BaseSkill`：

```python
from skills.base_skill import BaseSkill
from agent.context import TaskContext

class MyNewSkill(BaseSkill):
    @property
    def task_type(self) -> str:
        return "my_new_task"

    @property
    def guidance_files(self) -> list[str]:
        return ["general_principles"]  # 相关 guidance 文件名

    def build_prompt(self, context: TaskContext) -> str:
        return f"""# 任务：...
{self._guidance_section(context)}
## 输入材料
{self._format_input_section(context)}
## 任务要求
...
## 输出格式（JSON）
```json
{{ ... }}
```
"""
```

2. 在 `skills/__init__.py` 中注册：

```python
from skills.my_new_skill import MyNewSkill
SKILL_REGISTRY["my_new_task"] = MyNewSkill()
```

3. 在 `run_agent.py` 的 `VALID_TASKS` 中添加新任务名。

4. 在 `agent/task_classifier.py` 中添加关键词映射。

---

## 如何添加新的 Case

1. 在 `cases/` 下创建新目录：

```bash
mkdir -p cases/proj_001/input/drawings
mkdir -p cases/proj_001/input/boq
mkdir -p cases/proj_001/input/cad
mkdir -p cases/proj_001/golden_answer
mkdir -p cases/proj_001/ai_output
mkdir -p cases/proj_001/evaluation
```

2. 复制 `cases/sample_case_001/case_meta.yaml` 并修改项目信息。

3. 复制 `cases/sample_case_001/input/project_instructions.md` 并填写项目说明。

4. 将图纸放入 `input/drawings/`，清单放入 `input/boq/`。

5. 运行：`python run_agent.py --task quantity_takeoff --case proj_001`

---

## 如何添加新的 Guidance

1. 在 `guidance/` 下新建 `my_guidance.md`，使用 Markdown 格式编写。

2. 在 `file_io/readers.py` 的 `GUIDANCE_TASK_MAP` 中，将新文件关联到对应任务：

```python
GUIDANCE_TASK_MAP = {
    "quantity_takeoff": [
        "general_principles",
        "decoration_quantity",
        "my_guidance",  # 新增
        ...
    ],
}
```

3. 也可以在对应 skill 的 `guidance_files` 属性中添加。

---

## 如何添加公司规则

将公司算量规则整理为 Markdown 文件，放入：

- `knowledge/company_rules/` — 通用公司规则
- `knowledge/project_rules/项目名/` — 项目专属规则

Orchestrator 会自动加载 `knowledge/china_cost_engineering_tasks.md` 作为背景知识。

---

## 如何进行评测

1. 先运行算量任务生成 AI 输出
2. 造价师填写 `cases/{case_id}/golden_answer/human_answer.json`
3. 运行评测：

```bash
python evaluation/evaluate_case.py --case sample_case_001
```

评测结果保存到 `outputs/{case_id}/evaluation_report_YYYYMMDD_HHMMSS.json`

**8 项评测指标**：准确率、漏项率、重复计算率、数量偏差率、可解释性、复核成本、图纸依据完整性、不确定项标记。

---

## 后续路线图

### Phase 1（当前）
- [x] 项目骨架搭建
- [x] 6 个 skill 模板
- [x] Guidance 文档体系
- [x] 评测框架
- [ ] 填入真实图纸案例，跑通第一个 AI 算量

### Phase 2
- [ ] 补充公司算量规则（造价师主导）
- [ ] 积累评测案例库
- [ ] 根据评测结果优化 guidance 和 prompt
- [ ] 装修工程量计算精度达到 ±5% 目标

### Phase 3
- [ ] 广联达文件导出对接（路径 B）
- [ ] 更多专业支持（土建、安装）

### Phase 4
- [ ] 接入飞书/企业微信 Bot
- [ ] 向量数据库升级（Chroma / Qdrant）
- [ ] 广联达 API 集成（如有）

---

## 广联达集成计划

详见 `integrations/glodon_adapter.py`。三种路径：

| 路径 | 方式 | 状态 |
|------|------|------|
| A | 官方 API/SDK | TODO：确认广联达是否开放 |
| B | 文件导入导出（Excel/GTJ）| 优先推进 |
| C | RPA/GUI 自动化 | 备选方案 |

---

## 飞书集成

本项目通过 Claude Code + cc-connect 与飞书对接。
未来可在飞书机器人中直接发送算量指令，例如：
```
@造价AI 图纸审阅 [附上图纸.pdf]
@造价AI 工程量初算 案例：proj_001
```

---

## 重要免责声明

> AI 输出仅作为工程量初稿参考，不作为最终造价成果。
> 所有输出必须经注册造价工程师人工复核后方可用于报价、结算或任何正式用途。
> 本系统不对 AI 输出的准确性承担任何法律责任。
