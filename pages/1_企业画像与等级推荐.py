"""
模块① 企业画像与等级推荐 + 改造路径规划与成本估算
移植自 A 板块（app.py + prompts.py），统一调用 core.llm / core.a_prompts

交互约定（按用户要求）：
- 选择案例「之前」，企业基础信息表单全部为空，无任何预填内容；
- 在侧边栏选择案例工厂后，表单自动填入该工厂信息（不自动出报告）；
- 再点「生成画像与等级推荐」才生成报告：
    已配置模型接口 -> 调用大模型；未配置 -> 离线规则引擎模拟生成（零 Key 可跑）。
"""
import os
import sys
import datetime

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.llm import call_llm, DISCLAIMER, is_configured
from core.a_prompts import AGENT_PROFILE_PROMPT, AGENT_UPGRADE_PROMPT
from core import demo
from core.theme import apply_theme, render_enterprise_sidebar

st.set_page_config(page_title="①企业画像与等级推荐", layout="wide")
apply_theme()
st.markdown("<h1 style='font-size:1.55rem'>📊 ① 企业画像与等级推荐</h1>", unsafe_allow_html=True)
st.caption("六维度评分 · 四级达标度评估 · 冲稳保概率模型 · 改造路径规划与成本估算")

# ============================================================
# 表单字段：session_state 键 + 初始空默认值
# ============================================================
SYSTEM_OPTS = ["ERP", "MES", "PLM", "SCM", "QMS", "EMS", "WMS", "CRM", "CAD/CAE"]

FORM_DEFAULTS = {
    # 企业基础信息
    "f_name": "", "f_industry": "",
    "f_revenue": 0, "f_employees": 0,
    "f_is_high_tech": "否", "f_is_specialized": "否",
    "f_has_cert": "否", "f_has_accident": "无",
    # 装备与自动化
    "f_total_equip": 0, "f_networked": 0, "f_cnc": 0,
    "f_total_process": 0, "f_auto_process": 0, "f_collect_process": 0,
    # 软件与系统
    "f_systems": [],
    "f_has_design_tool": "否", "f_has_aps": "否", "f_has_qms": "否",
    "f_has_ems": "否", "f_has_ehs": "否", "f_integrated_systems": 0,
    # 互联互通
    "f_has_dashboard": "否", "f_has_supply_chain": "否",
    "f_has_value_chain": "否", "f_integration_level": "低",
    # 研发与创新
    "f_rd_ratio": 0.0, "f_patent_count": 0, "f_has_simulation": "否",
    "f_ai_scenarios": 0, "f_ai_coverage": 0.0,
    # 绩效与认证
    "f_maturity": "未评估", "f_integration_rating": "未贯标",
    "f_invest_3y": 0, "f_labor_productivity": 0.0, "f_oee": 0.0,
}

# session_state 键 -> demo.CASES[..]["form"] 的中文键（用于回填）
CASE_MAP = {
    "f_name": "企业名称", "f_industry": "所属行业",
    "f_revenue": "年营业收入", "f_employees": "员工人数",
    "f_is_high_tech": "是否高新技术企业", "f_is_specialized": "是否专精特新企业",
    "f_has_cert": "是否已有数字化车间/智能工厂认证", "f_has_accident": "近三年有无安全/环保重大事故",
    "f_total_equip": "关键设备总数", "f_networked": "已联网关键设备数", "f_cnc": "已数控化关键设备数",
    "f_total_process": "主要生产工序总数", "f_auto_process": "已实现自动化生产工序数", "f_collect_process": "已实现数据采集工序数",
    "f_systems": "现有业务系统",
    "f_has_design_tool": "是否具备研发设计数字化工具", "f_has_aps": "是否具备生产计划排程系统",
    "f_has_qms": "是否具备质量追溯系统", "f_has_ems": "是否具备能源管理系统",
    "f_has_ehs": "是否具备安全环保数字化系统", "f_integrated_systems": "已打通数据集成的业务系统数量",
    "f_has_dashboard": "是否具备跨系统数据看板", "f_has_supply_chain": "供应链协同系统是否打通",
    "f_has_value_chain": "是否具备全价值链数据协同", "f_integration_level": "系统间数据集成贯通程度",
    "f_rd_ratio": "研发投入占比", "f_patent_count": "专利数量", "f_has_simulation": "是否开展产品/工艺数字化仿真",
    "f_ai_scenarios": "AI应用场景数量", "f_ai_coverage": "AI应用覆盖比例",
    "f_maturity": "智能制造能力成熟度评估等级", "f_integration_rating": "两化融合贯标等级",
    "f_invest_3y": "近三年智能化改造累计投入", "f_labor_productivity": "全员劳动生产率", "f_oee": "关键设备综合效率 OEE",
}


