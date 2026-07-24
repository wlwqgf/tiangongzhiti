"""
天工智梯 · 智能工厂申报全流程 AI 智能体系统 — 双智能体独立登录入口

两个智能体账号相互独立、凭据不同：
  · 企业端  账号 01 / 密码 11111   →  申报画像 / 政策问答 / 大纲 / 研判 / 政策包
  · 专家端  账号 02 / 密码 22222   →  专家评定反馈（评分权重、评审细则可见）

运行：  streamlit run app.py
依赖：  pip install -r requirements.txt；.env 中配置模型接口（未配置亦可离线演示）
"""
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import streamlit as st
from core.llm import is_configured, DISCLAIMER
from core.theme import apply_theme


# ============================================================
# 凭据表：模拟两个独立智能体
# ============================================================
CREDENTIALS = {
    "enterprise": {
        "user": "01", "pwd": "11111",
        "label": "企业端", "icon": "🏢",
        "page": "pages/1_自评材料清单.py",
        "tagline": "面向制造业企业 · 自测画像 / 政策问答 / 大纲生成 / 申报书研判",
    },
    "expert": {
        "user": "02", "pwd": "22222",
        "label": "专家端", "icon": "🧑‍⚖️",
        "page": "pages/5_专家评定反馈.py",
        "tagline": "面向评审专家 · 初筛 / 增强标注 / 评分辅助与建议",
    },
}


def _is_logged_in() -> bool:
    return st.session_state.get("auth_user") in {"01", "02"}


def _current_role() -> str | None:
    return st.session_state.get("auth_role")


def do_login(role_key: str, username: str, password: str):
    cred = CREDENTIALS[role_key]
    if username.strip() != cred["user"]:
        return False, "账号不正确"
    if password != cred["pwd"]:
        return False, "密码不正确"
    st.session_state["auth_role"] = role_key
    st.session_state["auth_user"] = cred["user"]
    return True, ""


def do_logout():
    for k in ("auth_role", "auth_user", "selected_role"):
        st.session_state.pop(k, None)


# ============================================================
# 页面配置
# ============================================================
st.set_page_config(
    page_title="天工智梯 · 智能工厂申报 AI 专家顾问",
    page_icon="🏭",
    layout="wide",
)
apply_theme()


# ============================================================
# 侧边栏：模型状态 + 身份面板
# ============================================================
with st.sidebar:
    st.title("🏭 天工智梯")
    st.caption("智能工厂申报全流程 AI 智能体系统")
    st.divider()
    if is_configured():
        st.success("✅ 模型接口已配置")
    else:
        st.warning("⚠️ 未检测到模型配置")
        st.caption(
            "在 `.env` 中填写 OPENAI_API_KEY / OPENAI_BASE_URL 后重启，"
            "「政策标准问答」可离线使用，其余模块需接口方可生成报告。"
        )
    st.divider()

    # —— 身份面板：登录后显示当前身份 + 退出 —— 
    st.subheader("🔐 当前身份")
    if _is_logged_in():
        role_key = _current_role()
        cred = CREDENTIALS[role_key]
        st.markdown(
            f"<div style='padding:.7rem .9rem;border:1px solid var(--border);"
            f"border-radius:11px;background:var(--glass);box-shadow:var(--glow)'>"
            f"<div style='font-size:1.7rem'>{cred['icon']}</div>"
            f"<div style='font-weight:700;color:#7fe9ff;margin-top:.2rem'>{cred['label']}</div>"
            f"<div style='font-size:.85rem;color:#9fb3d6'>账号：{st.session_state['auth_user']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if st.button("🚪 退出登录", use_container_width=True, key="logout_sidebar"):
            do_logout()
            st.rerun()
    else:
        st.info("尚未登录 · 请在右侧面板选择身份登录")
    st.divider()
    st.caption("大连市智能制造产业协会 · AI 专家顾问")


# ============================================================
# 主区
# ============================================================
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
    "一站式 AI 辅助。定位为「线上引流 + 线下专家交付」的辅导工具，"
    "输出**指导性意见**而非权威结论。"
)

st.divider()

