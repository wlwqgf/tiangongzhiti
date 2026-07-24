# -*- coding: utf-8 -*-
"""
pages/7_政策包推荐.py —— 企业端 · 政策包推荐 + 标杆对标（改动1 & 改动2 落页面）

红线遵循：
  - 选案例前全空 / 点按钮才出报告（本页所有结果均在按钮点击后渲染）
  - 离线可跑：未配置模型接口时，规则引擎直接出结论
  - 不暴露内部字段：不使用 st.json() 输出结构化内部对象
  - 标题不使用 background-clip:text（避免 emoji 消失）
"""
import streamlit as st
from core.field_lib import query_production_scenarios
from core.policy_pack import recommend_policy_package, recommend_policy_package_llm, is_configured
from core.theme import apply_theme, render_enterprise_sidebar

# 登录身份锚定（企业端智能体）
st.session_state.setdefault("auth_role", "enterprise")

st.set_page_config(page_title="政策包推荐 · 天工智梯", page_icon="📦")
apply_theme()
with st.sidebar:
    render_enterprise_sidebar()
st.title("📦 政策包推荐与标杆对标")
st.caption("企业端 · 智能工厂梯度培育申报顾问 | 横向拉通多政策，算出您能拿多少")

LEVELS = ["无", "基础级", "先进级", "卓越级", "领航级"]
LINKS = ["工厂建设", "研发设计", "生产作业", "生产管理", "运营管理"]
INDUSTRIES = ["装备制造", "石化化工", "汽车及零部件", "电子信息", "食品", "其他"]
CERTS = ["无", "创新型中小企业", "专精特新中小企业", "专精特新小巨人"]
IDCS = ["无", "市级", "省级", "国家级"]
TECH_TYPES = ["无", "设备更新", "新型技改"]
REGIONS = ["辽宁（含大连）", "黑龙江", "吉林", "内蒙古"]

# =====================================================================
# 模块一：政策包推荐（强化F3，内置最优不冲突求解器）
# =====================================================================
st.divider()
st.subheader("① 政策包推荐：同步申报哪些、预计拿多少（取高·不冲突）")
st.info("输入企业资质标签，系统横向拉通梯度培育 / 专精特新 / 数字化车间 / 工业设计中心 / 单项冠军 / "
        "新型技改 / 高企 / 科技型中小 / 研发加计 / 先进制造业增值税 / 超长期国债 / 首台套 / 东北振兴金融工具 / "
        "东北区域省级奖补（辽·吉·黑·蒙）等政策，自动按「互斥组取高、叠加上限」算出最优不冲突组合与资金总额。"
        "首台套、东北振兴金融工具等已接入东北地区（黑龙江·吉林·辽宁·内蒙古）真实奖补口径；选择申报省份后可叠加对应省级奖补。")

