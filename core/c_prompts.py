# -*- coding: utf-8 -*-
"""
prompts.py — 智能工厂申报书大纲智能生成模块
包含：知识库数据、CO-STAR 提示词、生成规则、辅助功能Prompt、问卷字段定义
数据来源：IMA 共享知识库「智能工厂政策」(ID: 7482270705267738) · 全部 34 份文档
作者：第四五章负责人
"""

# ====================================================================
# 一、知识库元数据与文档索引（34份文档完整索引）
# ====================================================================

KB_META = {
    "name": "智能工厂政策",
    "id": "7482270705267738",
    "totalDocs": 34,
    "creator": "邵熠丰",
    "members": 10,
}

# A. 政策法规类（8份）
POLICY_DOCS = [
    {"id": "A1", "name": "2026大连市深化制造业智能化改造数字化转型三年行动计划.pdf", "format": "PDF", "source": "大连市政府", "docNo": "—", "usage": "市级政策依据"},
    {"id": "A2", "name": "（最新版）惠企政策30条20260225(1)(1).pdf", "format": "PDF", "source": "工信局", "docNo": "—", "usage": "补贴标准原文"},
    {"id": "A3", "name": "关于2026年度辽宁省智能工厂梯度培育工作的通知.pdf", "format": "PDF", "source": "辽宁省工信厅", "docNo": "辽工信明电[2026]3号", "usage": "省级申报通知"},
    {"id": "A4", "name": "附件1.关于2026年度智能工厂梯度培育有关工作安排的预通知(1).pdf", "format": "PDF", "source": "工信部", "docNo": "工通装函〔2026〕47号", "usage": "国家级预通知"},
    {"id": "A5", "name": "智能工厂梯度培育行动实施方案.pdf", "format": "PDF", "source": "工信部", "docNo": "—", "usage": "梯度培育框架"},
    {"id": "A6", "name": "智能工厂梯度培育要素条件（2024）.pdf", "format": "PDF", "source": "工信部", "docNo": "—", "usage": "2024版要素条件"},
    {"id": "A7", "name": "智能工厂梯度培育要素条件（2025）.pdf", "format": "PDF", "source": "工信部", "docNo": "沪经信制〔2025〕430号", "usage": "2025版要素条件"},
    {"id": "A8", "name": "智能工厂梯度培育要素条件.docx", "format": "DOCX", "source": "工信部", "docNo": "—", "usage": "2025年版要素条件（Word版）"},
]

# B. 申报材料类（6份）
APPLICATION_DOCS = [
    {"id": "B1", "name": "A企业-辽宁省-装备制造-卓越级智能工厂项目申报书（盖章件）.pdf", "format": "PDF", "level": "卓越级", "usage": "申报书模板范本"},
    {"id": "B2", "name": "A企业电控装备厂_先进级智能工厂项目申报书.pdf", "format": "PDF", "level": "先进级", "usage": "申报书模板范本"},
    {"id": "B3", "name": "1.先进级智能工厂项目申报书-大连某物流装备企业装备有限公司.pdf", "format": "PDF", "level": "先进级", "usage": "申报书模板范本"},
    {"id": "B4", "name": "卓越级智能工厂项目申报材料清单.pdf", "format": "PDF", "level": "卓越级", "usage": "材料清单要求"},
    {"id": "B5", "name": "先进级智能工厂、省级数字化车间-申报书样式及说明.docx", "format": "DOCX", "level": "先进级/数字化车间", "usage": "申报说明与格式"},
    {"id": "B6", "name": "《智能工厂梯度培育申报专家顾问智能体》.docx", "format": "DOCX", "level": "通用", "usage": "智能体设计参考"},
]

# C. 评审标准类（5份）
REVIEW_DOCS = [
    {"id": "C1", "name": "AA2026年度先进级智能工厂-企业打分表.xlsx", "format": "XLSX", "usage": "2026年度评分标准"},
    {"id": "C2", "name": "AA2025年度先进级智能工厂-企业打分表.xlsx", "format": "XLSX", "usage": "2025年度评分标准"},
    {"id": "C3", "name": "20_WD_2024005768_智能制造能力成熟度模型.pdf", "format": "PDF", "usage": "GB/T 39116国家标准"},
    {"id": "C4", "name": "20_WD_2024005769_智能制造能力成熟度评估方法.pdf", "format": "PDF", "usage": "GB/T 39117国家标准"},
    {"id": "C5", "name": "智能工厂评审标准相关的官方网站链接2025.docx", "format": "DOCX", "usage": "权威文件链接汇总"},
]

# D. 典型场景与解决方案类（5份）
SCENE_DOCS = [
    {"id": "D1", "name": "智能制造典型场景指引2025版（8大环节40个场景）.pdf", "format": "PDF", "usage": "场景建设参考"},
    {"id": "D2", "name": "《智能制造典型场景参考指引（2025年版）》.pdf", "format": "PDF", "usage": "场景建设参考（副本）"},
    {"id": "D3", "name": "智能工厂规划建设方案-大连4月.pdf", "format": "PDF", "usage": "中汽智造大连规划方案"},
    {"id": "D4", "name": "中汽智造-智能工厂整体解决方案(1).pdf", "format": "PDF", "usage": "中汽智造整体方案"},
    {"id": "D5", "name": "领航工厂案例（2026版）.pdf", "format": "PDF", "usage": "领航级案例集"},
]

