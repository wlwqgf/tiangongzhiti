"""
模块⑤ 专家侧评定与反馈 —— 天工智梯「专家端智能体」整合包（V3.3）忠实落地

本模块以用户提供的专家端整合包真实内容为唯一蓝本（见 expert_pack/ 目录）：
  · 01_系统提示词_SystemPrompt.md
  · 02_能力契约_Capabilities.md（三大模块 Prompt + 输出格式）
  · 03_知识库_KnowledgeBase.md
  · 05_参考实现_ReferenceImplementation.md（离线关键词 Mock 引擎）
  · 04_样例数据（华锐重工/新兴机械/精密电子）

流水线：① 初步筛查（PASS/REJECT/PENDING_EXPERT）→ ② 内容增强标注（《申报书增强分析报告》）
        → ③ 评分辅助与建议（6维度100分制 + P0/P1/P2 修改清单）

离线（无 LLM Key）也能完整跑通：确定性关键词引擎复现三大模块判定逻辑（移植自 05 参考实现）。
配置 OpenAI 兼容接口后，三大模块可调用真实大模型生成完整报告文本。
"""
import os
import re
import sys
import json
import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.llm import call_llm, is_configured, DISCLAIMER
from core import e_prompts as E
from core.theme import apply_theme, render_expert_sidebar

st.set_page_config(page_title="⑤专家侧评定与反馈", layout="wide")
apply_theme()
st.markdown("<h1 style='font-size:1.55rem'>🧑‍⚖️ ⑤ 专家侧评定与反馈</h1>", unsafe_allow_html=True)
st.caption("天工智梯专家端智能体（V3.3）· 初筛 → 增强标注 → 评分建议 三步走 · 输出仅供专家参考")

# ============================================================
# 离线关键词分析引擎（移植自 05_参考实现_ReferenceImplementation.md）
# ============================================================
LEVEL_MATURITY_MIN = {"基础级": 2, "先进级": 2, "卓越级": 3, "领航级": 4}


def _hit(text: str, keywords) -> bool:
    return any(kw in text for kw in keywords)


def analyze_doc(text: str, target_level: str) -> dict:
    """复现 05 参考实现的 _analyzeDoc：提取布尔/语义信号供三大模块判定。"""
    # 负向词排除：如"替代人工操作"不算手工生产（见 05 注意点）
    manual_neg = ("替代人工操作" in text) or ("取代人工操作" in text)
    is_manual = (not manual_neg) and _hit(text, E._SIGNAL_KEYWORDS["is_manual_production"])

    signals = {
        "is_small_scale": _hit(text, E._SIGNAL_KEYWORDS["is_small_scale"]),
        "is_manual_production": is_manual,
        "has_mes": _hit(text, E._SIGNAL_KEYWORDS["has_mes"]),
        "has_iot": _hit(text, E._SIGNAL_KEYWORDS["has_iot"]),
        "has_automation": _hit(text, E._SIGNAL_KEYWORDS["has_automation"]),
        "has_digital_design": _hit(text, E._SIGNAL_KEYWORDS["has_digital_design"]),
        "has_ai": _hit(text, E._SIGNAL_KEYWORDS["has_ai"]),
        "has_datashare": _hit(text, E._SIGNAL_KEYWORDS["has_datashare"]),
        "has_safety_env": _hit(text, E._SIGNAL_KEYWORDS["has_safety_env"]),
        "has_revenue": _hit(text, E._FORM_FIELDS["has_revenue"]),
        "has_employees": _hit(text, E._FORM_FIELDS["has_employees"]),
        "has_commitment": _hit(text, E._FORM_FIELDS["has_commitment"]),
    }

    # 五大环节覆盖统计
    covered = [env for env, kws in E._ENV_KEYWORDS.items() if _hit(text, kws)]
    signals["covered_environments"] = covered
    signals["covered_count"] = len(covered)

    # 成熟度提取：优先"总分：X.X分"，其次等级词（避免误抓 GB/T 39116 标准号）
    m = re.search(r"总分[：: ]*(\d+\.?\d*)", text)
    if m:
        signals["maturity_score"] = float(m.group(1))
    else:
        lm = re.search(r"对应等级[：:]\s*([一二三四五])级", text)
        if lm:
            base = {"一": 1.3, "二": 2.3, "三": 3.3, "四": 4.3, "五": 4.9}[lm.group(1)]
            signals["maturity_score"] = base
        else:
            signals["maturity_score"] = None
    return signals