with st.form("policy_pack_form"):
    pk_region = st.multiselect("申报省份 / 地区（可多选，决定可叠加的省级奖补）",
                               REGIONS, default=["辽宁（含大连）"], key="pk_region")

    st.write("**基础画像**")
    r1c1, r1c2, r1c3 = st.columns(3)
    with r1c1:
        pk_industry = st.selectbox("所属行业", INDUSTRIES, key="pk_ind")
        pk_level = st.selectbox("当前/目标等级", LEVELS, index=2, key="pk_lv")
    with r1c2:
        pk_cert = st.selectbox("专精特新认定", CERTS, key="pk_cert")
        pk_idc = st.selectbox("工业设计中心", IDCS, key="pk_idc")
    with r1c3:
        pk_tech_type = st.selectbox("技改类型", TECH_TYPES, key="pk_tt")
        pk_tech = st.number_input("设备技改投资额（万元）", min_value=0, value=2000, step=100, key="pk_tech")

    st.write("**资质与财务标签**")
    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        pk_high = st.checkbox("高新技术企业", key="pk_hi")
        pk_sme = st.checkbox("科技型中小企业", key="pk_sme")
    with r2c2:
        pk_champ = st.checkbox("制造业单项冠军", key="pk_ch")
        pk_ws = st.checkbox("省级数字化车间", key="pk_ws")
    with r2c3:
        pk_first = st.checkbox("首台(套)产品", key="pk_fs")
        pk_green = st.checkbox("绿色工厂", key="pk_gn")
    with r2c4:
        pk_rnd = st.number_input("研发投入（万元）", min_value=0, value=200, step=50, key="pk_rnd")
        pk_vat = st.number_input("可抵扣进项税（万元）", min_value=0, value=100, step=50, key="pk_vat")

    st.write("**投资与贷款**")
    r3c1, r3c2 = st.columns(2)
    with r3c1:
        pk_fixed = st.number_input("固定资产投入（万元，国债口径）", min_value=0, value=1000, step=100, key="pk_fx")
    with r3c2:
        pk_loan = st.number_input("智改数转贷款额（万元）", min_value=0, value=8000, step=100, key="pk_loan")

    st.write("**东北区域省级奖补补充字段（仅在所选省份适用时测算）**")
    r4c1, r4c2, r4c3 = st.columns(3)
    with r4c1:
        pk_hl_digi = st.number_input("黑龙江·数字化/智能工厂合同投资额（万元）", min_value=0, value=0, step=100, key="pk_hl_digi")
        pk_hl_factory = st.checkbox("黑龙江·智能工厂（省级认定）", key="pk_hl_fac")
        pk_hl_ws = st.checkbox("黑龙江·数字化车间（省级认定）", key="pk_hl_ws")
    with r4c2:
        pk_hidden = st.checkbox("黑龙江·省级制造业隐形冠军", key="pk_hidden")
        pk_fs_price = st.number_input("首台套产品成交价（万元）", min_value=0, value=0, step=50, key="pk_fs_price")
        pk_pledge = st.number_input("吉林·知识产权质押融资金额（万元）", min_value=0, value=0, step=50, key="pk_pledge")
    with r4c3:
        st.caption("说明：黑龙江智能工厂/数字化车间按合同额10%补助（≤1000万/≤200万）；"
                   "黑龙江小巨人省级另奖100万（与大连50万叠加）；吉林知识产权质押贴息2%（≤20万/年）。")
    st.write("**东北区域补充专项（辽宁（含大连）·吉林·黑龙江·内蒙古，勾选或填值即测算上限）**")
    r5c1, r5c2, r5c3 = st.columns(3)
    with r5c1:
        pk_jl_zgsz_invest = st.number_input("吉林·智改数转软硬件投资额（万元）", min_value=0, value=0, step=100, key="pk_jl_zgsz")
        pk_jl_zgsz_type = st.selectbox("吉林·智改数转类型", ["数字化车间", "智能工厂", "未来工厂"], key="pk_jl_zgsz_type")
        pk_dl_central = st.number_input("大连·新型技改中央奖补投资额（万元）", min_value=0, value=0, step=100, key="pk_dl_central")
    with r5c2:
        pk_dl_bench = st.checkbox("大连·新型技改标杆奖励(50-200万)", key="pk_dl_bench")
        pk_dl_guarantee = st.checkbox("大连·中小企业融资担保补助(≤20万)", key="pk_dl_gua")
        pk_dl_xsg = st.checkbox("大连·小升规奖励(5-10万)", key="pk_dl_xsg")
        pk_ln_low = st.checkbox("辽宁·低空经济贷款贴息(单企业年≤500万)", key="pk_ln_low")
    with r5c3:
        pk_ln_compute = st.checkbox("辽宁·算力使用补助(≤200万/年)", key="pk_ln_compute")
        pk_ln_chem = st.checkbox("辽宁·化工设备更新补贴(≤1000万)", key="pk_ln_chem")
        pk_ccxq_tech = st.checkbox("长春新区·技改/智改数转配套(≤200万)", key="pk_ccxq_tech")
        pk_ccxq_fs = st.checkbox("长春新区·首台套配套(≤50万)", key="pk_ccxq_fs")
        pk_hl_loan80 = st.checkbox("黑龙江·规上工业企业贷款贴息80%(≤1000万/年)", key="pk_hl_loan80")
        pk_hl_fs_ins = st.checkbox("黑龙江·首台套保险补偿(综合险≤50万/年)", key="pk_hl_fs_ins")
    submit_pk = st.form_submit_button("生成政策包推荐", use_container_width=True, type="primary")

