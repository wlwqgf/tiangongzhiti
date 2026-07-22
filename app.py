"""
天工智梯 · 智能工厂申报全流程 AI 智能体系统 — 统一入口

运行：  streamlit run app.py
依赖：  pip install -r requirements.txt，并在 .env 中配置模型接口（未配置亦可离线演示）
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.llm import is_configured, DISCLAIMER
from core.theme import apply_theme

st.set_page_config(
    page_title="天工智梯 · 智能工厂申报 AI 专家顾问",
    page_icon="🏭",
    layout="wide",
)
apply_theme()

# ---------- 侧边栏（全局） ----------
with st.sidebar:
    st.title("🏭 天工智梯")
    st.caption("智能工厂申报全流程 AI 智能体系统")
    st.divider()
    if is_configured():
        st.success("✅ 模型接口已配置")
    else:
        st.warning("⚠️ 未检测到模型配置")
        st.caption("在 `.env` 中填写 OPENAI_API_KEY / OPENAI_BASE_URL 后重启，"
                   "「政策标准问答」可离线使用，其余模块需接口方可生成报告。")
    st.divider()
    st.caption("大连市智能制造产业协会 · AI 专家顾问")

# ---------- 落地页 ----------
st.markdown(
    "<h1 style='font-size:1.9rem;margin-bottom:.2rem'>🏭 天工智梯</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div style='font-size:1.05rem;color:#9fb3d6;margin-bottom:1.2rem'>"
    "智能工厂申报全流程 · AI 专家顾问系统</div>",
    unsafe_allow_html=True,
)
st.markdown(
    "面向拟申报**智能工厂梯度培育**（基础级→先进级→卓越级→领航级）的制造企业，"
    "提供从**自测画像、政策问答、大纲生成、申报书研判**到**专家评定反馈**的"
    "一站式 AI 辅助。定位为「线上引流 + 线下专家交付」的辅导工具，输出**指导性意见**而非权威结论。"
)

st.divider()

# ---------- 首页专属：双端入口大卡片按钮样式 ----------
st.markdown("""
<style>
/* 首页主内容区的 secondary 按钮 → 大卡片（首页仅双端入口2个） */
section[data-testid="stMain"] button[data-testid="stBaseButton-secondary"]{
  min-height:200px !important;
  padding:1.8rem 1rem !important;
  background:var(--glass) !important;
  border:1px solid var(--border) !important;
  border-radius:16px !important;
  backdrop-filter:blur(6px);
  box-shadow:0 0 18px rgba(34,211,238,0.18);
  font-size:0.95rem !important;
  line-height:1.7 !important;
  white-space:pre-line !important;
  transition:all .2s ease;
}
section[data-testid="stMain"] button[data-testid="stBaseButton-secondary"]:hover{
  border-color:var(--cyan) !important;
  box-shadow:0 0 28px rgba(34,211,238,0.5) !important;
  transform:translateY(-3px);
}
</style>
""", unsafe_allow_html=True)

# ---------- 双端入口（企业端 / 专家端） ----------
st.subheader("👤 请选择您的角色")

# 大卡片按钮：点击直接跳转（无额外小按钮）
col1, col2 = st.columns(2, gap="large")

with col1:
    if st.button("🏢\n\n企业端\n面向制造业企业 · 自测画像 / 政策问答 / 大纲生成 / 申报书研判",
                 key="ent_entry", use_container_width=True, help="点击进入企业端"):
        st.switch_page("pages/1_企业画像与等级推荐.py")

with col2:
    if st.button("🧑‍⚖️\n\n专家端\n面向评审专家 · 初筛 / 增强标注 / 评分辅助与建议",
                 key="exp_entry", use_container_width=True, help="点击进入专家端"):
        st.switch_page("pages/5_专家评定反馈.py")

# ---------- 深度服务引流入口 ----------
st.markdown(
    "<div style='text-align:center;margin:1rem 0 .3rem;color:#9fb3d6;font-size:.9rem'>"
    "━━━ AI 未能满足您的深度需求？━━━</div>",
    unsafe_allow_html=True,
)
st.page_link("pages/6_线下服务对接.py", label="📞 提交智能需求工单 · 对接协会线下专家", icon="📞", use_container_width=True)

st.divider()

# ---------- 使用前须知（点击展开） ----------
with st.expander("🧭 使用前须知 / 免责声明", expanded=False):
    st.markdown(
        "- **四级梯度、逐级申报**：基础级→先进级→卓越级→领航级，原则上不可跳级，跳级面临一票否决。\n"
        "- **数据真实**：所有建议基于您填报的数据，缺失项将标注，不代为编造。\n"
        "- **线下交付闭环**：AI 给出初判与建议，复杂问题转接协会线下专家一对一辅导。\n"
    )
    st.info(DISCLAIMER)