def init_state():
    for _k, _v in FORM_DEFAULTS.items():
        st.session_state.setdefault(_k, _v)
    st.session_state.setdefault("profile_report", None)
    st.session_state.setdefault("user_data", None)
    st.session_state.setdefault("selected_case", None)


def load_case_into_form(case_key):
    """点击案例后，把该工厂数据回填进表单（不自动生成报告）。"""
    form = demo.CASES[case_key]["form"]
    for fk, cn_key in CASE_MAP.items():
        if fk == "f_systems":
            raw = form.get("现有业务系统", "")
            if isinstance(raw, str) and raw.strip():
                st.session_state[fk] = [s.strip() for s in raw.split(",") if s.strip() in SYSTEM_OPTS]
            else:
                st.session_state[fk] = []
            continue
        val = form.get(cn_key)
        if val is None:
            continue
        default = FORM_DEFAULTS[fk]
        if isinstance(default, float):
            try:
                st.session_state[fk] = float(val)
            except (TypeError, ValueError):
                pass
        elif isinstance(default, int):
            try:
                st.session_state[fk] = int(val)
            except (TypeError, ValueError):
                pass
        else:
            st.session_state[fk] = val
    # 清空旧报告，等待用户点「生成画像与等级推荐」
    st.session_state["profile_report"] = None
    st.session_state["selected_case"] = case_key


init_state()

# ---------------- 侧边栏 ----------------
with st.sidebar:
    render_enterprise_sidebar()
    st.markdown("### 📋 选择案例（自动填入表单）")
    st.caption("点击案例后，企业基础信息自动填入下方表单；再点「生成画像与等级推荐」即可出报告（离线·零 Key）。")
    for _key, _case in demo.CASES.items():
        if st.button(f"📋 {_key}", key=f"demo1_{_key}", help=_case["label"]):
            load_case_into_form(_key)
            st.success(f"已载入：{_case['label']}，请点「生成画像与等级推荐」")

# ---------------- 选项卡：分步 / 折叠 ----------------
tab1, tab2 = st.tabs(["① 企业数据填报与画像", "② 升级改造路径规划"])