# ============================================================
# 模块一：初步筛查（screening）
# ============================================================
REQUIRED_SECTIONS = [
    ("申报单位基本信息", ["基本信息", "企业名称", "统一社会信用代码"]),
    ("申报等级声明", ["申报等级"]),
    ("智能工厂基本情况", ["基本情况", "建设起止时间", "总投资"]),
    ("智能工厂场景建设情况", ["场景建设", "具体场景", "集成情况"]),
    ("智能工厂建设成效", ["建设成效", "实施成效", "先进性"]),
    ("真实性及保密承诺", ["真实性", "保密", "承诺"]),
]


def screening(text: str, target_level: str) -> dict:
    s = analyze_doc(text, target_level)
    rid = f"SC-2026-{abs(hash(text)) % 10000:04d}"

    # 步骤1：完整性检查
    missing_sections, missing_fields = [], []
    for sec_name, hints in REQUIRED_SECTIONS:
        if not any(h in text for h in hints):
            missing_sections.append(sec_name)
    if "企业名称" not in text or "统一社会信用代码" not in text:
        missing_fields.append("企业名称/统一社会信用代码为空")
    authenticity = "完整" if ("真实" in text and "保密" in text and "承诺" in text) else ("不完整" if "承诺" in text else "缺失")
    formality_status = "FAIL" if (missing_sections or missing_fields) else "PASS"

    # 步骤2：基础要求核查
    basic_items = []
    basic_items.append({"item_name": "规模以上工业企业", "standard_source": "《要素条件》基础要求①",
                        "actual_status": "不满足" if s["is_small_scale"] else "满足",
                        "evidence_text": "含小微企业/小规模表述" if s["is_small_scale"] else "未提示小规模信号"})
    basic_items.append({"item_name": "近三年经营财务良好、无不良信用/事故", "standard_source": "《要素条件》基础要求②",
                        "actual_status": "数据不足", "evidence_text": "离线无法核验，需专家确认"})
    basic_items.append({"item_name": "关键装备/软件安全可控", "standard_source": "《要素条件》基础要求③",
                        "actual_status": "满足", "evidence_text": "未提示安全风险信号"})
    basic_items.append({"item_name": "智能工厂统筹组织机制与人才", "standard_source": "《要素条件》基础要求④",
                        "actual_status": "数据不足", "evidence_text": "离线无法核验，需专家确认"})
    ms = s["maturity_score"]
    ok5 = (ms is not None and ms >= LEVEL_MATURITY_MIN[target_level])
    basic_items.append({"item_name": f"成熟度≥{LEVEL_MATURITY_MIN[target_level]}级", "standard_source": "《要素条件》基础要求⑤",
                        "actual_status": ("满足" if ok5 else ("不满足" if ms is not None else "数据不足")),
                        "evidence_text": f"自评估={ms if ms is not None else '缺失'}"})
    basic_fail = any(it["actual_status"] == "不满足" for it in basic_items)
    basic_status = "FAIL" if basic_fail else ("INSUFFICIENT_DATA" if any(it["actual_status"] == "数据不足" for it in basic_items) else "PASS")

    # 步骤3：目标等级一票否决
    veto = []
    if target_level == "基础级":
        if s["is_manual_production"]:
            veto.append(("手工生产模式", "《要素条件》基础级"))
        if not s["has_automation"]:
            veto.append(("无关键装备数字化改造", "《要素条件》基础级"))
        if not s["has_iot"]:
            veto.append(("无生产数据实时采集", "《要素条件》基础级"))
        if s["covered_count"] < 1:
            veto.append(("未覆盖生产作业环节", "《要素条件》基础级"))
    elif target_level == "先进级":
        if not s["has_datashare"]:
            veto.append(("未实现生产经营数据互通共享", "《要素条件》先进级"))
        if not s["has_mes"]:
            veto.append(("未部署MES", "《要素条件》先进级"))
        if s["covered_count"] < 3:
            veto.append(("未覆盖生产作业+生产管理+运营管理三环节", "《要素条件》先进级"))
        if not s["has_digital_design"]:
            veto.append(("未提仿真或数字化设计工具", "《要素条件》先进级"))
        if not s["has_safety_env"]:
            veto.append(("未开展安全能源环保数字化管控", "《要素条件》先进级"))
    elif target_level == "卓越级":
        if not s["has_ai"]:
            veto.append(("未开展AI技术应用（AI场景<10%）", "《要素条件》卓越级 AI≥20%"))
        if s["covered_count"] < 5:
            veto.append(("未覆盖全部五个环节", "《要素条件》卓越级"))
        if not s["has_datashare"]:
            veto.append(("无工业互联网或高性能网络算力", "《要素条件》卓越级"))
        if ms is not None and ms < 3:
            veto.append(("成熟度<三级", "《要素条件》卓越级"))
    elif target_level == "领航级":
        if not s["has_ai"]:
            veto.append(("未开展AI技术应用（AI场景<40%）", "《要素条件》领航级 AI≥60%"))
        if s["covered_count"] < 5:
            veto.append(("未覆盖全部五个环节", "《要素条件》领航级"))
        if ms is not None and ms < 4:
            veto.append(("成熟度<四级", "《要素条件》领航级"))

    # 步骤4：综合判定
    maturity_missing = (ms is None)
    if formality_status == "FAIL":
        result = "REJECT"
        reject_reason = f"形式审查不通过：缺失{'、'.join(missing_sections + missing_fields)}"
        pending, suggested = None, None
    elif basic_fail:
        result = "REJECT"
        reject_reason = "基础要求不满足：" + "、".join(it["item_name"] for it in basic_items if it["actual_status"] == "不满足")
        suggested = "基础级" if target_level != "基础级" else None
        pending = None
    elif veto:
        result = "REJECT"
        reject_reason = "命中一票否决项：" + "；".join(f"{v[0]}（{v[1]}）" for v in veto)
        suggested = "基础级" if target_level in ("先进级", "卓越级", "领航级") else None
        pending = None
    elif maturity_missing:
        result = "PENDING_EXPERT"
        reject_reason = None
        pending = "缺失智能制造能力成熟度自评估报告/自评估得分，需专家核实后判定。"
        suggested = None
    else:
        result = "PASS"
        reject_reason, pending, suggested = None, None, None

    return {
        "screening_id": rid, "screening_result": result, "target_level": target_level,
        "formality_check": {"status": formality_status, "missing_sections": missing_sections,
                            "missing_fields": missing_fields, "authenticity_commitment": authenticity},
        "basic_requirement_check": {"status": basic_status, "checked_items": basic_items},
        "hard_indicator_check": {"status": ("FAIL" if veto else "PASS"), "veto_triggered": veto},
        "reject_reason": reject_reason, "pending_notes": pending,
        "forward_to_expert": result != "REJECT",
        "screening_summary": f"初筛结果={result}；覆盖环节{s['covered_count']}/5；成熟度={s['maturity_score']}；触发否决项{len(veto)}项。",
        "suggested_level_adjustment": suggested,
        "_signals": s,
    }