# E. 讲座PPT类（3份）
LECTURE_DOCS = [
    {"id": "E1", "name": "人工智能及数字化转型政策介绍(1).pptx", "format": "PPTX", "speaker": "边志达", "org": "大连市智能制造产业协会"},
    {"id": "E2", "name": "智能工厂政策介绍.pptx", "format": "PPTX", "speaker": "孔晟源", "org": "—"},
    {"id": "E3", "name": "智能制造典型场景及转型路径(1)(1).pptx", "format": "PPTX", "speaker": "边子轩", "org": "依科（大连市中小企业数字化转型试点城市服务商）"},
]

# F. 企业成熟度报告与数据类（4份）
ENTERPRISE_DOCS = [
    {"id": "F1", "name": "智能制造成熟度评估报告--XX企业.pdf", "format": "PDF", "enterprise": "大连德原工业有限公司", "cmmm": "3.55分/三级", "industry": "汽车制造业"},
    {"id": "F2", "name": "7-智能制造成熟度报告-大连融科储能集团股份有限公司.pdf", "format": "PDF", "enterprise": "大连融科储能集团股份有限公司", "cmmm": "3.71分/三级", "industry": "化学原料和化学制品制造业"},
    {"id": "F3", "name": "智能制造成熟度指数报告（2022）.pdf", "format": "PDF", "enterprise": "全国行业报告", "cmmm": "—", "industry": "—"},
    {"id": "F4", "name": "大连市国家级专精特新小巨人企业调研报告.xlsx", "format": "XLSX", "enterprise": "91家企业", "cmmm": "—", "industry": "约20个大类"},
]

# G. 名单汇总表类（3份）
LIST_DOCS = [
    {"id": "G1", "name": "辽宁省基础级智能工厂名单汇总表.docx", "format": "DOCX", "usage": "名单格式模板"},
    {"id": "G2", "name": "海外智能工厂培育名单.docx", "format": "DOCX", "usage": "海外工厂名单模板"},
    {"id": "G3", "name": "卓越级智能工厂项目推荐汇总表.doc", "format": "DOC", "usage": "推荐汇总表模板"},
]

# 全部文档索引
ALL_DOCS = POLICY_DOCS + APPLICATION_DOCS + REVIEW_DOCS + SCENE_DOCS + LECTURE_DOCS + ENTERPRISE_DOCS + LIST_DOCS


# ====================================================================
# 二、四级梯度体系与补贴标准
# ====================================================================

LEVELS = {
    "basic":     {"name": "基础级", "review": "市级工信部门复核", "subsidy": "—",       "maturity": "GB/T 39116 二级及以上",          "req": "规模以上工业企业，已完成数字化网络化建设", "doc": "A5-A8"},
    "advanced":  {"name": "先进级", "review": "省级工信部门评审", "subsidy": "≤100万",   "maturity": "达到先进级要素条件要求",           "req": "已完成智能工厂建设并投入使用，省内同行业引领带动", "doc": "A2/A5-A8/B2/B3"},
    "excellent": {"name": "卓越级", "review": "工信部组织评审",   "subsidy": "≤200万",   "maturity": "达到卓越级要素条件要求",           "req": "国家级智能工厂，建设成效显著", "doc": "A2/A5-A8/B1/B4"},
    "leading":   {"name": "领航级", "review": "工信部组织评审",   "subsidy": "≤200万",   "maturity": "达到领航级要素条件要求",           "req": "最高级别，具有国际竞争力", "doc": "A5-A8/D5"},
}

# 政策层级体系
POLICY_HIERARCHY = {
    "national": [
        {"doc": "工通装函〔2026〕47号", "title": "关于2026年度智能工厂梯度培育有关工作安排的预通知"},
        {"doc": "工信部联通装〔2025〕262号", "title": "智能工厂梯度培育管理办法（暂行）"},
        {"doc": "—", "title": "智能工厂梯度培育行动实施方案"},
        {"doc": "—", "title": "智能工厂梯度培育要素条件（2025年版）"},
        {"doc": "—", "title": "智能制造典型场景参考指引（2025年版）— 8大环节40个场景"},
        {"doc": "GB/T 39116-2020", "title": "智能制造能力成熟度模型"},
        {"doc": "GB/T 39117-2020", "title": "智能制造能力成熟度评估方法"},
    ],
    "provincial": [
        {"doc": "辽政发〔2026〕3号", "title": "促进经济向新向好若干政策举措"},
        {"doc": "辽工信明电〔2026〕3号", "title": "关于2026年度辽宁省智能工厂梯度培育工作的通知"},
    ],
    "municipal": [
        {"doc": "—", "title": "2026大连市深化制造业智能化改造数字化转型三年行动计划（2026-2028年）"},
        {"doc": "大工信发〔2024〕113号", "title": "中小企业数字化转型试点工作方案"},
    ],
}