with tab1:
    if st.session_state.get("selected_case"):
        st.info(f"✅ 已载入案例「{st.session_state['selected_case']}」，表单已自动填入。请展开下方分区填写/核对，再点「生成画像与等级推荐」生成报告。")

    with st.form("enterprise_form"):
        with st.expander("📋 企业基础信息", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("企业名称", key="f_name")
                industry = st.text_input("所属行业", key="f_industry")
                revenue = st.number_input("年营业收入（万元）", min_value=0, step=1, key="f_revenue")
                employees = st.number_input("员工人数", min_value=0, step=1, key="f_employees")
            with c2:
                is_high_tech = st.selectbox("是否高新技术企业", ["是", "否"], key="f_is_high_tech")
                is_specialized = st.selectbox("是否专精特新企业", ["是", "否"], key="f_is_specialized")
                has_cert = st.selectbox("是否已有数字化车间/智能工厂认证", ["是", "否"], key="f_has_cert")
                has_accident = st.selectbox("近三年有无安全/环保重大事故", ["无", "有"], key="f_has_accident")

        with st.expander("⚙️ 装备与自动化水平", expanded=False):
            c1, c2 = st.columns(2)
            with c1:
                total_equip = st.number_input("关键设备总数", min_value=0, step=1, key="f_total_equip")
                networked = st.number_input("已联网关键设备数", min_value=0, step=1, key="f_networked")
                cnc = st.number_input("已数控化关键设备数", min_value=0, step=1, key="f_cnc")
            with c2:
                total_process = st.number_input("主要生产工序总数", min_value=0, step=1, key="f_total_process")
                auto_process = st.number_input("已实现自动化生产工序数", min_value=0, step=1, key="f_auto_process")
                collect_process = st.number_input("已实现数据采集工序数", min_value=0, step=1, key="f_collect_process")

        with st.expander("💻 软件与系统覆盖", expanded=False):
            systems = st.multiselect("现有业务系统（可多选）", SYSTEM_OPTS, key="f_systems")
            has_design_tool = st.selectbox("是否具备研发设计数字化工具", ["是", "否"], key="f_has_design_tool")
            has_aps = st.selectbox("是否具备生产计划排程系统", ["是", "否"], key="f_has_aps")
            has_qms = st.selectbox("是否具备质量追溯系统", ["是", "否"], key="f_has_qms")
            has_ems = st.selectbox("是否具备能源管理系统", ["是", "否"], key="f_has_ems")
            has_ehs = st.selectbox("是否具备安全环保数字化系统", ["是", "否"], key="f_has_ehs")
            integrated_systems = st.number_input("已打通数据集成的业务系统数量", min_value=0, step=1, key="f_integrated_systems")

        with st.expander("🔗 互联互通与数据协同", expanded=False):
            has_dashboard = st.selectbox("是否具备跨系统数据看板", ["是", "否"], key="f_has_dashboard")
            has_supply_chain = st.selectbox("供应链协同系统是否打通", ["是", "否"], key="f_has_supply_chain")
            has_value_chain = st.selectbox("是否具备全价值链数据协同", ["是", "否"], key="f_has_value_chain")
            integration_level = st.selectbox("系统间数据集成贯通程度", ["低", "中", "高"], key="f_integration_level")

        with st.expander("🔬 研发与创新能力", expanded=False):
            rd_ratio = st.number_input("研发投入占比（%）", min_value=0.0, max_value=100.0, step=0.1, format="%.1f", key="f_rd_ratio")
            patent_count = st.number_input("专利数量", min_value=0, step=1, key="f_patent_count")
            has_simulation = st.selectbox("是否开展产品/工艺数字化仿真", ["是", "否"], key="f_has_simulation")
            ai_scenarios = st.number_input("AI应用场景数量", min_value=0, step=1, key="f_ai_scenarios")
            ai_coverage = st.number_input("AI应用覆盖比例（%）", min_value=0.0, max_value=100.0, step=0.1, format="%.1f", key="f_ai_coverage")

        with st.expander("📊 绩效与认证", expanded=False):
            maturity = st.selectbox("智能制造能力成熟度评估等级", ["未评估", "一级", "二级", "三级", "四级", "五级"], key="f_maturity")
            integration_rating = st.selectbox("两化融合贯标等级", ["未贯标", "A", "AA", "AAA"], key="f_integration_rating")
            invest_3y = st.number_input("近三年智能化改造累计投入（万元）", min_value=0, step=1, key="f_invest_3y")
            labor_productivity = st.number_input("全员劳动生产率（万元/人/年）", min_value=0.0, step=0.1, format="%.1f", key="f_labor_productivity")
            oee = st.number_input("关键设备综合效率 OEE（%）", min_value=0.0, max_value=100.0, step=0.1, format="%.1f", key="f_oee")

        submitted = st.form_submit_button("🚀 生成画像与等级推荐")

    if submitted:
        networking_rate = (networked / total_equip * 100) if total_equip else 0
        cnc_rate = (cnc / total_equip * 100) if total_equip else 0
        auto_rate = (auto_process / total_process * 100) if total_process else 0
        collect_rate = (collect_process / total_process * 100) if total_process else 0

        user_data = {
            "企业名称": name, "所属行业": industry, "年营业收入": revenue, "员工人数": employees,
            "是否高新技术企业": is_high_tech, "是否专精特新企业": is_specialized,
            "是否已有数字化车间/智能工厂认证": has_cert, "近三年有无安全/环保重大事故": has_accident,
            "关键设备总数": total_equip, "已联网关键设备数": networked, "已数控化关键设备数": cnc,
            "主要生产工序总数": total_process, "已实现自动化生产工序数": auto_process, "已实现数据采集工序数": collect_process,
            "关键设备联网率": round(networking_rate, 2), "关键设备数控化率": round(cnc_rate, 2),
            "生产工序自动化率": round(auto_rate, 2), "生产工序数据采集率": round(collect_rate, 2),
            "现有业务系统": ", ".join(systems), "系统覆盖数量": len(systems),
            "是否具备研发设计数字化工具": has_design_tool, "是否具备生产计划排程系统": has_aps,
            "是否具备质量追溯系统": has_qms, "是否具备能源管理系统": has_ems,
            "是否具备安全环保数字化系统": has_ehs, "已打通数据集成的业务系统数量": integrated_systems,
            "是否具备跨系统数据看板": has_dashboard, "供应链协同系统是否打通": has_supply_chain,
            "是否具备全价值链数据协同": has_value_chain, "系统间数据集成贯通程度": integration_level,
            "研发投入占比": rd_ratio, "专利数量": patent_count, "是否开展产品/工艺数字化仿真": has_simulation,
            "AI应用场景数量": ai_scenarios, "AI应用覆盖比例": ai_coverage,
            "智能制造能力成熟度评估等级": maturity, "两化融合贯标等级": integration_rating,
            "近三年智能化改造累计投入": invest_3y, "全员劳动生产率": labor_productivity,
            "关键设备综合效率 OEE": oee,
        }
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user_content = "请根据以下企业数据完成画像评估与等级推荐：\n\n"
        user_content += f"- 当前系统时间: {now}\n"
        for k, v in user_data.items():
            user_content += f"- {k}: {v}\n"

        if is_configured():
            with st.spinner("⏳ 正在调用 AI 智能体生成报告..."):
                report = call_llm(AGENT_PROFILE_PROMPT, user_content, temperature=0.2, max_tokens=6000)
        else:
            st.caption("⚙️ 未配置模型接口，已用离线规则引擎模拟生成画像（零 Key 可跑）；如需 AI 深度报告请在 `.env` 配置 OPENAI_API_KEY。")
            report = demo.build_profile_report(user_data)

        st.session_state["profile_report"] = report
        st.session_state["user_data"] = user_data

    if st.session_state.get("profile_report"):
        import re
        report = st.session_state["profile_report"]
        report_clean = re.sub(r"雷达图数据（供前端渲染）：\{.*?\}", "", report, flags=re.DOTALL)
        st.subheader("📄 企业画像与等级推荐报告")
        st.markdown(report_clean)

with tab2:
    st.caption("根据①的画像报告，选择当前等级与冲刺目标，生成改造路径规划与成本估算（离线·零 Key 可跑）。")
    if not st.session_state.get("user_data"):
        st.warning("⚠️ 请先在「① 企业数据填报与画像」中生成画像报告，再回到此处规划改造路径。")
    else:
        current_level = st.selectbox("请选择您当前的等级（根据上一报告推荐）",
                                     ["基础级", "先进级", "卓越级", "领航级"], index=0)
        target_level = st.selectbox("您希望冲击的更高等级（不可跳级）",
                                    ["先进级", "卓越级", "领航级"], index=0)
        level_order = {"基础级": 0, "先进级": 1, "卓越级": 2, "领航级": 3}
        if level_order.get(target_level, -1) <= level_order.get(current_level, -1):
            st.warning("⚠️ 目标等级应比当前等级更高，请重新选择。")
        else:
            if st.button("生成改造路径规划与成本估算"):
                if not is_configured():
                    st.caption("⚙️ 未配置模型接口，已用离线规则引擎生成改造路径与成本估算（零 Key 可跑）；如需 AI 深度报告请在 `.env` 配置 OPENAI_API_KEY。")
                    upgrade_report = demo.build_upgrade_report(st.session_state["user_data"], current_level, target_level)
                else:
                    upgrade_input = f"""
当前等级: {current_level}
目标等级: {target_level}

上一份画像报告内容（供参考）:
{st.session_state['profile_report']}

企业原始数据:
{st.session_state['user_data']}

请按提示词二的要求生成《改造路径规划与成本估算清单》。
"""
                    with st.spinner("📈 正在生成改造规划..."):
                        upgrade_report = call_llm(AGENT_UPGRADE_PROMPT, upgrade_input,
                                                  temperature=0.2, max_tokens=6000)
                st.subheader("📈 改造路径规划与成本估算清单")
                st.markdown(upgrade_report)

st.divider()
st.markdown("#### 📞 需要更深入的线下服务？")
st.caption("若 AI 画像报告无法完全满足您的需求（如现场诊断、申报书代写、深度改造规划），可提交需求工单，协会线下专家将一对一对接。")
st.page_link("pages/6_线下服务对接.py", label="提交智能需求工单 →", icon="📞", use_container_width=True)

st.info(DISCLAIMER)