# ============================================================
# 模块二：内容增强标注（enhancement）—— 离线骨架
# ============================================================
def enhancement_skeleton(text: str, target_level: str) -> dict:
    s = analyze_doc(text, target_level)
    env_rows = []
    for env in ["工厂建设", "研发设计", "生产作业", "生产管理", "运营管理"]:
        hit = env in s["covered_environments"]
        kw = E._ENV_KEYWORDS[env][0]
        env_rows.append({"环节": env, "状态": "✅满足" if hit else "❌不满足",
                         "关键词": kw, "是否覆盖": "是" if hit else "否"})
    scene_rows = []
    for cat, scenes in E.OFFICIAL_40_SCENES.items():
        for sc in scenes:
            inv = _hit(text, [sc]) or _hit(text, [sc[:4]])
            scene_rows.append({"环节": cat, "场景": sc, "涉及": "涉及" if inv else "未涉及",
                               "程度": ("深度" if inv else "—")})
    covered_scenes = sum(1 for r in scene_rows if r["涉及"] == "涉及")
    red, yellow, blue = [], [], []
    if not s["has_mes"] and target_level in ("先进级", "卓越级", "领航级"):
        red.append("未部署MES（先进级及以上硬性要求）")
    if s["covered_count"] < 3 and target_level in ("先进级", "卓越级", "领航级"):
        red.append(f"覆盖环节仅{s['covered_count']}/5，未达目标等级覆盖要求")
    if not s["has_datashare"]:
        yellow.append("未体现生产经营数据互通共享")
    if s["maturity_score"] is None:
        blue.append("缺失成熟度自评估数据，需专家要求补充")
    return {"signals": s, "env_rows": env_rows, "scene_rows": scene_rows,
            "covered_scenes": covered_scenes, "red": red, "yellow": yellow, "blue": blue}