# 惠企政策30条补贴标准（原文引用）
SUBSIDIES = [
    {"dept": "工信局", "no": 1, "name": "优质中小企业梯度培育", "text": "对首次认定为国家级专精特新\"小巨人\"企业和省级\"专精特新\"中小企业，分别给予50万和30万一次性奖补", "doc": "A2"},
    {"dept": "工信局", "no": 2, "name": "辽宁省数字化车间", "text": "对建成省级数字化车间的企业，给予不超过50万的资金支持", "doc": "A2"},
    {"dept": "工信局", "no": 3, "name": "智能工厂梯度培育", "text": "对建成国家级智能工厂（卓越级及以上）给予不超过200万；省级智能工厂（先进级）给予不超过100万", "doc": "A2"},
]

# 申报基本条件
APPLICATION_CONDITIONS = [
    "企业应为规模以上工业企业，企业和产品均具有较强市场竞争力",
    "企业近三年经营和财务状况良好，无不良信用记录、无较大及以上安全、环保等事故，无违法违规行为",
    "工厂使用的关键技术装备、工业软件、工业操作系统、系统解决方案等安全可控，网络安全和数据安全风险可控",
    "企业应建立智能工厂统筹规划、建设和运营的组织机制，拥有一批智能制造专业人才",
    "基础级和先进级工厂智能制造能力成熟度评估水平达到GB/T 39116-2020《智能制造能力成熟度模型》二级及以上",
]

# 卓越级/领航级申报书结构（9大章，对标A企业范本B1）
EXCELLENT_CHAPTERS = [
    "封面（项目名称 / 申报单位盖章 / 推荐单位盖章 / 申报日期）",
    "真实性及保密承诺",
    "一、申报主体和智能工厂基本信息（申报主体信息 + 工厂基本信息）",
    "二、智能工厂场景建设情况（项目总体情况 + 具体场景建设 + 系统集成）",
    "三、智能工厂建设成效（先进性与特色 + 实施成效 + 后续实施计划）",
    "四、投资预算与资金来源",
    "五、实施进度",
    "六、预期效益",
    "七、保障措施",
]

# 先进级申报书结构（7大章，对标某物流装备企业范本B3）
ADVANCED_CHAPTERS = [
    "封面 + 真实性承诺",
    "一、申报主体和智能工厂基本信息",
    "二、智能工厂场景建设情况",
    "三、智能工厂建设成效",
    "四、投资预算与资金来源",
    "五、实施进度",
    "六、预期效益",
    "七、保障措施",
]

# 成熟度等级标准（GB/T 39116）
MATURITY_LEVELS = [
    {"level": "一级", "name": "基础自动化", "feature": "基础自动化改造，局部数字化"},
    {"level": "二级", "name": "局部集成化", "feature": "部分系统间集成，数据局部共享"},
    {"level": "三级", "name": "系统级集成", "feature": "跨系统全流程集成，数据全面打通"},
    {"level": "四级", "name": "全流程智能化", "feature": "全流程智能化运行，数据驱动决策"},
]

# 八大环节（依据D1/D2典型场景指引2025版）
EIGHT_SCENES = [
    {"no": 1, "name": "工厂建设环节", "basis": "厂房设计、设施部署、产线建设"},
    {"no": 2, "name": "研发设计环节", "basis": "产品设计、工艺仿真、数字孪生"},
    {"no": 3, "name": "生产作业环节", "basis": "人机协同、柔性制造、智能排产"},
    {"no": 4, "name": "生产管理环节", "basis": "质量管控、设备管理、能耗监测"},
    {"no": 5, "name": "检验检测环节", "basis": "在线检测、智能质检、追溯管理"},
    {"no": 6, "name": "仓储物流环节", "basis": "智能仓储、自动配送、供应链协同"},
    {"no": 7, "name": "运营管理环节", "basis": "计划调度、供应链管理、决策分析"},
    {"no": 8, "name": "销售服务环节", "basis": "客户管理、远程运维、产品服务"},
]

# 评审评分维度
SCORING_DIMS = [
    {"dim": "1.智能制造成熟度", "item": "2025年智能制造能力成熟度评估报告", "range": "0-20分",
     "detail": "一级(基础自动化)0分；二级(局部集成化)5分；三级(系统级集成)10分；四级(全流程智能化)20分", "doc": "C1/C2"},
    {"dim": "2.信息基础建设水平", "item": "智能装备应用、设备互联互通、生产线智能化、工业互联网、数据中台、云应用",
     "range": "[详见打分表]", "detail": "智能装备广泛应用（智能设备占比、生产设备数字化管理能力成熟度等）", "doc": "C1/C2"},
]

