"""
模块② 政策标准互动问答（离线可运行）
移植自 B 板块 agent-core.js 的「意图识别 + 回答生成」引擎，用 Python 重写，
数据来自 core.knowledge（政策条款 / 案例 / 奖补 / 40 场景）。
"""
import os
import sys
import re

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.knowledge import (
    POLICIES, CASES, SUBSIDY, TYPICAL_SCENES, LEVEL_THRESHOLDS,
    search_policy, find_cases, get_subsidy,
)
from core.llm import call_llm, is_configured, DISCLAIMER
from core import demo
from core.theme import apply_theme, render_enterprise_sidebar

st.set_page_config(page_title="②政策标准互动问答", layout="wide")
apply_theme()
st.markdown("<h1 style='font-size:1.55rem'>💬 ② 政策标准互动问答</h1>", unsafe_allow_html=True)
st.caption("离线知识库驱动 · 等级对标 / 指标查询 / 奖补测算 / 流程指引 / 政策解读 / 案例参考")


# ---------------- 意图识别（评分制：命中词最多的意图胜出） ----------------
def classify_intent(text: str) -> str:
    t = text.lower()
    rules = {
        "subsidy_calc": ["补贴", "奖补", "奖励", "资金", "多少钱", "补助", "贴息", "扶持", "财政", "小巨人", "专精特新"],
        "grade_match": ["适合申报", "申报哪个", "哪个等级", "对标", "等级", "该报", "报哪", "能报", "报几级",
                        "申报等级", "推荐等级", "建议报", "申报先进级", "申报卓越级", "申报基础级", "申报领航级"],
        "index_query": ["指标", "联网率", "数控化", "营收", "专利", "成熟度", "门槛", "要求", "占比",
                        "标准", "条件", "设备", "覆盖率", "自动化", "数字化率", "研发投入"],
        "process_guide": ["流程", "怎么申报", "步骤", "材料", "时间", "窗口", "如何申报", "程序", "怎么报",
                          "申报书", "认定", "评审", "怎么准备"],
        "case_ref": ["案例", "例子", "别人", "华锐", "中集", "企业", "参照", "参考", "同行", "示范", "标杆"],
        "policy_explain": ["政策", "办法", "要素条件", "规定", "文件", "解读", "依据", "智能工厂", "梯度培育", "什么是"],
    }
    best, best_score = "unknown", 0
    for intent, kws in rules.items():
        score = sum(1 for kw in kws if kw in t)
        if score > best_score:
            best, best_score = intent, score
    return best


def extract_info(text: str):
    info = {}
    m = re.search(r"营收[^\d]*?(\d+(?:\.\d+)?)\s*(亿|万)", text)
    if m:
        val = float(m.group(1))
        unit = m.group(2)
        info["revenue"] = int(val * 10000 if unit == "亿" else val)
    for ind in ["装备制造", "汽车", "电子", "化工", "医药", "新材料", "食品", "金属", "通用设备", "专用设备"]:
        if ind in text:
            info["industry"] = ind
            break
    return info


# ---------------- 回答生成 ----------------
def resp_grade_match(info):
    lines = ["### 🎯 等级对标建议\n"]
    if "revenue" not in info:
        return "请补充企业**年营业收入**与**所属行业**，我来为您对标可申报等级。例如：「我们是装备制造，年营收约 1.5 亿」。"
    rev = info["revenue"]
    if rev < 5000:
        fit = "基础级（先进级起营收门槛约 5000 万，您暂未达，建议从基础级起步）"
    elif rev < 20000:
        fit = "先进级（营收已达 5000 万门槛；卓越级需≥2 亿）"
    elif rev < 50000:
        fit = "卓越级（营收已达 2 亿门槛；领航级需≥5 亿）"
    else:
        fit = "领航级（营收达 5 亿门槛，可冲击最高等级）"
    lines.append(f"根据营收 **{rev} 万元**，初步对标：**{fit}**。")
    lines.append("\n> 注意：营收只是维度之一。最终等级还需满足数控化率、联网率、成熟度、研发占比等硬性指标"
                 "（见「指标查询」），且须**逐级申报、不可跳级**。")
    lines.append("\n建议：先完成「①企业画像与等级推荐」获取六维度评分与冲稳保概率。")
    return "\n".join(lines)