# ============================================================
# 模块三：评分辅助与建议（scoring）—— P0/P1/P2 离线清单
# ============================================================
DIM_TEMPLATES = {
    "智能制造成熟度": "补齐成熟度短板：按 GB/T 39116 逐能力域自评，对[部分满足/不满足]域制定[数据采集+流程固化]提升计划，目标达到{mat}级。",
    "信息基础建设水平": "关键工序设备应具有[预测性维护/远程监测]功能。通过[传感器+系统]实时采集存储，构建[算法模型]实现[故障预警]；推进 MES/ERP/SCADA/AGV 数采集成（鼓励国产）。",
    "技术应用先进性": "对生产工艺与质量要素采集监控，构建工艺与质量数据关联模型，实时调整工艺参数下发设备；通过SPC预测质量；确保覆盖生产作业、生产管理、运营管理三环节。",
    "解决方案示范性和可推广性": "提炼[可复用方案]，归纳实施方法论，形成可被同行业借鉴的标杆案例与标准化模板。",
    "经济社会效益情况": "量化降本增效：统计成本降低率/效率提升率/库存周转率、良率提升、能耗与排放降低（参考 T/CAMS182），用数据支撑效益。",
    "后续实施计划": "制定分年度实施计划（如2025-2027），明确目标合理性、成长性与推广可行性，设定可考核里程碑。",
}
DIM_PRIORITY = {"智能制造成熟度": "P1", "信息基础建设水平": "P0", "技术应用先进性": "P0",
                "解决方案示范性和可推广性": "P2", "经济社会效益情况": "P1", "后续实施计划": "P2"}


def build_suggestions(dims_scores: dict, target_level: str) -> list:
    """对得分率偏低维度生成动作级 P0/P1/P2 建议（离线）。"""
    out = []
    for d in E.EXPERT_SCORING_DIMS:
        name = d["name"]
        score = dims_scores.get(name, 0)
        rate = score / d["max"]
        if rate < 0.6:
            out.append({
                "优先级": DIM_PRIORITY[name],
                "维度": name,
                "得分": f"{score}/{d['max']}",
                "修改方向(动作级)": DIM_TEMPLATES[name].format(mat=LEVEL_MATURITY_MIN[target_level]),
                "参考案例": "参照大连德原工业(成熟度3.55/三级)、大连融科储能(成熟度3.71/三级)改进建议风格",
                "工作量": "中等(3-5天)" if DIM_PRIORITY[name] == "P0" else "轻量/系统(视现状)",
            })
    return out