# 数据原则（7条）
DATA_PRINCIPLES = [
    "所有政策引用标注文号 — 必须使用知识库文档原文文号",
    "所有补贴金额引用原文 — 必须引用《惠企政策30条》原文表格",
    "所有结构依据范本 — 必须依据对应级别的申报书范本原文目录",
    "所有评分维度对齐 — 必须覆盖知识库评分表的所有评分项",
    "所有场景依据指引 — 必须依据《典型场景参考指引》8环节40场景",
    "禁止编造数据 — 无法获取的数据标注 [需企业提供]",
    "禁止通用网络模板 — 所有内容来源于知识库文档",
]

# 知识库检索流程（7步）
RETRIEVAL_FLOW = [
    {"step": 1, "title": "确定申报级别", "detail": "用户选择: 基础级 / 先进级 / 卓越级 / 领航级"},
    {"step": 2, "title": "检索对应范本", "detail": "基础级→G1+A8 | 先进级→B2/B3+B5+C1/C2 | 卓越级→B1+B4+A7 | 领航级→D5+A4"},
    {"step": 3, "title": "检索政策依据", "detail": "国家级→A4+A5+A6-A8 | 省级→A3 | 市级→A1+A2"},
    {"step": 4, "title": "检索场景体系", "detail": "D1/D2(典型场景指引: 8环节40场景)"},
    {"step": 5, "title": "检索中汽智造方案", "detail": "D3(大连规划方案) + D4(整体解决方案)"},
    {"step": 6, "title": "检索评审标准", "detail": "C1/C2(评分表) + C3/C4(国标) + C5(官方链接)"},
    {"step": 7, "title": "检索对标数据", "detail": "F1-F4(成熟度报告/企业数据) + E1-E3(讲座内容)"},
]


# ====================================================================
# 三、CO-STAR 提示词 V3.3 终版（核心Prompt）
# ====================================================================

COSTAR_PROMPT = """# 角色设定

你是一位拥有 10 年经验的智能制造申报书顾问，熟悉工信部、辽宁省、大连市三级政策体系。
你服务于大连市智能制造产业协会，服务对象是辽宁中小制造企业。
你的知识库包含 34 份政策和范本文档，涵盖：
- 政策法规 8 份：工通装函〔2026〕47号、辽工信明电〔2026〕3号、大工信发〔2024〕113号、惠企政策30条、要素条件2024/2025版等
- 申报范本 6 份：A企业（卓越级+先进级）、某物流装备企业（先进级）真实盖章件
- 评审标准 5 份：2025/2026年度打分表、GB/T 39116、GB/T 39117
- 典型场景 5 份：8大环节40场景、中汽智造大连规划方案、领航工厂案例集
- 企业数据 4 份：德原工业（CMMM 3.55/三级）、融科储能（CMMM 3.71/三级）

---

# 任务

请根据以下企业信息，生成一份完整的智能工厂申报书分级大纲。

## 执行步骤

1. 判断申报等级：根据企业现状，判断属于「基础级 / 先进级 / 卓越级 / 领航级」中的哪一级
2. 检索适配政策：从知识库中匹配适用的政策条款和补贴标准
3. 套用范本结构：根据判断的等级，套用对应的申报书范本结构
   - 卓越级 / 领航级 → 参考A企业范本（9 大章）
   - 先进级 → 参考某物流装备企业范本（7 大章）
4. 填充企业信息：将企业提供的实际数据填入对应章节；缺失数据标注「[需企业补充]」

## 申报等级与补贴标准参考

| 等级 | 补贴上限 | 成熟度要求 | 评审主体 |
|------|---------|-----------|---------|
| 数字化车间 | ≤ 50 万 | — | 省级 |
| 基础级 | — | GB/T 39116 二级及以上 | 市级复核 |
| 先进级 | ≤ 100 万 | 达到先进级要素条件 | 省级评审 |
| 卓越级 | ≤ 200 万 | 达到卓越级要素条件 | 工信部评审 |
| 领航级 | ≤ 200 万 | 达到领航级要素条件 | 工信部评审 |

## 典型场景参考（8大环节）

1. 工厂建设环节 — 厂房设计、设施部署、产线建设
2. 研发设计环节 — 产品设计、工艺仿真、数字孪生
3. 生产作业环节 — 人机协同、柔性制造、智能排产
4. 生产管理环节 — 质量管控、设备管理、能耗监测
5. 检验检测环节 — 在线检测、智能质检、追溯管理
6. 仓储物流环节 — 智能仓储、自动配送、供应链协同
7. 运营管理环节 — 计划调度、供应链管理、决策分析
8. 销售服务环节 — 客户管理、远程运维、产品服务

---

# 输出格式要求

- 格式：Markdown，三级标题（# / ## / ###）
- 量化字段：用表格呈现（竖线分隔）
- 总字数：8000 ~ 12000 字
- 每章末尾：附「数据来源清单」，标注引用的知识库文档名称
- 补贴金额、政策文号、评分标准等必须标注来源文档
- 场景填报格式：「环节名—场景名—实例名」

---

# 风格与语气

- 风格：正式公文 + 行业术语，对标A企业和某物流装备企业的盖章件
- 语气：客观、严谨、可信
- 禁止：口语化表达、网络用语、编造数字和企业名称
- 数据规则：有来源的标注来源；无来源的标注「[需企业补充]」；绝不编造

---

# 受众

- 主受众：工信厅评审专家（40 岁以上，注重政策合规性和数据严谨性）
- 次受众：企业管理层（关注投资回报和可操作性）
- 阅读时长：每章控制在 15 分钟以内

---

# Few-shot 示例

## 示例 1：卓越级申报书结构（参考A企业范本B1）

# [企业名称]智能工厂申报书

## 第一章 项目总述
### 1.1 项目背景
### 1.2 建设目标
### 1.3 投资概算

## 第二章 企业基本情况
### 2.1 企业概况
### 2.2 生产经营状况
### 2.3 信息化基础

## 第三章 智能制造成熟度现状
### 3.1 评估依据（GB/T 39116）
### 3.2 各环节成熟度评分
### 3.3 成熟度等级判定

## 第四章 建设方案
### 4.1 总体架构
### 4.2 典型场景设计（8大环节40场景）
### 4.3 技术路线

## 第五章 投资预算与资金来源
### 5.1 投资估算
### 5.2 资金来源
### 5.3 补贴申请（≤ 200万）

## 第六章 实施计划
### 6.1 建设周期
### 6.2 里程碑节点

## 第七章 预期效益
### 7.1 经济效益
### 7.2 社会效益

## 第八章 保障措施
### 8.1 组织保障
### 8.2 人才保障
### 8.3 资金保障

## 第九章 风险分析
### 9.1 技术风险
### 9.2 实施风险

---

## 示例 2：先进级申报书结构（参考某物流装备企业范本B3）

# [企业名称]数字化车间 / 智能工厂申报书

## 第一章 项目概况
## 第二章 企业基本情况
## 第三章 数字化 / 智能化现状
## 第四章 建设方案
## 第五章 投资预算
## 第六章 实施进度
## 第七章 预期效益

---

# 异常处理

1. 知识库中无相关数据时：在该处标注「[需企业补充]」，不要编造
2. 用户询问政策范围外的问题时：礼貌说明不在本次申报范围内，并指引咨询相关部门
3. 输出超字数时：自动精简二级标题下的详细描述，保留三级标题结构
4. 企业信息不足无法判断等级时：输出各等级对应条件，请企业自评后补充

---

# 企业信息输入

（以下由企业填写）

- 企业名称：
- 所属行业：
- 主营产品：
- 年营收：
- 员工人数：
- 现有信息化系统：
- 已完成改造情况：
- 拟申报等级（如已知）：
- 项目总投资预算：
- 其他补充说明：
"""


