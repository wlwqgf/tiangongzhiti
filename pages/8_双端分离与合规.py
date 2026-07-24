# -*- coding: utf-8 -*-
"""
pages/8_双端分离与合规.py
------------------------------------------------------------
改动3 落地页：企业端 / 专家端 双智能体分离 + 合规声明。
- 侧边栏 radio 切换模式（与 app.py 主开关保持一致）。
- 仅点击「提交」后才调用路由，避免任何自动执行/泄露。
- 企业端命中禁输出关键词时，只返回引导语，绝不回显专家端权重。
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from core.agent_mode import (
    ENTERPRISE, EXPERT, MODES, route_query, build_system_prompt,
)

st.set_page_config(page_title="双端分离与合规", page_icon="🛡️")
st.title("🛡️ 双智能体分离与合规声明")

st.markdown(
    "本系统**企业端**与**专家端**为两个物理隔离的智能体：\n"
    "- 企业端：仅含公开政策 + 脱敏字段库，辅助申报撰写。\n"
    "- 专家端：含评分权重与评审细则，仅专家可见，防止企业泄题式刷分。\n"
    "两端口径由 `core/agent_mode.py` 统一路由，企业端问及评审权重将被拦截。"
)

mode = st.sidebar.radio("选择智能体模式", MODES, index=0)
query = st.text_input("输入你的问题（例如：评分权重是多少 / 生产作业写几个场景）")
if st.button("提交"):
    r = route_query(mode, query)
    if not r["allowed"]:
        st.error(r["prompt_hint"])
    else:
        st.success(f"✅ {mode} 合规放行")
        # 仅展示提示词"作用域说明"，不打印专家端权重明细给企业端
        scope = (
            "企业端知识域：公开政策 + 脱敏字段库（不含评分权重）"
            if mode == ENTERPRISE
            else "专家端知识域：含评分权重与评审细则（企业端不可见）"
        )
        st.info(scope)
        with st.expander("查看本端系统提示词（点击展开）"):
            st.code(build_system_prompt(mode), language="text")

st.caption("合规红线：企业端无法获取专家评审权重 / 打分细则。")