# ============================================================
# 渲染辅助
# ============================================================
def render_screening(res: dict):
    badge = {"PASS": "🟢 初筛通过", "REJECT": "🔴 拦截（REJECT）", "PENDING_EXPERT": "🟡 待专家判定"}[res["screening_result"]]
    st.markdown(f"### 筛查结论：{badge}")

    # 友好展示（不暴露原始 JSON / 内部字段名）
    fc = res.get("formality_check", {})
    bc = res.get("basic_requirement_check", {})
    hc = res.get("hard_indicator_check", {})

    st.markdown("**一、形式审查（完整性检查）**")
    fc_status = {"PASS": "✅ 通过", "FAIL": "❌ 不通过"}.get(fc.get("status", ""), "⚠️ 异常")
    st.markdown(f"- 审查结果：{fc_status}")
    missing = fc.get("missing_sections", [])
    if missing:
        st.markdown(f"- 缺失章节（{len(missing)}项）：{', '.join(missing)}")
    auth = fc.get("authenticity_commitment", "")
    if auth and auth != "完整":
        st.markdown(f"- 真实性承诺：{auth}")

    items = bc.get("checked_items", [])
    if items:
        st.markdown("**二、基础要求核查**")
        bc_status = {"PASS": "✅ 全部满足", "FAIL": "❌ 存在不满足项", "INSUFFICIENT_DATA": "⚠️ 部分数据待核实"}.get(
            bc.get("status", ""), f"状态={bc.get('status','')}")
        st.markdown(f"- 核查结论：{bc_status}")
        for it in items:
            icon = "✅" if it.get("actual_status") == "满足" else ("❌" if it.get("actual_status") == "不满足" else "⏳")
            st.markdown(f"- {icon} **{it['item_name']}**（《{it['standard_source']}》）：{it['actual_status']} — {it['evidence_text']}")

    veto = hc.get("veto_triggered", [])
    if veto:
        st.markdown("**三、目标等级一票否决**")
        for v in veto:
            st.markdown(f"- ❌ {v[0]}（{v[1]}）")

    summary = res.get("screening_summary", "")
    if summary:
        st.caption(summary)

    if res["reject_reason"]:
        st.error(f"🚫 拦截理由（附标准出处）：{res['reject_reason']}")
    if res["suggested_level_adjustment"]:
        st.warning(f"💡 建议等级调整：{res['suggested_level_adjustment']}")
    if res["pending_notes"]:
        st.info(res["pending_notes"])
    if res.get("llm_text"):
        st.subheader("🤖 LLM 结构化判定全文")
        st.markdown(res["llm_text"])
    if res["forward_to_expert"]:
        st.success("✅ 已转发专家，进入模块②内容增强标注。")