# ====================================================================
# 四、六项生成规则
# ====================================================================

GENERATION_RULES = [
    {
        "no": 1,
        "title": "结构严格依据范本",
        "detail": "申报书目录结构必须依据知识库内对应级别的申报书范本原文生成：先进级→依据B2/B3范本目录结构；卓越级→依据B1范本目录结构+B4材料清单要求",
        "doc": "B1/B2/B3/B4",
    },
    {
        "no": 2,
        "title": "政策引用必须标注文号",
        "detail": "所有政策引用必须标注原文文号：[政策依据: 辽工信明电[2026]3号]、[政策依据: 大工信发[2024]113号]、[政策依据: 工通装函〔2026〕47号]",
        "doc": "A3/A4/E2",
    },
    {
        "no": 3,
        "title": "补贴金额引用原文",
        "detail": "补贴标准必须引用《惠企政策30条》原文表格数据：数字化车间不超过50万[来源:惠企政策30条第2条]；先进级不超过100万[来源:惠企政策30条第3条]；卓越级及以上不超过200万[来源:惠企政策30条第3条]",
        "doc": "A2",
    },
    {
        "no": 4,
        "title": "场景描述依据指引",
        "detail": "智能工厂场景建设内容必须依据《智能制造典型场景参考指引（2025年版）》的8大环节40个场景体系，按\"环节名—场景名—实例名\"格式填报",
        "doc": "D1/D2/G1",
    },
    {
        "no": 5,
        "title": "评分维度对齐打分表",
        "detail": "大纲中的建设成效部分必须覆盖知识库评分表的所有评分维度，确保申报内容与评审标准完全对齐",
        "doc": "C1/C2",
    },
    {
        "no": 6,
        "title": "数据来源标注规范",
        "detail": "政策原文数据标注[来源:知识库文档名,原文位置]；范本结构数据标注[来源:申报书范本-企业名]；评分标准数据标注[来源:XXXX年度评分表]；企业对标数据标注[来源:企业名-CMMM报告]；待补充数据标注[需企业提供:具体数据项]；预测推算数据标注[预测:测算依据]",
        "doc": "全库",
    },
]


# ====================================================================
# 五、F1~F8 辅助功能 Prompt
# ====================================================================

