"""
模块⑥ 线下服务对接（智能需求工单 / 引流单）

当 AI 智能体无法满足企业深度需求时，引导企业填写本工单。
系统根据预算、紧急度、企业规模、成熟度等维度自动打分分级为 A/B/C 三类，
作为精准线索推送给协会认证的线下服务机构，形成
「线上智能体引流 + 线下专家交付」的商业闭环。

离线（无 LLM Key）也能完整跑通：确定性规则打分。
配置 OpenAI 兼容接口后，可调用大模型对分级结果做智能校验。
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.leads import (
    BUDGET_OPTS, URGENCY_OPTS, DELIVERY_OPTS, SCALE_OPTS,
    score_lead, build_summary, verify_with_llm,
)
from core.llm import is_configured, DISCLAIMER
from core.theme import apply_theme, render_enterprise_sidebar

st.set_page_config(page_title="⑥线下服务对接", layout="wide")
apply_theme()
st.markdown("<h1 style='font-size:1.55rem'>📞 ⑥ 线下服务对接 · 智能需求工单</h1>", unsafe_allow_html=True)
st.caption("当 AI 智能体无法满足您的深度需求时，提交本工单 · 协会线下专家 24 小时内对接 · A/B/C 精准分级派单")

# ---------------- 侧边栏 ----------------
with st.sidebar:
    render_enterprise_sidebar()
    st.markdown("### ℹ️ 工单说明")
    st.caption(
        "本工单用于收集企业深度服务需求，系统将自动分级（A/B/C）并派单至协会认证线下机构。"
        "请如实填写，信息越完整，分级越精准，对接越高效。"
    )
    st.divider()
    if is_configured():
        st.success("✅ 模型接口已配置\n工单分级将启用 AI 智能校验")
    else:
        st.info("💡 未配置模型接口\n工单走规则打分（离线可用）")

st.markdown(
    "「天工智梯」AI 智能体可解答政策标准、等级对标、大纲生成等**前置咨询**问题。"
    "若您的需求涉及**现场诊断、申报书代写、深度改造规划、专家评审辅导**等，"
    "请填写下方工单，协会将安排认证线下机构与您一对一对接。\n\n"
    "**填写约需 3 分钟 · 提交后系统自动分级 · A 类线索 24 小时内响应**"
)

st.divider()

# ---------------- 表单初始化 ----------------
def init_state():
    st.session_state.setdefault("lead_submitted", False)
    st.session_state.setdefault("lead_form_data", None)
    st.session_state.setdefault("lead_score", None)
    st.session_state.setdefault("lead_summary", None)
    st.session_state.setdefault("lead_llm_verify", None)

init_state()

# ---------------- 已提交 → 展示结果 ----------------
if st.session_state.get("lead_submitted"):
    score = st.session_state["lead_score"]
    grade = score["grade"]
    grade_style = {
        "A": ("🔴 A 类 · 高优先级", "#f87171", "已优先派单至协会认证线下机构，专家将在 24 小时内联系您。"),
        "B": ("🟠 B 类 · 中优先级", "#fbbf24", "协会将在 3 个工作日内联系您，进一步沟通需求细节并匹配服务方案。"),
        "C": ("🔵 C 类 · 培育跟进", "#60a5fa", "已纳入协会会员培育池，将定期推送政策解读与公益讲座，待条件成熟再激活。"),
    }
    label, color, action = grade_style[grade]

    st.success(f"✅ 工单已提交成功！")
    st.markdown(
        f"<div style='text-align:center;padding:1.5rem;margin:1rem 0;"
        f"background:var(--glass);border:2px solid {color};border-radius:16px;"
        f"backdrop-filter:blur(6px);'>"
        f"<div style='font-size:1.6rem;font-weight:800;color:{color};margin-bottom:.5rem'>{label}</div>"
        f"<div style='color:#9fb3d6;font-size:.95rem'>{action}</div>"
        f"<div style='color:#7fe9ff;font-size:1.1rem;margin-top:.5rem'>"
        f"总分 {score['total']}/{score['max_total']}</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    with st.expander("📄 查看工单完整摘要", expanded=True):
        st.markdown(st.session_state["lead_summary"])

    if st.session_state.get("lead_llm_verify"):
        with st.expander("🤖 AI 智能校验意见", expanded=False):
            st.markdown(st.session_state["lead_llm_verify"])

    st.divider()
    st.markdown("#### 📞 协会联系方式")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("服务热线", "0411-XXXX-XXXX")
    with col_b:
        st.metric("邮箱", "service@dlzmia.cn")
    with col_c:
        st.metric("地址", "大连市高新区·协会秘书处")

    st.info(
        "📋 **后续流程**：协会线下服务专员将根据工单分级联系您 → 了解详细需求 → "
        "匹配认证咨询机构 → 签署服务协议 → 专家驻场/远程交付 → 申报书定稿与评审辅导。"
    )
    st.info(DISCLAIMER)

    if st.button("📝 再提交一份工单", use_container_width=False):
        st.session_state["lead_submitted"] = False
        st.session_state["lead_form_data"] = None
        st.session_state["lead_score"] = None
        st.session_state["lead_summary"] = None
        st.session_state["lead_llm_verify"] = None
        st.rerun()

# ---------------- 未提交 → 展示表单 ----------------
else:
    # 不用 st.form，改用普通容器 + st.button，确保 widget 值即时存入 session_state
    # ========== 第一步：企业基本信息 ==========
    st.markdown("##### 📋 第一步 · 企业基本信息")
    st.caption("用于识别企业身份与规模画像，信息越准确分级越精准。")
    c1, c2 = st.columns(2)
    with c1:
        company = st.text_input("企业全称 *", placeholder="如：大连XX智能制造有限公司", key="lead_company")
        industry = st.selectbox("所属行业 *", [
            "装备制造", "汽车零部件", "电子信息", "化工", "医药", "新材料",
            "食品", "金属制品", "通用设备", "专用设备", "其他",
        ], index=None, placeholder="请选择行业", key="lead_industry")
        region = st.text_input("所在地区", placeholder="如：大连市金普新区", key="lead_region")
        revenue = st.number_input("上年度营收（万元）", min_value=0, step=100, value=0, key="lead_revenue")
        scale = st.selectbox("企业规模（员工人数）", SCALE_OPTS, index=None, placeholder="请选择规模", key="lead_scale")
    with c2:
        contact_name = st.text_input("联系人姓名 *", placeholder="如：张三", key="lead_contact_name")
        contact_title = st.text_input("联系人职位", placeholder="如：信息化部长 / 总经理", key="lead_contact_title")
        contact_phone = st.text_input("联系电话 *", placeholder="如：138XXXXXXXX", key="lead_contact_phone")
        contact_email = st.text_input("邮箱", placeholder="如：zhangsan@company.com", key="lead_contact_email")

    st.divider()

    # ========== 第二步：需求描述 ==========
    st.markdown("##### 💬 第二步 · 需求描述")
    st.caption("深入挖掘企业智能化转型痛点与难点，便于线下专家精准匹配。")
    c3, c4 = st.columns(2)
    with c3:
        target_level = st.selectbox("目标申报等级 *", ["基础级", "先进级", "卓越级", "领航级", "尚未确定"], index=4, key="lead_target_level")
        maturity = st.selectbox("智能制造能力成熟度评估等级", [
            "未评估", "一级", "二级", "三级", "四级", "五级",
        ], index=0, key="lead_maturity")
    with c4:
        delivery = st.selectbox("期望交付方式", DELIVERY_OPTS, index=2, key="lead_delivery")

    scenes = st.multiselect("已规划/已建的典型场景（可多选）", [
        "工厂数字化规划设计", "数字孪生工厂构建", "产品数字化设计", "产品虚拟验证",
        "工艺数字化设计", "生产计划优化", "车间智能排产", "柔性产线快速换产",
        "先进过程控制", "人机协同作业", "在线智能检测", "质量精准追溯",
        "设备故障诊断与预测", "智能经营决策", "数智精益管理", "远程运维服务",
        "供应链协同管理", "能源智能管控", "安全一体化管控", "其他",
    ], key="lead_scenes")
    challenges = st.multiselect("当前面临的主要挑战（可多选）", [
        "政策标准不清晰", "等级对标困难", "申报材料撰写困难",
        "数据指标不足", "缺乏现场核查经验", "改造路径不明确",
        "预算有限需要分步实施", "其他",
    ], key="lead_challenges")
    need_desc = st.text_area(
        "具体需求描述 *", height=120,
        placeholder="请详细描述您遇到的具体问题或需要的服务（不限于申报），例如：\n"
        "「我们计划明年申报先进级智能工厂，目前数控化率约60%，联网率40%，"
        "MES刚上线3个月，希望专家帮我们评估差距并辅导申报书撰写。」",
        key="lead_need_desc",
    )

    st.divider()

    # ========== 第三步：预算与意向 ==========
    st.markdown("##### 💰 第三步 · 预算与意向")
    st.caption("用于判断需求紧急程度与付费意愿，信息严格保密，仅用于服务匹配。")
    c5, c6 = st.columns(2)
    with c5:
        budget = st.selectbox("服务预算范围 *", BUDGET_OPTS, index=None, placeholder="请选择预算", key="lead_budget")
    with c6:
        urgency = st.selectbox("希望何时开始服务 *", URGENCY_OPTS, index=None, placeholder="请选择时间", key="lead_urgency")

    st.divider()

    # ========== 第四步：服务授权 ==========
    st.markdown("##### 🔐 第四步 · 服务授权")
    agree = st.checkbox(
        "我已阅读并同意《个人信息保护法》相关要求，授权大连市智能制造产业协会"
        "使用上述信息用于线下服务对接与派单。 *",
        value=False, key="lead_agree",
    )
    st.caption("提交即表示您同意协会将工单信息转交至认证线下服务机构进行服务对接。")

    submitted = st.button("🚀 提交工单", type="primary", use_container_width=True)

    # ---------------- 提交校验与处理 ----------------
    if submitted:
        # 必填校验
        errors = []
        if not company.strip():
            errors.append("企业全称")
        if not industry:
            errors.append("所属行业")
        if not contact_name.strip():
            errors.append("联系人姓名")
        if not contact_phone.strip():
            errors.append("联系电话")
        if not target_level:
            errors.append("目标申报等级")
        if not need_desc.strip():
            errors.append("具体需求描述")
        if not budget:
            errors.append("服务预算范围")
        if not urgency:
            errors.append("希望何时开始服务")
        if not agree:
            errors.append("服务授权同意")

        if errors:
            st.error(f"❌ 以下字段未填写或未勾选：{ '、'.join(errors) }，请补全后重新提交。")
        else:
            form_data = {
                "company": company.strip(),
                "industry": industry,
                "region": region.strip(),
                "revenue": revenue,
                "scale": scale or "未选择",
                "contact_name": contact_name.strip(),
                "contact_title": contact_title.strip(),
                "contact_phone": contact_phone.strip(),
                "contact_email": contact_email.strip(),
                "target_level": target_level,
                "maturity": maturity,
                "scenes": scenes,
                "challenges": challenges,
                "delivery": delivery,
                "need_desc": need_desc.strip(),
                "budget": budget,
                "urgency": urgency,
            }
            score = score_lead(form_data)
            summary = build_summary(form_data, score)

            st.session_state["lead_submitted"] = True
            st.session_state["lead_form_data"] = form_data
            st.session_state["lead_score"] = score
            st.session_state["lead_summary"] = summary

            # LLM 校验（有 Key 时自动调用）
            if is_configured():
                with st.spinner("⏳ AI 正在校验分级结果…"):
                    llm_verify = verify_with_llm(form_data, score)
                    st.session_state["lead_llm_verify"] = llm_verify

            st.rerun()

            st.rerun()

st.info(DISCLAIMER)