def render_enhancement(sk: dict, llm_text, target_level: str, doc_len: int):
    st.markdown("**一、基本信息**")
    s = sk["signals"]
    st.markdown(
        f"- 目标等级：{target_level} ｜ 覆盖环节：{s['covered_count']}/5（{', '.join(s['covered_environments']) or '无'}）"
        f"｜ 成熟度自评估：{s['maturity_score'] or '缺失'} ｜ 字数：{doc_len} ｜ 场景覆盖：{sk['covered_scenes']}/40"
    )
    st.markdown("**二、五大环节对照分析（原文-标准-关键词 骨架）**")
    st.table([{"环节": r["环节"], "是否覆盖": r["是否覆盖"], "匹配状态": r["状态"], "标准关键词": r["关键词"]} for r in sk["env_rows"]])
    st.markdown("**三、典型场景覆盖矩阵（40 场景）**")
    with st.expander("展开全部 40 场景覆盖情况", expanded=False):
        st.table(sk["scene_rows"])
    st.caption(f"已涉及场景 {sk['covered_scenes']}/40")
    st.markdown("**四、问题汇总（红/黄/蓝 分级）**")
    if sk["red"]:
        st.markdown("🔴 **红色（硬性不符合，必须改）**：" + "；".join(sk["red"]))
    if sk["yellow"]:
        st.markdown("🟡 **黄色（逻辑/数据不一致）**：" + "；".join(sk["yellow"]))
    if sk["blue"]:
        st.markdown("🔵 **蓝色（表述/证据不充分）**：" + "；".join(sk["blue"]))
    if not (sk["red"] or sk["yellow"] or sk["blue"]):
        st.markdown("未识别到显著问题，建议专家结合全文复核。")
    if llm_text:
        st.markdown("---")
        st.subheader("🤖 LLM 生成《申报书增强分析报告》全文")
        st.markdown(llm_text)


def render_scoring_report(dims_scores: dict, target_level: str, expert_name: str, review_date):
    total = sum(dims_scores.values())
    concl = E.conclusion_of(total)
    sugg = build_suggestions(dims_scores, target_level)
    report = f"""# 智能工厂申报书 · 专家修改建议报告

**目标等级**：{target_level}
**专家总分**：{total}/100 ｜ **结论类型**：{concl['type']}（{concl['desc']}）
**评定专家**：{expert_name or '（未署名）'} ｜ **评定日期**：{review_date}

## 一、评审结论
{concl['type']}。建议按上述结论处理。

## 二、评分明细（6 维度）
| 维度 | 满分 | 专家评分 | 得分率 | 主要扣分点 |
|------|-----|---------|-------|-----------|
""" + "\n".join(
        f"| {d['name']} | {d['max']} | {dims_scores[d['name']]} | {dims_scores[d['name']]/d['max']*100:.0f}% | 见修改建议 |"
        for d in E.EXPERT_SCORING_DIMS
    ) + f"\n| **合计** | **100** | **{total}** | | |\n"
    if sugg:
        report += "\n## 三、修改建议清单（P0/P1/P2 动作级）\n"
        for plevel in ["P0", "P1", "P2"]:
            items = [x for x in sugg if x["优先级"] == plevel]
            if items:
                report += f"\n### {plevel}（{'必须改' if plevel=='P0' else '建议改' if plevel=='P1' else '优化提升'}）\n"
                report += "| 维度 | 得分 | 修改方向(动作级) | 参考案例 | 工作量 |\n|------|-----|---------------|---------|-------|\n"
                for x in items:
                    report += f"| {x['维度']} | {x['得分']} | {x['修改方向(动作级)']} | {x['参考案例']} | {x['工作量']} |\n"
    else:
        report += "\n## 三、修改建议清单\n各维度得分率均≥60%，无强制改进项；可酌情优化表述与证据。\n"
    report += (
        "\n## 四、转线下咨询建议\n以下情况建议转接协会线下专家一对一深度辅导：特殊工艺（半导体/生物医药等）、"
        "跨区域政策差异、重大数据矛盾需现场核查、最终定稿争议。\n\n"
        f"{DISCLAIMER}"
    )
    return report, total, concl