AUX_FUNCTIONS = [
    {"id": "F1", "name": "政策解读", "input": "政策条款原文",
     "output": "一句话通俗解释 + 适用企业类型 + 申报要点(3~5条) + 补贴金额(如有) + 来源文档名称"},
    {"id": "F2", "name": "等级自评", "input": "企业现状描述(行业、规模、信息化基础、改造情况)",
     "output": "建议申报等级 + 各等级差距清单(逐条列缺什么) + 整改路径(按优先级排序) + 预估CMMM得分区间",
     "basis": "GB/T 39116 成熟度模型、要素条件 2025 版"},
    {"id": "F3", "name": "政策匹配", "input": "企业描述",
     "output": "政策列表表格(序号/政策名称/文号/补贴金额/匹配度/申报截止)，按匹配度从高到低排序",
     "basis": "知识库 A1-A8 全部政策文档"},
    {"id": "F4", "name": "范本检索", "input": "关键词(如「仓储环节」「投资预算」「成熟度评估」)",
     "output": "匹配的范本片段(原文引用) + 来源文档名称和页码 + 适用场景说明 + 适用申报等级",
     "basis": "A企业(卓越级+先进级)、某物流装备企业(先进级)"},
    {"id": "F5", "name": "补贴测算", "input": "项目总投资额 + 申报等级",
     "output": "适用补贴政策名称和文号 + 补贴区间(数字化车间≤50万/先进级≤100万/卓越级及以上≤200万) + 计算依据(引用政策原文条款) + 注意事项",
     "basis": "《惠企政策30条》原文表格"},
    {"id": "F6", "name": "材料清单", "input": "申报等级",
     "output": "材料清单表格(序号/材料名称/是否必需/模板链接/备注)，按必需→选填排序",
     "basis": "B4 卓越级材料清单、B5 申报书样式及说明"},
    {"id": "F7", "name": "评审模拟", "input": "申报书草稿",
     "output": "模拟专家提问(5~8题，覆盖政策合规性、技术可行性、经济效益、风险) + 风险点提示(按「高/中/低」标注) + 改进建议",
     "basis": "C1/C2 打分表、GB/T 39116"},
    {"id": "F8", "name": "知识问答", "input": "任意问题",
     "output": "精准回答(引用知识库原文) + 来源文档名称和位置 + 相关延伸(如有)",
     "basis": "知识库全部34份文档"},
]


# ====================================================================
# 六、企业申报问卷字段定义（10大模块）
# ====================================================================

