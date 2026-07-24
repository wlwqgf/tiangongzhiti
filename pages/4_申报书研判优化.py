"""
模块④ 申报书研判与优化
移植自 D 板块 smart-factory-review-expert.md（六步预审：信息抽取→合规检查→一致性校验→证据评估→三级标记→诊断报告）。
知识依据来自 core.knowledge 生成的政策标准库与历史案例库。

交互约定（对齐模块①）：
- 选择案例「之前」，申报书正文为空；
- 在侧边栏选择案例工厂后，自动填入该工厂申报书全文（不自动出报告）；
- 再点「开始预审诊断」才生成报告：已配置接口 -> 大模型；未配置 -> 离线规则引擎（零 Key）。
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.llm import call_llm, DISCLAIMER, is_configured
from core.knowledge import policy_standards_md, historical_cases_md, LEVEL_THRESHOLDS
from core import demo
from core.theme import apply_theme, render_enterprise_sidebar

st.set_page_config(page_title="④申报书研判与优化", layout="wide")
apply_theme()
st.markdown("<h1 style='font-size:1.55rem'>🔍 ④ 申报书研判与优化</h1>", unsafe_allow_html=True)
st.caption("六步 AI 预审 · 合规/一致性/证据评估 · 🔴🟡🔵 三级标记 · 转人工建议")

PROMPT_PATH = os.path.join(_ROOT, "knowledge", "expert_review_prompt.md")


@st.cache_resource
def load_review_prompt() -> str:
    with open(PROMPT_PATH, "r", encoding="utf-8") as f:
        return f.read()


review_prompt = load_review_prompt()

st.session_state.setdefault("doc_text", "")
st.session_state.setdefault("rev_level", "先进级")
st.session_state.setdefault("rev_filled_case", None)


def fill_submission(case_key):
    text = open(demo.CASES[case_key]["submission"], encoding="utf-8").read()
    st.session_state["doc_text"] = text
    st.session_state["rev_level"] = demo.CASES[case_key]["level"]
    st.session_state["rev_filled_case"] = case_key
    # 选择案例后离线自动生成诊断报告（零 Key 可跑，无需点击按钮）
    st.session_state["demo_review"] = demo.build_review_report(text, demo.CASES[case_key]["level"])


tab1, tab2 = st.tabs(["🔍 申报书研判诊断", "📐 等级指标对照"])

# ---------------- 侧边栏：选择案例（仅回填正文） ----------------
with st.sidebar:
    render_enterprise_sidebar()
    st.markdown("### 📋 选择案例（自动填入正文）")
    st.caption("点击案例后，申报书全文自动填入下方文本框；再点「开始预审诊断」即可出报告（离线·零 Key）。")
    for _key, _case in demo.CASES.items():
        if st.button(f"📋 {_key}", key=f"demo4_{_key}", help=_case["label"]):
            fill_submission(_key)
            st.success(f"已载入：{_case['label']}，请点「开始预审诊断」")

with tab1:
    st.markdown(
        "将您的《智能工厂申报书》草稿粘贴到下方（支持文档正文）。系统将按 6 个步骤执行预审，"
        "输出含 🔴红色(硬伤)/🟡黄色(矛盾)/🔵蓝色(建议) 三级标记的结构化诊断报告。"
    )
    if st.session_state.get("rev_filled_case"):
        st.info(f"✅ 已载入案例「{st.session_state['rev_filled_case']}」，申报书正文已自动填入。请点击「开始预审诊断」。")

    uploaded = st.file_uploader("（可选）上传申报书文本 .txt", type=["txt"])
    doc_text = st.text_area("申报书正文", height=320, key="doc_text",
                            placeholder="粘贴申报书全文，或上传 .txt 文件，或点左侧案例自动填入…")

    if uploaded is not None:
        content = uploaded.read().decode("utf-8", errors="ignore")
        st.session_state["doc_text"] = content
        doc_text = content

    rev_level = st.selectbox("目标申报等级", ["基础级", "先进级", "卓越级", "领航级"],
                             key="rev_level")

    if st.button("🚀 开始预审诊断") and doc_text.strip():
        if is_configured():
            knowledge_block = (
                "\n\n# 本次分析可用的知识依据（必须优先引用）\n\n"
                + policy_standards_md() + "\n\n" + historical_cases_md()
            )
            system_prompt = review_prompt + knowledge_block
            with st.spinner("⏳ 正在执行六步预审（信息抽取→合规检查→一致性校验→证据评估→标记→诊断）..."):
                report = call_llm(system_prompt, doc_text, temperature=0.2, max_tokens=8000)
        else:
            st.caption("⚙️ 未配置模型接口，已用离线规则引擎执行六步预审（零 Key 可跑）；如需 AI 深度诊断请在配置 OPENAI_API_KEY。")
            report = demo.build_review_report(doc_text, rev_level)
        st.session_state["demo_review"] = report

    # 选择案例或点击诊断后，自动展示报告（离线零 Key 也能出报告）
    if st.session_state.get("demo_review"):
        st.subheader("📋 智能工厂申报书诊断报告")
        st.markdown(st.session_state["demo_review"])
        st.caption("本诊断为 AI 预审，不替代官方评审；复杂问题请转接协会线下专家。")

with tab2:
    st.caption("各等级硬性指标阈值（依据《智能工厂梯度培育要素条件（2025年版）》）。点击展开查看。")
    with st.expander("📐 各等级硬性指标阈值", expanded=False):
        rows = {
            "关键工序数控化率": "cnc_rate",
            "关键设备联网率": "network_rate",
            "年营业收入(万元)": "revenue_min",
            "研发投入占比": "rd_ratio",
            "成熟度(GB/T 39116)": "maturity_min",
        }
        md = ["| 指标 | 基础级 | 先进级 | 卓越级 | 领航级 |", "|------|------|------|------|------|"]
        for label, key in rows.items():
            suffix = "%" if "率" in label else ""
            cells = " | ".join(str(LEVEL_THRESHOLDS[lv][key]) + suffix for lv in ["基础级", "先进级", "卓越级", "领航级"])
            md.append(f"| {label} | {cells} |")
        st.markdown("\n".join(md))

st.divider()
st.markdown("#### 📞 需要更深入的线下服务？")
st.caption("若研判报告无法完全满足您的需求（如现场诊断、申报书代写、深度改造规划），可提交需求工单，协会线下专家将一对一对接。")
st.page_link("pages/6_线下服务对接.py", label="提交智能需求工单 →", icon="📞", use_container_width=True)

st.divider()
st.markdown("#### 🏛️ 官方智能工厂申报通道")
st.caption("完成本模块的研判与优化后，可前往工业和信息化部官方智能工厂申报系统提交正式申报。")
st.link_button("前往官方智能工厂申报系统 ↗", "https://adminconsole.miit-imps.com/", use_container_width=True)

st.divider()
# 2026-07-24: 删除模块四结尾的 6 个省级/市级站点链接区块
# 原因：用户指出这些不是报名入口，已统一收录在 knowledge/policy_library_index.json
#       智能体知识库（页面 9_政策文件库）里；模块四仅保留上方 MIIT 官方申报通道
st.info(DISCLAIMER)