# ============================================================
# UI
# ============================================================
# ---- 样例数据（来自 04_样例数据，含一键演示预设评分）----
_SAMPLE_ROOT = os.path.join(_ROOT, "expert_pack")
SAMPLES = {
    "华锐重工（先进级·应通过）": {
        "lv": "先进级",
        "path": os.path.join(_SAMPLE_ROOT, "1784556664650137524-sample1_先进级_华锐重工.txt"),
        "scores": {"智能制造成熟度": 18, "信息基础建设水平": 26, "技术应用先进性": 17,
                   "解决方案示范性和可推广性": 8, "经济社会效益情况": 8, "后续实施计划": 7},
    },
    "新兴机械（先进级·应拦截）": {
        "lv": "先进级",
        "path": os.path.join(_SAMPLE_ROOT, "1784556664710279767-sample2_不合格_新兴机械.txt"),
        "scores": {"智能制造成熟度": 2, "信息基础建设水平": 8, "技术应用先进性": 3,
                   "解决方案示范性和可推广性": 2, "经济社会效益情况": 5, "后续实施计划": 8},
    },
    "精密电子（基础级·应通过）": {
        "lv": "基础级",
        "path": os.path.join(_SAMPLE_ROOT, "17845566647983541-sample3_基础级_精密电子.txt"),
        "scores": {"智能制造成熟度": 10, "信息基础建设水平": 22, "技术应用先进性": 14,
                   "解决方案示范性和可推广性": 7, "经济社会效益情况": 8, "后续实施计划": 9},
    },
}

def _load_and_run(label, info):
    """载入案例并离线跑通三模块（初筛→增强→评分），结果存入 session_state（零 Key 可跑）。"""
    text = open(info["path"], encoding="utf-8").read()
    st.session_state["doc_text"] = text
    st.session_state["target_level"] = info["lv"]
    st.session_state["screen_res"] = screening(text, info["lv"])
    sk = enhancement_skeleton(text, info["lv"])
    st.session_state["enh_sk"] = sk
    st.session_state["enh_llm"] = None
    for d in E.EXPERT_SCORING_DIMS:
        st.session_state[f"score_{d['name']}"] = info["scores"][d["name"]]
    st.success(f"已载入并跑通三模块：{label}")


with st.sidebar:
    render_expert_sidebar()
    use_llm = st.checkbox("调用大模型生成完整报告（需配置接口）", value=False,
                          help="不勾选时走离线关键词引擎，开箱即用；勾选后三大模块调用真实大模型。")
    if use_llm and not is_configured():
        st.warning("尚未配置模型接口，勾选后将自动降级为离线引擎。")
    st.divider()
    st.markdown("### 📋 选择案例（自动出报告）")
    st.caption("点击案例即离线跑通初筛→增强→评分三模块，无需配置接口；也可勾选上方调用大模型。")
    for label, info in SAMPLES.items():
        if st.button(f"📋 {label}", key=f"fill_{label}"):
            _load_and_run(label, info)
    st.divider()
    st.markdown("### 🚀 一键演示（离线跑通三模块）")
    st.caption("同上：自动载入样例并连续初筛→增强→评分，无需配置接口。")
    for label, info in SAMPLES.items():
        if st.button(f"🚀 {label}", key=f"demo_{label}"):
            _load_and_run(label, info)

st.markdown(
    "将企业《智能工厂申报书》粘贴到下方，系统按专家端整合包 V3.3 三大模块依次辅助评审。"
    "**所有输出仅供专家参考，最终结论须由专家确认。**"
)

doc_text = st.text_area("申报书正文", height=240, key="doc_text",
                        placeholder="粘贴申报书全文（支持 txt 复制）… 或点左侧案例自动填入…")
with st.container():
    target_level = st.selectbox("目标申报等级", ["基础级", "先进级", "卓越级", "领航级"],
                                index=["基础级", "先进级", "卓越级", "领航级"].index(
                                    st.session_state.get("target_level", "先进级")))

use_llm_effective = use_llm and is_configured()

# ---------- ① 初步筛查 ----------
tab1, tab2, tab3 = st.tabs(["① 初步筛查", "② 内容增强标注", "③ 评分辅助与建议"])

