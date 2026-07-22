"""
模块③ 申报书大纲智能生成
移植自 C 板块（prompts.py：COSTAR 提示词 / 问卷 schema / 生成规则 / F1-F8 辅助功能）。
含离线缺口分析 + 大模型大纲生成 + 辅助功能调用。

交互约定（对齐模块①）：
- 选择案例「之前」，问卷全部为空，无任何预填内容；
- 在侧边栏选择案例工厂后，问卷自动填入该工厂信息（不自动出报告）；
- 再点「运行缺口分析 + 生成大纲」才生成报告：已配置接口 -> 大模型；未配置 -> 离线规则引擎（零 Key）。
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.c_prompts import (
    COSTAR_PROMPT, QUESTIONNAIRE_SCHEMA, LEVELS, build_full_prompt,
    build_kb_summary, build_rules_text, build_aux_prompts_text,
)
from core.knowledge import LEVEL_THRESHOLDS
from core.llm import call_llm, DISCLAIMER, is_configured
from core import demo
from core.theme import apply_theme, render_enterprise_sidebar

st.set_page_config(page_title="③申报书大纲智能生成", layout="wide")
apply_theme()
st.markdown("<h1 style='font-size:1.55rem'>📝 ③ 申报书大纲智能生成</h1>", unsafe_allow_html=True)
st.caption("10 模块问卷 · 离线缺口分析 · 分级大纲生成 · F1-F8 辅助功能")

LEVEL_KEY_MAP = {"基础级": "basic", "先进级": "advanced", "卓越级": "excellent", "领航级": "leading"}


# ---------------- session_state 初始化（全空） ----------------
def init_q_state():
    for mkey, mdef in QUESTIONNAIRE_SCHEMA.items():
        for fkey, fdef in mdef.get("fields", {}).items():
            ftype = fdef.get("type", "text")
            sk = "q_" + fkey
            if ftype == "multi_select":
                st.session_state.setdefault(sk, [])
            elif ftype == "select":
                st.session_state.setdefault(sk, "（未填）")
            elif ftype == "radio":
                st.session_state.setdefault(sk, fdef.get("default", fdef.get("options", ["是"])[0]))
            elif ftype == "number":
                st.session_state.setdefault(sk, 0.0 if fdef.get("step", 1) < 1 else 0)
            else:  # text / textarea / date
                st.session_state.setdefault(sk, None if ftype == "date" else "")
    st.session_state.setdefault("q_target_level", "基础级")
    st.session_state.setdefault("q_filled_case", None)


def fill_questionnaire(case_key):
    """点击案例后，把该工厂 qdata 回填进问卷（不自动生成报告）。"""
    q = demo.CASES[case_key]["qdata"]
    for mkey, mdef in QUESTIONNAIRE_SCHEMA.items():
        for fkey, fdef in mdef.get("fields", {}).items():
            if fkey not in q:
                continue
            val = q[fkey]
            ftype = fdef.get("type", "text")
            sk = "q_" + fkey
            if ftype == "multi_select":
                opts = fdef.get("options", [])
                st.session_state[sk] = [v for v in val if v in opts] if isinstance(val, list) else []
            elif ftype == "select":
                opts = ["（未填）"] + fdef.get("options", [])
                st.session_state[sk] = val if val in opts else "（未填）"
            elif ftype == "radio":
                opts = fdef.get("options", ["是", "否"])
                st.session_state[sk] = val if val in opts else opts[0]
            elif ftype == "number":
                try:
                    st.session_state[sk] = float(val) if fdef.get("step", 1) < 1 else int(val)
                except (TypeError, ValueError):
                    pass
            elif ftype == "date":
                pass  # 案例无日期数据，保持空
            else:  # text / textarea
                st.session_state[sk] = "" if val is None else str(val)
    st.session_state["q_target_level"] = demo.CASES[case_key]["level"]
    st.session_state["q_filled_case"] = case_key
    # 清空旧大纲，等待用户点生成
    st.session_state.pop("last_outline", None)


init_q_state()


# ---------------- 问卷渲染（session_state 绑定 + 折叠分区） ----------------
def render_questionnaire():
    data = {}
    scenes = {}
    _first = True
    for mkey, mdef in QUESTIONNAIRE_SCHEMA.items():
        with st.expander(mdef.get("title", mkey), expanded=_first):
            _first = False
            fields = mdef.get("fields", {})
            for fkey, fdef in fields.items():
                label = fdef.get("label", fkey)
                ftype = fdef.get("type", "text")
                opts = fdef.get("options", [])
                sk = "q_" + fkey
                if ftype == "date":
                    data[fkey] = st.date_input(label, value=st.session_state.get(sk), key=sk)
                elif ftype == "text":
                    data[fkey] = st.text_input(label, key=sk)
                elif ftype == "textarea":
                    data[fkey] = st.text_area(label, key=sk)
                elif ftype == "number":
                    step = fdef.get("step", 1.0)
                    if step < 1:
                        data[fkey] = st.number_input(label, min_value=0.0, step=step, format="%.2f", key=sk)
                    else:
                        data[fkey] = st.number_input(label, min_value=0, step=1, key=sk)
                elif ftype == "select":
                    opts2 = ["（未填）"] + opts
                    data[fkey] = st.selectbox(label, opts2, key=sk)
                elif ftype == "radio":
                    data[fkey] = st.radio(label, fdef.get("options", ["是", "否"]), horizontal=True, key=sk)
                elif ftype == "multi_select":
                    data[fkey] = st.multiselect(label, opts, key=sk)
            # 八大环节特殊模块
            if "scenes" in mdef:
                st.caption("按「环节名—场景名—实例名」格式填写已建设情况")
                for sc in mdef["scenes"]:
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        built = st.text_input(f"环节{sc['no']} {sc['name']}", key=f"sc_{sc['no']}",
                                              placeholder="已建/部分/未建")
                    with col2:
                        desc = st.text_input("描述/实例", key=f"scd_{sc['no']}", placeholder="如：产线柔性配置—XX产线")
                    scenes[str(sc["no"])] = {"built": built, "desc": desc}
    data["scenes"] = scenes
    return data


# ---------------- 侧边栏：选择案例（仅回填问卷） ----------------
with st.sidebar:
    render_enterprise_sidebar()
    st.markdown("### 📋 选择案例（自动填入问卷）")
    st.caption("点击案例后，问卷自动填入该工厂信息；再点「运行缺口分析 + 生成大纲」即可出报告（离线·零 Key）。")
    for _key, _case in demo.CASES.items():
        if st.button(f"📋 {_key}", key=f"demo3_{_key}", help=_case["label"]):
            fill_questionnaire(_key)
            st.success(f"已载入：{_case['label']}，请点「运行缺口分析 + 生成大纲」")

tab1, tab2 = st.tabs(["📝 问卷与大纲生成", "🧰 辅助功能 F1-F8"])


def offline_gap_analysis(qdata, level_name):
    """离线缺口分析：对照目标等级硬性阈值。"""
    t = LEVEL_THRESHOLDS[level_name]
    gaps = []
    rev = qdata.get("revenue")
    try:
        rev = float(rev) if rev not in (None, "") else None
    except Exception:
        rev = None
    if rev is not None and rev < t["revenue_min"]:
        gaps.append(f"年营业收入 {rev} 万 < {level_name}门槛 {t['revenue_min']} 万")
    net = qdata.get("netRate")
    try:
        net = float(net) if net not in (None, "") else None
    except Exception:
        net = None
    if net is not None and net < t["network_rate"]:
        gaps.append(f"设备联网率 {net}% < {level_name}要求 {t['network_rate']}%")
    cm = qdata.get("cmmmLevel")
    if cm and cm != "（未填）":
        lvl_num = int(str(cm)[0]) if str(cm)[0].isdigit() else None
        if lvl_num is not None and lvl_num < t["maturity_min"]:
            gaps.append(f"成熟度 {cm} < {level_name}要求 ≥{t['maturity_min']}级")
    return gaps


with tab1:
    if st.session_state.get("q_filled_case"):
        st.info(f"✅ 已载入案例「{st.session_state['q_filled_case']}」，问卷已自动填入。请展开下方分区填写/核对，再点「运行缺口分析 + 生成大纲」生成报告。")

    with st.form("qa_form"):
        qdata = render_questionnaire()
        target_level = st.selectbox("拟申报等级", ["基础级", "先进级", "卓越级", "领航级"],
                                    key="q_target_level")
        submitted = st.form_submit_button("🚀 运行缺口分析 + 生成大纲")

    if submitted:
        gaps = offline_gap_analysis(qdata, target_level)
        if is_configured():
            sys_prompt, user_prompt = build_full_prompt(qdata, LEVEL_KEY_MAP[target_level])
            with st.spinner("⏳ 正在调用大模型生成申报书大纲（约 1-3 分钟）..."):
                outline = call_llm(sys_prompt, user_prompt, temperature=0.3, max_tokens=8000)
        else:
            st.caption("⚙️ 未配置模型接口，已用离线规则引擎生成大纲（零 Key 可跑）；如需 AI 深度大纲请在 `.env` 配置 OPENAI_API_KEY。")
            outline = demo.build_outline(qdata, target_level, gaps)
        st.subheader("📄 智能工厂申报书大纲")
        st.markdown(outline)
        st.session_state["last_outline"] = outline

with tab2:
    st.caption("F1-F8 为申报书撰写期的实用小工具；选择功能、填写内容、点「运行辅助功能」即可（离线·零 Key 可跑）。")
    aux = [
        ("F1 政策解读", "粘贴政策条款原文，获取通俗解释+适用企业+申报要点+补贴"),
        ("F2 等级自评", "描述企业现状，获取建议等级+差距清单+整改路径"),
        ("F3 政策匹配", "描述企业，获取匹配政策列表（按匹配度排序）"),
        ("F4 范本检索", "输入关键词，获取匹配范本片段与适用等级"),
        ("F5 补贴测算", "输入投资额+等级，获取补贴区间与计算依据"),
        ("F6 材料清单", "选择等级，获取材料清单（必需→选填）"),
        ("F7 评审模拟", "粘贴申报书草稿，获取模拟专家提问+风险点"),
        ("F8 知识问答", "任意问题，精准回答并标注来源"),
    ]
    aux_name = st.selectbox("选择功能", [a[0] for a in aux])

    # 选案例后自动填充示例输入
    case_key_for_aux = st.session_state.get("q_filled_case")
    if not aux_name.startswith("F6") and case_key_for_aux:
        demo_hint = demo.AUX_DEMO_INPUTS.get(aux_name, "")
        if demo_hint and not st.session_state.get("aux_edited_manually"):
            aux_input = st.text_area("输入内容", value=demo_hint,
                                     key="aux_input",
                                     help="已自动填入示例内容（基于当前选中案例），可修改后点击「运行辅助功能」")
        else:
            aux_input = st.text_area("输入内容", key="aux_input",
                                     placeholder="根据所选功能粘贴相应内容...")
    else:
        aux_input = st.text_area("输入内容", key="aux_input",
                                 placeholder="根据所选功能粘贴相应内容...")

    if st.button("🚀 运行辅助功能"):
        # 标记用户手动编辑过
        st.session_state["aux_edited_manually"] = True
        # 获取案例 form 数据供 F2/F7/F8 使用
        case_form = demo.CASES.get(case_key_for_aux, {}).get("form") if case_key_for_aux else None
        if is_configured():
            spec = next(a for a in aux if a[0] == aux_name)
            sys_prompt = (
                f"你是大连市智能制造产业协会的智能工厂申报顾问。请执行辅助功能【{aux_name}】：{spec[1]}。\n"
                f"严格依据知识库（34份政策/范本文档）回答，严禁编造；缺失数据标注[需企业补充]。\n\n"
                f"知识库摘要：\n{build_kb_summary()}\n\n生成规则：\n{build_rules_text()}"
            )
            with st.spinner("⏳ 正在调用大模型..."):
                out = call_llm(sys_prompt, aux_input, temperature=0.3, max_tokens=4000)
        else:
            st.caption("⚙️ 未配置模型接口，已用离线规则引擎回复（零 Key 可跑）；如需 AI 深度分析请在 `.env` 配置 OPENAI_API_KEY。")
            out = demo.build_aux_response(aux_name, aux_input, case_form)
        st.subheader(f"📋 {aux_name} 结果")
        st.markdown(out)

st.divider()
st.markdown("#### 📞 需要更深入的线下服务？")
st.caption("若大纲生成无法完全满足您的需求（如现场诊断、申报书代写、深度改造规划），可提交需求工单，协会线下专家将一对一对接。")
st.page_link("pages/6_线下服务对接.py", label="提交智能需求工单 →", icon="📞", use_container_width=True)

st.info(DISCLAIMER)
