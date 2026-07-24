"""
模块① 企业智能制造成熟度自评材料准备
v2 — 引导企业按 c3mep 自评所需材料清单逐项准备,
     完成后一键跳转 c3mep.cn 官方自评通道。

依据：GB/T 39116-2020《智能制造能力成熟度模型》
     GB/T 39117-2020《智能制造能力成熟度评估方法》

本模块的设计定位（与原模块一不同）：
  原版 = AI 自评生成画像报告
  新版 = 自评前材料准备助手（跳转至 CMMMEP 官方平台）
新方案更专业、更合规：
  - CMMMEP 是国标制定方（中国电子技术标准化研究院）的官方自评通道，
    比自研评估工具权威性高得多；
  - 我们的差异化价值 = 让企业自评前不缺料、流程更顺畅。
"""
import streamlit as st
from core.theme import apply_theme, render_enterprise_sidebar
from core.checklist import (
    CHECKLIST,
    progress,
    total_count,
    group_progress,
    apply_preset,
    reset_all,
    CASE_PRESET_NAME,
    CASE_PRESET_DESC,
)

CMMEP_URL = "https://www.c3mep.cn"
CMMEP_DESC = "中国电子技术标准化研究院 · 智能制造能力成熟度评估平台"

# 官方自评估要素条件（基础级智能工厂）— 作为模块①提示展示
OFFICIAL_ELEMENTS_MD = """
### 一、基本要求
1. 企业应为规模以上工业企业，企业和产品均具有较强市场竞争力。
2. 企业近三年经营和财务状况良好，无不良信用记录、无较大及以上安全、环保等事故，无违法违规行为，未违反国家相关产业政策。
3. 工厂使用的关键技术装备、工业软件、系统（含工业控制系统）等安全可控，网络安全和数据安全风险可控。
4. 企业应建立智能工厂统筹规划、建设和运营的组织机制，拥有一批智能制造专业人才。
5. 基础级智能工厂智能制造能力成熟度自评估水平应达到 **GB/T 39116—2020《智能制造能力成熟度模型》二级及以上**。

### 二、建设内容
鼓励企业参考《智能制造典型场景参考指引（2025年版）》，围绕工厂建设、研发设计、生产作业、生产管理、运营管理等开展智能工厂建设，且**至少覆盖生产作业环节**。

1. **工厂建设**：开展产线级、车间级数字化规划与建设；部署安全可控的智能制造装备、工业软件、系统（含工业控制系统）和数字基础设施。
2. **研发设计**：应用数字化设计工具开展产品、工艺研发设计，实现设计数据、文档、图纸的规范管理。
3. **生产作业**：开展关键装备数字化改造与工艺优化，按需配置自动化检测等装备，实现关键装备和系统的状态可视化监测，以及关键生产工序自动化。
4. **生产管理**：应用生产信息系统，对生产计划、设备资产、生产物料等进行管理，实现关键生产过程规范化，支撑精益管理改善。
5. **运营管理**：应用运营信息系统，对采购、销售、库存、财务和人力资源等进行管理，实现经营数据精准核算和绩效指标量化评估。

### 三、建设成效
参考《智能工厂建设关键绩效指标参考》、**GB/T 47695-2026《企业智能制造效能评测方法》**，评估智能工厂建设成效，主要技术经济指标应高于省（区、市）同行业平均水平。
"""

st.set_page_config(page_title="①企业自评材料准备", layout="wide")
apply_theme()

st.markdown(
    "<h1 style='font-size:1.55rem'>📋 ① 自评材料清单</h1>",
    unsafe_allow_html=True,
)
st.caption(
    f"5 大能力域 · {total_count()} 项必备材料 · 准备就绪一键跳转 {CMMEP_URL} 官方自评"
)

# ============================================================
# 官方自评估要素条件（提示）
# ============================================================
st.info(
    "📌 **官方自评估要素条件提示**：以下为「基础级智能工厂」申报的官方要素条件"
    "（基本要求 + 建设内容 + 建设成效）。请先对照这些条件自查企业是否满足，"
    "再继续下方自评材料清单的准备。"
)
with st.expander("📜 展开查看：官方自评估要素条件（基础级智能工厂）", expanded=False):
    st.markdown(OFFICIAL_ELEMENTS_MD)

# ============================================================
# 侧边栏：企业端导航
# ============================================================
with st.sidebar:
    render_enterprise_sidebar()