QUESTIONNAIRE_SCHEMA = {
    # 模块一：企业基本信息
    "module_1_enterprise": {
        "title": "企业基本信息",
        "fields": {
            "entName":    {"label": "企业全称", "type": "text", "required": True, "placeholder": "如：大连XX机械制造有限公司"},
            "creditCode": {"label": "统一社会信用代码", "type": "text", "required": False, "placeholder": "18位代码"},
            "foundDate":  {"label": "成立时间", "type": "date", "required": False},
            "address":    {"label": "注册地址", "type": "text", "required": False, "placeholder": "大连市XX区XX路XX号"},
            "mainBiz":    {"label": "主营业务", "type": "text", "required": True, "placeholder": "如：高端装备制造、汽车零部件"},
            "industry":   {"label": "行业分类(GB/T 4754)", "type": "select", "required": False,
                           "options": ["装备制造业", "汽车制造业", "化学原料和化学制品制造业", "电气机械和器材制造业",
                                       "金属制品业", "通用设备制造业", "专用设备制造业", "计算机、通信和其他电子设备制造业",
                                       "食品制造业", "纺织业", "医药制造业", "其他制造业"]},
            "employees":  {"label": "员工人数", "type": "text", "required": False, "placeholder": "如：320人"},
            "revenue":    {"label": "年营业收入(万元)", "type": "number", "required": True, "placeholder": "如：15000"},
        },
        "source_doc": "A7/A8 申报基本条件",
    },
    # 模块二：申报工厂基本信息
    "module_2_factory": {
        "title": "申报工厂基本信息",
        "fields": {
            "factoryName":  {"label": "申报工厂名称", "type": "text", "required": True, "placeholder": "如：XX智能工厂"},
            "factoryAddr":  {"label": "工厂地址", "type": "text", "required": False},
            "buildStart":   {"label": "建设起始时间", "type": "date", "required": False},
            "buildEnd":     {"label": "建设完成时间", "type": "date", "required": False},
            "totalInvest":  {"label": "项目总投资额(万元)", "type": "number", "required": True, "placeholder": "如：3000"},
            "integrator":   {"label": "主要系统集成商", "type": "text", "required": False, "placeholder": "如：中汽智造/XX科技"},
        },
        "source_doc": "B1/B2/B3 范本结构",
    },
    # 模块三：智能化建设基础
    "module_3_infrastructure": {
        "title": "智能化建设基础",
        "fields": {
            "systems":    {"label": "已部署的信息系统", "type": "multi_select",
                           "options": ["MES 制造执行系统", "ERP 企业资源计划", "PLM 产品生命周期", "WMS 仓储管理",
                                       "SCADA 数据采集", "CRM 客户管理", "SCM 供应链管理", "BI 商业智能",
                                       "工业互联网平台", "数字孪生平台"]},
            "equipment":  {"label": "主要自动化设备", "type": "multi_select",
                           "options": ["工业机器人", "数控机床(CNC)", "AGV/AMR", "智能传感器", "机器视觉检测",
                                       "3D打印/增材制造", "自动化产线", "PLC/DCS控制系统"]},
            "netRate":    {"label": "设备联网率(%)", "type": "number", "required": True, "placeholder": "如：92"},
            "prodLines":  {"label": "自动化产线数量", "type": "number", "required": False, "placeholder": "如：5"},
        },
        "source_doc": "C1/C2 评审打分表",
    },
    # 模块四：CMMM成熟度评估
    "module_4_cmmm": {
        "title": "智能制造能力成熟度(CMMM)",
        "fields": {
            "cmmmDone":   {"label": "是否已做CMMM评估？", "type": "radio", "options": ["未评估", "已评估"], "default": "未评估"},
            "cmmmLevel":  {"label": "CMMM等级", "type": "select",
                           "options": ["一级(基础自动化)", "二级(局部集成化)", "三级(系统级集成)", "四级(全流程智能化)"]},
            "cmmmScore":  {"label": "CMMM得分", "type": "number", "step": 0.01, "placeholder": "如：3.55"},
            "cmmmOrg":    {"label": "评估机构", "type": "text", "placeholder": "如：中国电子技术标准化研究院"},
        },
        "benchmark": "F1 德原工业 CMMM 3.55/三级 · F2 融科储能 CMMM 3.71/三级",
    },
    # 模块五：八大环节建设情况
    "module_5_scenes": {
        "title": "八大环节建设情况",
        "source_doc": "D1 典型场景指引2025版",
        "scenes": EIGHT_SCENES,
        "format": "环节名—场景名—实例名",
    },
    # 模块六：建设成效数据
    "module_6_effectiveness": {
        "title": "建设成效数据（建设前后对比）",
        "fields": {
            "effEfficiency": {"label": "生产效率提升(%)", "type": "number", "placeholder": "如：35"},
            "effQuality":    {"label": "良品率提升(%)", "type": "number", "placeholder": "如：12"},
            "effCost":       {"label": "运营成本降低(%)", "type": "number", "placeholder": "如：20"},
            "effEnergy":     {"label": "能耗降低(%)", "type": "number", "placeholder": "如：15"},
        },
        "source_doc": "B2 申报须知",
    },
    # 模块七：投资预算明细
    "module_7_budget": {
        "title": "投资预算明细",
        "fields": {
            "investEquip": {"label": "设备购置(万元)", "type": "number", "placeholder": "如：1200"},
            "investSoft":  {"label": "软件开发(万元)", "type": "number", "placeholder": "如：500"},
            "investInteg": {"label": "系统集成(万元)", "type": "number", "placeholder": "如：800"},
            "investOther": {"label": "其他费用(万元)", "type": "number", "placeholder": "如：200"},
            "fundSource":  {"label": "资金来源", "type": "multi_select",
                           "options": ["企业自筹", "银行贷款", "政府补贴", "社会资本"]},
        },
        "source_doc": "A2 惠企政策30条",
    },
    # 模块八：认证与荣誉
    "module_8_certs": {
        "title": "认证与荣誉",
        "fields": {
            "certs":     {"label": "已获认证", "type": "multi_select",
                          "options": ["ISO 9001 质量管理", "ISO 14001 环境管理", "ISO 45001 职业健康安全",
                                      "IATF 16949 汽车行业", "两化融合管理体系", "信息安全管理体系"]},
            "petType":   {"label": "专精特新认定", "type": "select",
                          "options": ["未认定", "省级专精特新中小企业", "国家级专精特新\"小巨人\""]},
            "otherHonor":{"label": "其他智能制造荣誉", "type": "text", "placeholder": "如：省级智能制造示范工厂"},
        },
        "source_doc": "A2 惠企政策30条",
    },
    # 模块九：安全合规情况
    "module_9_safety": {
        "title": "安全合规情况",
        "fields": {
            "safeRecord":   {"label": "近三年无重大安全事故", "type": "radio", "options": ["是", "否"], "default": "是"},
            "netSecurity":  {"label": "网络安全风险评估", "type": "radio", "options": ["已评估", "未评估"], "default": "未评估"},
        },
        "source_doc": "A7/A8 申报基本条件",
    },
    # 模块十：补充说明
    "module_10_remark": {
        "title": "其他补充说明",
        "fields": {
            "remark": {"label": "补充说明", "type": "textarea", "placeholder": "如有其他需要说明的情况请填写..."},
        },
    },
}


# ====================================================================
# 七、辅助函数：构建知识库摘要文本
# ====================================================================