def resp_index_query():
    lines = ["### 📐 各等级硬性指标阈值（要点）\n"]
    lines.append("| 指标 | 基础级 | 先进级 | 卓越级 | 领航级 |")
    lines.append("|------|------|------|------|------|")
    rows = {
        "关键工序数控化率": "cnc_rate",
        "关键设备联网率": "network_rate",
        "年营业收入(万元)": "revenue_min",
        "研发投入占比": "rd_ratio",
        "成熟度(GB/T 39116)": "maturity_min",
    }
    for label, key in rows.items():
        suffix = "%" if "率" in label else ""
        cells = " | ".join(str(LEVEL_THRESHOLDS[lv][key]) + suffix for lv in ["基础级", "先进级", "卓越级", "领航级"])
        lines.append(f"| {label} | {cells} |")
    lines.append("\n> 来源：《智能工厂梯度培育要素条件（2025年版）》。完整条款请在「①画像」与「④研判」中对照。")
    return "\n".join(lines)


def resp_subsidy_calc(text):
    lines = ["### 💰 奖补测算（大连市 / 辽宁省，示意）\n"]
    lines.append("| 等级 | 补贴比例 | 市级/国家级上限 | 省级配套上限 |")
    lines.append("|------|------|------|------|")
    for lv in ["基础级", "先进级", "卓越级", "领航级"]:
        s = get_subsidy(lv)
        rate = f"{int(s['rate']*100)}%" if s["rate"] else "资格型"
        lines.append(f"| {lv} | {rate} | {s['cap']}万 | {s['province_cap']}万 |")
    lines.append("\n- 数字化车间：不超过 **50 万**（惠企政策30条第2条）")
    lines.append("- 国家级专精特新\"小巨人\"：**50 万**；省级专精特新：**30 万**（第1条）")
    inv = re.search(r"投资[^\d]*?(\d[\d,]*)\s*万", text)
    if inv:
        inv_v = int(inv.group(1).replace(",", ""))
        lines.append(f"\n按您投资 **{inv_v} 万** 估算：")
        for lv in ["先进级", "卓越级", "领航级"]:
            s = get_subsidy(lv)
            amt = min(inv_v * s["rate"], s["cap"])
            lines.append(f"- {lv}：约 **{amt:.0f} 万**（投资×{int(s['rate']*100)}%，封顶 {s['cap']}万）")
    else:
        lines.append("\n如需按投资额测算，请补充「智能化改造投资额 XX 万」与「目标等级」。")
    lines.append("\n> 补贴金额为示意性估算，以当年财政预算与最新政策为准。")
    return "\n".join(lines)


def resp_process_guide():
    a = POLICIES["管理办法"]["articles"]
    lines = ["### 📝 申报流程指引\n"]
    lines.append(a["评审流程"])
    lines.append(f"\n- 等级体系：{a['等级体系']}")
    lines.append(f"- 2026 预通知：{a['2026预通知']}")
    lines.append("\n> 提示：基础级由市级认定；先进级及以上由省级/工信部认定，一般需先获低一级认定。")
    return "\n".join(lines)


def resp_case_ref(info):
    ind = info.get("industry")
    cases = find_cases(ind)
    lines = ["### 📚 脱敏案例参考\n"]
    for c in cases:
        lines.append(f"- **[{c['level']}] {c['company']}**（{c['result']}）：{c['lesson']}")
    lines.append("\n> 案例为结构化参照，引用时请说明「参照同类企业成功做法」。")
    return "\n".join(lines)


def resp_policy_explain():
    a = POLICIES["管理办法"]["articles"]
    lines = ["### 📖 政策要点解读\n"]
    lines.append(f"- **等级体系**：{a['等级体系']}")
    lines.append(f"- **申报条件**：{a['申报条件']}")
    lines.append(f"- **复核管理**：{a['复核管理']}")
    return "\n".join(lines)


def compose(user_text: str):
    info = extract_info(user_text)
    intent = classify_intent(user_text)
    if intent == "grade_match":
        return resp_grade_match(info), ["我们营收 8000 万，适合报哪个等级？", "年营收 3 亿能报卓越级吗？"]
    if intent == "index_query":
        return resp_index_query(), ["关键设备联网率要求多少？", "先进级的营收门槛是多少？"]
    if intent == "subsidy_calc":
        return resp_subsidy_calc(user_text), ["投资 2000 万报卓越级能补多少？", "数字化车间补贴多少？"]
    if intent == "process_guide":
        return resp_process_guide(), ["申报流程是什么？", "2026 年申报窗口？"]
    if intent == "case_ref":
        return resp_case_ref(info), ["有没有装备制造的案例？", "先进级有通过的例子吗？"]
    if intent == "policy_explain":
        return resp_policy_explain(), ["智能工厂分几个等级？", "复核多久一次？"]
    return ("我可以帮您解答：①适合申报哪个等级 ②各等级硬性指标 ③奖补测算 ④申报流程 ⑤政策解读 ⑥案例参考。"
            "\n请直接描述您的问题，例如「我们是汽车零部件，年营收 1 亿，适合报哪级？」",
            ["适合申报哪个等级？", "各等级硬性指标？", "奖补怎么算？"])