# ============================================================
# 顶部：主跳转区
# ============================================================
c1, c2 = st.columns([3, 1])
with c1:
    st.markdown(
        "### 🎯 智能制造能力成熟度自评（CMMMEP 官方通道）\n\n"
        "本模块引导您按 **GB/T 39116-2020**《智能制造能力成熟度模型》"
        "和 **GB/T 39117-2020**《智能制造能力成熟度评估方法》逐项准备自评素材，"
        f"完成后在 [{CMMEP_URL}]({CMMEP_URL}) 进行官方自评。\n\n"
        "**5 个等级**：一级规划级 → 二级规范级 → 三级集成级 → 四级优化级 → 五级引领级\n\n"
        "💡 **本模块价值**：c3mep 是国标制定方的官方自评通道，比自研工具权威性高得多。"
        "本助手帮您**提前梳理材料清单**，自评过程更顺畅、不缺料。"
    )
with c2:
    st.link_button(
        "🚀 前往 c3mep.cn 官方自评",
        CMMEP_URL,
        type="primary",
        use_container_width=True,
        help=CMMEP_DESC,
    )

st.divider()

# ============================================================
# 进度追踪
# ============================================================
done, total, pct = progress(st.session_state)
st.markdown("### 📊 材料准备进度")
pc1, pc2 = st.columns([4, 1])
with pc1:
    st.progress(pct / 100, text=f"已完成 {done} / {total} 项（{pct}%）")
with pc2:
    if pct >= 80:
        st.success("✅ 准备充分")
    elif pct >= 50:
        st.warning(f"⚠️ 还差 {total - done} 项")
    else:
        st.info(f"ℹ️ 继续准备")

# 一键预设（案例演示）
with st.expander(f"🎁 {CASE_PRESET_NAME}", expanded=False):
    st.markdown(CASE_PRESET_DESC)
    st.warning("⚠️ 仅用于演示/测试自评流程，不会连接任何外部服务。")
    b1, b2 = st.columns(2)
    if b1.button("✅ 一键预设全部就绪", key="btn_preset", use_container_width=True):
        apply_preset(st.session_state, on=True)
        st.toast("✅ 已预设全部材料为「就绪」", icon="🎁")
        st.rerun()
    if b2.button("🔄 重置 / 清空", key="btn_reset", use_container_width=True):
        reset_all(st.session_state)
        st.toast("🔄 已清空", icon="🧹")
        st.rerun()

st.divider()

# ============================================================
# 材料清单 (5 组)
# ============================================================
st.markdown("### 📦 自评材料清单")
st.caption(
    "✅ = 材料已就绪可上传，⬜ = 仍需补充。展开各能力域，按清单逐项勾选。"
)

for grp in CHECKLIST:
    gd, gt = group_progress(st.session_state, grp["key"])
    label = f"{grp['title']} — 已就绪 {gd} / {gt} 项"
    with st.expander(label, expanded=True):
        st.caption(grp["sub_title"])
        for it in grp["items"]:
            checked = st.checkbox(
                f"**{it['name']}**",
                key=f"chk_{it['id']}",
            )
            # 描述 + 证据 用两列对齐展示
            cc1, cc2 = st.columns([3, 1])
            with cc1:
                st.markdown(f"📝 **准备说明**：{it['desc']}")
            with cc2:
                st.markdown(f"📂 **证据类型**：{it['evidence']}")

st.divider()

# ============================================================
# 底部：跳转区（主行动）
# ============================================================
done2, total2, pct2 = progress(st.session_state)
st.markdown("### 🎯 完成准备，前往 c3mep 官方自评")

cc1, cc2 = st.columns([3, 1])
with cc1:
    if pct2 >= 80:
        st.success(
            f"✅ 已完成 {done2}/{total2} 项（{pct2}%）— 材料准备充分，可跳转自评。"
        )
    elif pct2 >= 50:
        st.warning(
            f"⚠️ 已完成 {done2}/{total2} 项（{pct2}%）— 建议补齐后再跳转，通过率更高。"
        )
    else:
        st.info(
            f"ℹ️ 已完成 {done2}/{total2} 项（{pct2}%）— 可跳转，但建议补齐材料。"
        )
    st.caption(
        "💡 **温馨提示**：c3mep 是中国电子技术标准化研究院的官方自评平台，"
        "自评结果由平台出具，与本助手（天工智梯）独立。"
        "本模块的价值在于帮您**提前梳理材料清单**，让自评过程更顺畅。"
    )
with cc2:
    st.link_button(
        "🚀 前往 c3mep.cn 自评",
        CMMEP_URL,
        type="primary",
        use_container_width=True,
    )

# 线下服务引导
st.markdown("#### 📞 自评后需要专业辅导？")
st.caption(
    "如自评等级不理想、可由协会认证线下机构提供驻场/远程辅导、"
    "申报书代写、智能工厂梯度培育辅导等服务。"
)
st.page_link(
    "pages/6_线下服务对接.py",
    label="提交线下服务需求 →",
    icon="📞",
    use_container_width=True,
)