if submit_pk:
    profile = {
        "industry": pk_industry, "level": None if pk_level == "无" else pk_level,
        "cert": None if pk_cert == "无" else pk_cert,
        "tech_type": None if pk_tech_type == "无" else pk_tech_type, "tech_invest": pk_tech,
        "is_hightech": pk_high, "is_tech_sme": pk_sme, "rnd_invest": pk_rnd,
        "idc": None if pk_idc == "无" else pk_idc, "champion": pk_champ,
        "digital_workshop": pk_ws, "first_set": pk_first, "green_factory": pk_green,
        "fixed_asset_invest": pk_fixed, "vat_base": pk_vat, "loan_amount": pk_loan,
        "region": pk_region or ["辽宁（含大连）"],
        "hl_digi_invest": pk_hl_digi, "digital_factory_hl": pk_hl_factory,
        "digital_workshop_hl": pk_hl_ws, "hidden_champion": pk_hidden,
        "first_set_price": pk_fs_price, "pledge_amount": pk_pledge,
        "jl_zgsz_invest": pk_jl_zgsz_invest, "jl_zgsz_type": pk_jl_zgsz_type,
        "dl_tech_central_invest": pk_dl_central,
        "dl_tech_benchmark": pk_dl_bench, "dl_sme_guarantee": pk_dl_guarantee,
        "dl_xiaoshenggui": pk_dl_xsg, "ln_lowaltitude": pk_ln_low,
        "ln_compute": pk_ln_compute, "ln_chemical": pk_ln_chem,
        "ccxq_tech": pk_ccxq_tech, "ccxq_fs": pk_ccxq_fs,
        "hl_loan_80": pk_hl_loan80, "hl_fs_insurance": pk_hl_fs_ins,
    }
    rec = recommend_policy_package_llm(profile) if is_configured() else recommend_policy_package(profile)

    st.success(rec["text"])
    if rec["matched"]:
        st.write("##### ✅ 已选政策（互斥组取高·不冲突）")
        for m in rec["matched"]:
            # 防御性渲染：单条字段缺失不阻塞整页
            st.markdown(
                f"- **{m.get('policy','?')}**（`{m.get('level','—')}`）：约 **{m.get('amount_wan','?')} 万元** — "
                f"{m.get('basis','')} {m.get('note','')}"
            )
    if rec["pending"]:
        st.write("##### ⏳ 需补字段 / 待核定政策（补充字段或按最新通知核定后自动测算）")
        for p in rec["pending"]:
            st.markdown(f"- **{p.get('policy','?')}** — {p.get('basis','')} {p.get('note','')}")
    if rec["excluded"]:
        st.write("##### 🔒 互斥 / 取高说明")
        for e in rec["excluded"]:
            st.markdown(f"- {e}")
    if rec["upgrades"]:
        st.write("##### 💡 升级建议（满足条件可再增）")
        for u in rec["upgrades"]:
            st.markdown(f"- {u}")
    if not rec["matched"] and not rec["pending"]:
        st.warning(rec["text"])
    if rec.get("narrative"):
        st.info(rec["narrative"])
    st.caption("⚠️ [真实·大连]为惠企30条明确值；[真实·东北]为东北地区（黑·吉·辽·蒙）省级政策明文值；[真实·全国]为国家级政策；"
               "[暂无]为政策明文暂无补助。总额封顶与叠加以各省最新申报指南为准，本端仅作前置参考。")

# =====================================================================
# 模块二：标杆对标（改动1 结构化字段库）
# =====================================================================
st.divider()
st.subheader("② 标杆对标：同行业同等级，通常写几个场景？")
st.info("基于结构化字段库（行业+等级+环节+场景+关键指标数据+得分点段落），"
        "回答老师那句原话：『同行业的先进级企业，在\"生产作业\"环节通常写几个场景？』")

with st.form("benchmark_form"):
    b1, b2, b3 = st.columns(3)
    with b1:
        bm_industry = st.selectbox("行业", INDUSTRIES, key="bm_ind")
    with b2:
        bm_level = st.selectbox("等级", LEVELS, index=1, key="bm_lv")
    with b3:
        bm_link = st.selectbox("环节", LINKS, index=2, key="bm_link")
    submit_bm = st.form_submit_button("查询标杆对标", use_container_width=True)

if submit_bm:
    q = query_production_scenarios(bm_industry, bm_level, bm_link)
    if q["matched"] == 0:
        st.warning(q.get("message", "暂无样本。"))
    else:
        st.success(f"匹配样本 {q['matched']} 份 ｜ 该环节通常写 **{q['count_typical']} 个** 典型场景")
        st.write("##### 高频场景（标杆企业常写）")
        st.markdown("、".join(f"**{s}**" for s in q["top_scenarios"]))
        st.write("##### 标杆得分点段落（脱敏，供借鉴）")
        for src, para in zip(q["sources"], q["scoring_paragraphs"]):
            st.markdown(f"> 【{src}】{para}")
        st.caption("⚠️ 字段库样本持续扩充中；当前为示例数据，仅供写法借鉴，不替代专家裁定。")

st.divider()
st.caption("天工智梯 · 企业端 | 本页为辅助参考，最终以专家评定及工信部门审核为准。")
