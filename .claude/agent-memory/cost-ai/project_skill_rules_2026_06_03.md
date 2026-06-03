---
name: project-skill-rules-2026-06-03
description: 2026-06-03 完成识图规则+GB50500-2013计价规范的整合，新增 drawing_boq_skill 和两个 knowledge 规则库文件
metadata:
  type: project
---

2026-06-03 完成了两个原始文件的读取和规则固化，将识图规则、清单抽取逻辑、计价规范整合为可复用的 skill 规则库。同日在实图识别任务（一层平面图扫描件）中沉淀了建筑平面图专项规则（R-ARC 系列）。

**主要工作：**

1. 新增知识库文件 `knowledge/standards/drawing_recognition_rules.md`：
   - 来源：土建-中国建设工程图纸识图与构件清单抽取逻辑_Agent规则版 V1.0
   - 内容：P1/P2/P3 总原则、规范体系6级优先级、图纸读取流水线、各专业构件识别规则（建筑/结构/装饰/总图）、证据权重体系、置信度分级（0.85+高/0.65-0.84中/0.40-0.64低/<0.40极低）、R01~R19强制规则、构件清单标准JSON字段、识别前审核闯关表
   - 2026-06-03 追加第十七节：建筑平面图专项识别规则（R-ARC-01~R-ARC-08）+ 扫描图补充规定

2. 新增知识库文件 `knowledge/standards/gb50500_2013_pricing_rules.md`：
   - 来源：GB50500-2013 建设工程工程量清单计价规范完整版（457页）
   - 内容：核心术语定义、计价方式与费用构成、清单五要素（项目编码/名称/特征/计量单位/工程量）、工程量偏差15%调整规则、物价变化5%/10%分担规则、施工索赔28天程序、竣工结算28天审核时限、各专业清单计算规则摘要（土石方/砌筑/混凝土/门窗/防水/保温/装饰/措施）

3. 新增 Skill：`skills/drawing_boq_skill.py`（task_type = "drawing_boq"）：
   - 集成 P1/P2/P3 原则 + Rule 1/Rule 2 强制规则
   - 输出标准JSON格式，含：recognition_summary、components（含置信度/证据/警告）、unresolved_questions
   - 已在 `skills/__init__.py` 中注册

4. 新增 Skill：`skills/drawing_recognition_skill.py`（task_type = "drawing_recognition"）：
   - 建筑平面图专项识别 skill，在 DrawingBOQSkill 基础上专注建筑平面图单图识别
   - 集成 R-ARC-01~08 专项规则（轴网确立、墙厚取值、门窗统计、楼梯识别、柱净高、砌体扣减、房间面积绑定）
   - 已在 `skills/__init__.py` 中注册

5. 更新 `knowledge/standards/README.md`：补充三个文件的说明和规范版本注意事项

**Skill 选用指南：**
- `drawing_boq`（DrawingBOQSkill）：全专业完整图纸包，多专业综合识别+清单映射
- `drawing_recognition`（DrawingRecognitionSkill）：建筑专业单图/单层专项识别，更细化处理建筑平面图的轴网/门窗/楼梯/房间等建筑专项逻辑

**Why:** 用户提供了包含完整识图逻辑的 docx 和 GB50500-2013 完整 PDF，需要将其固化为可复用的规则库，避免每次任务重新描述规则。

**How to apply:** 图纸识读任务（drawing_boq）直接使用 DrawingBOQSkill；算量任务（quantity_takeoff）继续使用 QuantityTakeoffSkill + gb50854_2013_rules.md；清单编制/合同价款类任务参考 gb50500_2013_pricing_rules.md。

**重要版本说明：** 2024版新标准（GB/T 50500-2024、GB/T 50854-2024）已于2025-09-01起实施；如项目合同/招标文件另有约定，以约定为准；规则库基于2013版整理，核心计算规则大体一致。

[[project-overview]]