# ---------------- 界面：选项卡 ----------------
tab1, tab2 = st.tabs(["💬 政策问答", "📚 政策知识速览"])

# ---------------- 侧边栏：选择案例（离线问答） + 大模型开关 ----------------
with st.sidebar:
    render_enterprise_sidebar()
    st.markdown("### 📋 案例演示（离线问答）")
    st.caption("点击后自动注入该案例的代表性问题与离线回答，演示用三个工厂做政策咨询（无需配置接口）。")
    for _key, _case in demo.CASES.items():
        if st.button(f"📋 {_key}", key=f"demo2_{_key}"):
            f = _case["form"]
            q = (f"我们是{f.get('所属行业','')}企业，年营业收入约{f.get('年营业收入',0)}万元，"
                 f"关键设备数控化率{f.get('关键设备数控化率',0)}%、联网率{f.get('关键设备联网率',0)}%，"
                 f"智能制造能力成熟度{f.get('智能制造能力成熟度评估等级','未评估')}，"
                 f"已部署{f.get('现有业务系统','')}。请问我们适合申报哪个等级？")
            a, fq = compose(q)
            st.session_state["qa_history"].append(("user", q))
            st.session_state["qa_history"].append(("assistant", a))
            st.session_state["pending_followups"] = fq
            st.rerun()
    st.divider()
    use_llm = st.checkbox("调用大模型深度回答（需配置接口）", value=False,
                          disabled=not is_configured())

with tab1:
    if "qa_history" not in st.session_state:
        st.session_state["qa_history"] = [
            ("assistant", "您好，我是天工智梯政策问答助手。请问您想了解智能工厂申报的哪方面？")
        ]
    if "pending_followups" not in st.session_state:
        st.session_state["pending_followups"] = []

    for role, msg in st.session_state["qa_history"]:
        with st.chat_message(role):
            st.markdown(msg)

    # 可继续追问（位于 chat_input 之前，确保始终可见、可点击）
    followups = st.session_state.get("pending_followups", [])
    if followups:
        st.caption("💡 可继续追问：")
        for i, fq in enumerate(followups):
            if st.button(fq, key=f"fq_{i}"):
                st.session_state["qa_history"].append(("user", fq))
                with st.chat_message("user"):
                    st.markdown(fq)
                with st.chat_message("assistant"):
                    ans2, f2 = compose(fq)
                    st.markdown(ans2)
                    st.session_state["qa_history"].append(("assistant", ans2))
                    st.session_state["pending_followups"] = f2

    if prompt := st.chat_input("输入您的问题，例如：我们是装备制造，年营收1.5亿，适合报哪个等级？"):
        st.session_state["qa_history"].append(("user", prompt))
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            thinking = st.empty()
            thinking.markdown("⏳ 正在分析意图并检索知识库...")
            if use_llm and is_configured():
                kb = "\n".join([f"- {k}: {v}" for k, v in LEVEL_THRESHOLDS.items()])
                sys_prompt = (
                    "你是大连市智能制造产业协会的智能工厂政策问答助手，依据《要素条件(2025版)》《惠企政策30条》"
                    "等回答，严禁编造。知识库等级阈值摘要：\n" + kb
                )
                answer = call_llm(sys_prompt, prompt, temperature=0.2)
                followups = []
            else:
                answer, followups = compose(prompt)
            thinking.markdown(answer)
            st.session_state["qa_history"].append(("assistant", answer))
            st.session_state["pending_followups"] = followups
            st.rerun()  # 重新渲染，使可见位置的「可继续追问」按钮生效

with tab2:
    st.caption("点击展开对应政策知识表（依据《智能工厂梯度培育要素条件（2025年版）》等）。")
    with st.expander("📐 各等级硬性指标阈值", expanded=False):
        st.markdown(resp_index_query())
    with st.expander("💰 各等级奖补测算口径", expanded=False):
        st.markdown(resp_subsidy_calc(""))
    with st.expander("📖 政策要点解读", expanded=False):
        st.markdown(resp_policy_explain())
    with st.expander("📝 申报流程指引", expanded=False):
        st.markdown(resp_process_guide())

st.divider()
st.markdown("#### 📞 需要更深入的线下服务？")
st.caption("若政策问答无法完全解决您的问题（如现场诊断、申报书代写、深度改造规划），可提交需求工单，协会线下专家将一对一对接。")
st.page_link("pages/6_线下服务对接.py", label="提交智能需求工单 →", icon="📞", use_container_width=True)

st.info(DISCLAIMER)