with tab1:
    st.subheader("① 初步筛查（自动拦截明显不合格）")
    if st.button("▶ 运行初步筛查", type="primary", disabled=not doc_text.strip()):
        if doc_text.strip():
            with st.spinner("⏳ 正在初筛…"):
                res = screening(doc_text, target_level)
                if use_llm_effective:
                    res["llm_text"] = call_llm(E.SYSTEM_PROMPT + "\n\n" + E.SCREENING_PROMPT,
                                               f"目标等级：{target_level}\n\n申报书全文：\n{doc_text}",
                                               temperature=0.2, max_tokens=3000)
            st.session_state["screen_res"] = res
    res = st.session_state.get("screen_res")
    if res and res.get("target_level") == target_level:
        render_screening(res)
    elif res:
        st.caption("（上次初筛结果的目标等级与当前不一致，请重新运行）")

# ---------- ② 内容增强标注 ----------
with tab2:
    st.subheader("② 内容增强标注（《申报书增强分析报告》）")
    if st.button("▶ 生成增强分析报告", disabled=not doc_text.strip()):
        with st.spinner("⏳ 正在增强标注…"):
            sk = enhancement_skeleton(doc_text, target_level)
            llm_text = None
            if use_llm_effective:
                llm_text = call_llm(E.SYSTEM_PROMPT + "\n\n" + E.ENHANCEMENT_PROMPT + "\n\n" + E.knowledge_md(),
                                    f"目标等级：{target_level}\n\n申报书全文：\n{doc_text}",
                                    temperature=0.3, max_tokens=6000)
            st.session_state["enh_sk"] = sk
            st.session_state["enh_llm"] = llm_text
    sk = st.session_state.get("enh_sk")
    if sk:
        render_enhancement(sk, st.session_state.get("enh_llm"), target_level, len(doc_text))

# ---------- ③ 评分辅助与建议 ----------
with tab3:
    st.subheader("③ 评分辅助与建议（6 维度 100 分制）")
    st.caption("辅助专家按《先进级智能工厂评选评分表》打分；对低分维度生成 P0/P1/P2 动作级修改建议。")
    dims_scores = {}
    cols = st.columns(2)
    for i, d in enumerate(E.EXPERT_SCORING_DIMS):
        with cols[i % 2]:
            dims_scores[d["name"]] = st.number_input(
                f"{d['name']}（满分{d['max']}）", min_value=0, max_value=d["max"],
                value=0, step=1, key=f"score_{d['name']}",
                help=d["criteria"],
            )
    total = sum(dims_scores.values())
    concl = E.conclusion_of(total)
    st.markdown(f"**专家总分：{total} / 100** ｜ 结论映射：`{concl['desc']}` → **{concl['type']}**")

    expert_name = st.text_input("评定专家", "")
    review_date = st.date_input("评定日期", value=datetime.date.today())

    if st.button("▶ 生成《申报书修改建议报告》"):
        llm_text = None
        if use_llm_effective:
            with st.spinner("⏳ LLM 正在生成修改建议报告…"):
                llm_text = call_llm(
                    E.SYSTEM_PROMPT + "\n\n" + E.SCORING_PROMPT + "\n\n" + E.knowledge_md(),
                    f"目标等级：{target_level}\n专家评分：{json.dumps(dims_scores, ensure_ascii=False)}\n"
                    f"结论：{concl['type']}\n\n申报书全文：\n{doc_text[:4000]}",
                    temperature=0.3, max_tokens=6000)
        report, _, _ = render_scoring_report(dims_scores, target_level, expert_name, review_date)
        st.session_state["expert_report"] = report
        if llm_text:
            st.session_state["expert_report_llm"] = llm_text

    report = st.session_state.get("expert_report")
    if report:
        st.subheader("📋 申报书修改建议报告")
        st.markdown(report)
        if st.session_state.get("expert_report_llm"):
            st.markdown("---")
            st.subheader("🤖 LLM 生成《修改建议报告》全文")
            st.markdown(st.session_state["expert_report_llm"])

st.divider()
st.info(DISCLAIMER)