if _is_logged_in():
    # ============================
    # 已登录：欢迎 + 进入对应智能体
    # ============================
    role_key = _current_role()
    cred = CREDENTIALS[role_key]
    st.success(
        f"✅ 您已登录为 **{cred['label']}**（账号 {st.session_state['auth_user']}）"
    )
    c1, c2 = st.columns([2, 1])
    with c1:
        if st.button(
            f"{cred['icon']}  进入{cred['label']}智能体",
            type="primary", use_container_width=True, key="enter_agent",
        ):
            st.switch_page(cred["page"])
    with c2:
        if st.button("🚪 退出登录", use_container_width=True, key="logout_main"):
            do_logout()
            st.rerun()

    st.divider()
    st.page_link(
        "pages/6_线下服务对接.py",
        label="📞 提交智能需求工单 · 对接协会线下专家",
        icon="📞", use_container_width=True,
    )
else:
    # ============================
    # 未登录：先选端 → 再弹该端账号密码
    # ============================
    selected = st.session_state.get("selected_role", None)

    if selected is None:
        # —— 第一步：选择登录端 ——
        st.subheader("🚪 请选择登录端")
        st.caption("两个智能体账号独立、凭据不同。请先选择要进入的智能体，再填写账号密码。")

        st.markdown(
            """
<style>
.pick-card{
  background:var(--glass); border:1px solid var(--border);
  border-radius:16px; padding:1.1rem 1.2rem; backdrop-filter:blur(6px);
  box-shadow:var(--glow); text-align:center; transition:.2s;
}
.pick-card .big-icon{ font-size:2.4rem; line-height:1; }
.pick-card h4{ color:#7fe9ff; margin:.4rem 0 .2rem 0; }
.pick-card .tag{ color:#9fb3d6; font-size:.86rem; }
</style>
""",
            unsafe_allow_html=True,
        )

        c1, c2 = st.columns(2, gap="large")
        with c1:
            st.markdown(
                "<div class='pick-card'>"
                "<div class='big-icon'>🏢</div>"
                "<h4>企业端智能体</h4>"
                "<div class='tag'>面向制造业企业 · 自测画像 / 政策问答 / 大纲生成 / 申报书研判</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "选择企业端",
                use_container_width=True, type="primary", key="pick_enterprise",
            ):
                st.session_state["selected_role"] = "enterprise"
                st.rerun()
        with c2:
            st.markdown(
                "<div class='pick-card'>"
                "<div class='big-icon'>🧑‍⚖️</div>"
                "<h4>专家端智能体</h4>"
                "<div class='tag'>面向评审专家 · 初筛 / 增强标注 / 评分辅助与建议</div>"
                "</div>",
                unsafe_allow_html=True,
            )
            if st.button(
                "选择专家端",
                use_container_width=True, type="primary", key="pick_expert",
            ):
                st.session_state["selected_role"] = "expert"
                st.rerun()
    else:
        # —— 第二步：该端的登录表单 ——
        cred = CREDENTIALS[selected]
        st.subheader(f"{cred['icon']} 登录 {cred['label']}智能体")
        st.caption(cred["tagline"])
        if st.button("← 返回选择登录端", key="back_pick"):
            st.session_state.pop("selected_role", None)
            st.rerun()

        with st.form(f"login_{selected}", clear_on_submit=False):
            u = st.text_input("账号", key=f"u_{selected}", placeholder="请输入账号")
            p = st.text_input(
                "密码", type="password", key=f"p_{selected}", placeholder="请输入密码"
            )
            submitted = st.form_submit_button(
                f"登录{cred['label']}", use_container_width=True, type="primary"
            )
            if submitted:
                ok, msg = do_login(selected, u, p)
                if ok:
                    st.success("登录成功，正在进入…")
                    st.switch_page(cred["page"])
                else:
                    st.error(f"登录失败：{msg}")
        with st.expander("ℹ️ 查看测试凭据", expanded=False):
            st.code(f"账号：{cred['user']}\n密码：{cred['pwd']}", language="text")

st.divider()

with st.expander("🧭 使用前须知 / 免责声明", expanded=False):
    st.markdown(
        "- **四级梯度、逐级申报**：基础级→先进级→卓越级→领航级，原则上不可跳级，跳级面临一票否决。\n"
        "- **数据真实**：所有建议基于您填报的数据，缺失项将标注，不代为编造。\n"
        "- **双智能体独立**：企业端（账号 01）与专家端（账号 02）凭据独立、互不可见，"
        "分别提供申报辅助与评审支持；专家端的评分权重与评审细则仅对账号 02 可见。\n"
        "- **线下交付闭环**：AI 给出初判与建议，复杂问题转接协会线下专家一对一辅导。"
    )
    st.info(DISCLAIMER)