def build_kb_summary():
    """构建知识库摘要文本，用于注入Prompt"""
    lines = [
        f"知识库名称：{KB_META['name']}",
        f"知识库ID：{KB_META['id']}",
        f"文档总数：{KB_META['totalDocs']}份",
        f"创建者：{KB_META['creator']}",
        "",
        "## A. 政策法规类（8份）",
    ]
    for d in POLICY_DOCS:
        lines.append(f"  - {d['id']} {d['name']}（{d['docNo']}，{d['usage']}）")
    lines.append("\n## B. 申报材料类（6份）")
    for d in APPLICATION_DOCS:
        lines.append(f"  - {d['id']} {d['name']}（{d['level']}，{d['usage']}）")
    lines.append("\n## C. 评审标准类（5份）")
    for d in REVIEW_DOCS:
        lines.append(f"  - {d['id']} {d['name']}（{d['usage']}）")
    lines.append("\n## D. 典型场景与解决方案类（5份）")
    for d in SCENE_DOCS:
        lines.append(f"  - {d['id']} {d['name']}（{d['usage']}）")
    lines.append("\n## E. 讲座PPT类（3份）")
    for d in LECTURE_DOCS:
        lines.append(f"  - {d['id']} {d['name']}（主讲：{d['speaker']}）")
    lines.append("\n## F. 企业成熟度报告与数据类（4份）")
    for d in ENTERPRISE_DOCS:
        lines.append(f"  - {d['id']} {d['name']}（{d['enterprise']}，CMMM: {d['cmmm']}）")
    lines.append("\n## G. 名单汇总表类（3份）")
    for d in LIST_DOCS:
        lines.append(f"  - {d['id']} {d['name']}（{d['usage']}）")
    return "\n".join(lines)


def build_level_info(level_key):
    """根据等级key返回等级详情"""
    return LEVELS.get(level_key, LEVELS["advanced"])


def build_rules_text():
    """构建生成规则文本"""
    lines = []
    for r in GENERATION_RULES:
        lines.append(f"规则{r['no']}：{r['title']} — {r['detail']} [来源: {r['doc']}]")
    return "\n".join(lines)


def build_aux_prompts_text():
    """构建辅助功能Prompt摘要文本"""
    lines = []
    for f in AUX_FUNCTIONS:
        line = f"{f['id']} {f['name']}：输入={f['input']}，输出={f['output']}"
        if "basis" in f:
            line += f"，依据={f['basis']}"
        lines.append(line)
    return "\n".join(lines)


def build_questionnaire_prompt(questionnaire_data):
    """
    将企业问卷数据转换为Prompt可用的结构化文本
    questionnaire_data: dict，键为字段名，值为用户填写内容
    """
    lines = ["# 企业问卷填报数据\n"]
    for module_key, module_def in QUESTIONNAIRE_SCHEMA.items():
        module_title = module_def.get("title", module_key)
        lines.append(f"\n## {module_title}")
        fields = module_def.get("fields", {})
        for field_key, field_def in fields.items():
            label = field_def.get("label", field_key)
            value = questionnaire_data.get(field_key, "")
            if isinstance(value, list):
                value = "、".join(value) if value else "未填写"
            lines.append(f"- {label}：{value or '未填写'}")
        # 处理八大环节特殊模块
        if "scenes" in module_def:
            scenes_data = questionnaire_data.get("scenes", {})
            for scene in module_def["scenes"]:
                s_data = scenes_data.get(str(scene["no"]), {})
                built = s_data.get("built", "未填写")
                desc = s_data.get("desc", "")
                lines.append(f"- 环节{scene['no']} {scene['name']}：建设情况={built}，描述={desc or '未填写'}")
    return "\n".join(lines)


# ====================================================================
# 八、完整Prompt构建器
# ====================================================================

def build_full_prompt(questionnaire_data, target_level="advanced"):
    """
    构建完整的请求Prompt，包含CO-STAR提示词 + 知识库摘要 + 问卷数据 + 生成规则
    可直接传给OpenAI API的messages参数
    """
    level_info = build_level_info(target_level)

    system_prompt = f"""{COSTAR_PROMPT}

---

# 知识库数据（严格依据，禁止编造）

{build_kb_summary()}

---

# 申报等级信息

目标等级：{level_info['name']}
评审主体：{level_info['review']}
补贴上限：{level_info['subsidy']}
成熟度要求：{level_info['maturity']}
申报要求：{level_info['req']}
参考文档：{level_info['doc']}

---

# 六项生成规则（必须遵守）

{build_rules_text()}

---

# 辅助功能Prompt（F1~F8）

{build_aux_prompts_text()}
"""

    user_prompt = build_questionnaire_prompt(questionnaire_data)

    return system_prompt, user_prompt


if __name__ == "__main__":
    # 测试：打印知识库摘要
    print(build_kb_summary())
    print("\n" + "="*60)
    print("模块加载成功！")
    print(f"知识库文档总数：{len(ALL_DOCS)}")
    print(f"生成规则数：{len(GENERATION_RULES)}")
    print(f"辅助功能数：{len(AUX_FUNCTIONS)}")
    print(f"问卷模块数：{len(QUESTIONNAIRE_SCHEMA)}")
