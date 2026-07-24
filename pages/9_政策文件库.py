# -*- coding: utf-8 -*-
"""
pages/9_政策文件库.py —— 东北区域政策文件库（企业端 · 资源库）

汇总「天工智梯」接入的东北区域（辽·吉·黑）及国家级智能工厂相关政策原文 / 通知索引，
每条含发布单位、文号、日期、关键奖补摘要与官方来源链接，便于企业按省检索权威出处。
"""
import os
import json

import streamlit as st
from core.theme import apply_theme, render_enterprise_sidebar

st.session_state.setdefault("auth_role", "enterprise")
st.set_page_config(page_title="政策文件库 · 天工智梯", page_icon="📚")
apply_theme()
with st.sidebar:
    render_enterprise_sidebar()

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(_ROOT, "knowledge", "policy_library_index.json")

st.title("📚 东北区域政策文件库")
st.caption(
    "企业端 · 资源库 | 汇总已接入的东北区域（辽·吉·黑）及国家级智能工厂相关政策原文 / 通知，"
    "含发布单位、文号、关键奖补摘要与官方来源链接。"
)

try:
    with open(IDX, encoding="utf-8") as f:
        DOCS = json.load(f)
except Exception as e:
    st.error(f"政策文件库索引加载失败：{e}")
    DOCS = []

REGION_ORDER = ["全国", "辽宁（含大连）", "辽宁·大连", "辽宁·省", "吉林", "吉林·长春新区", "黑龙江"]


def reg_key(r: str) -> int:
    for i, k in enumerate(REGION_ORDER):
        if k in r:
            return i
    return 99


groups = {}
for d in DOCS:
    groups.setdefault(d.get("region", "其他"), []).append(d)

for region in sorted(groups, key=reg_key):
    st.subheader(f"📍 {region}")
    for d in groups[region]:
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{d.get('title', '（无标题）')}**")
                meta = []
                if d.get("publisher"):
                    meta.append(d["publisher"])
                if d.get("doc_no"):
                    meta.append(d["doc_no"])
                if d.get("date"):
                    meta.append(d["date"])
                if meta:
                    st.caption(" · ".join(meta))
                if d.get("summary"):
                    st.markdown(d["summary"])
            with c2:
                if d.get("link"):
                    st.link_button("前往官方来源 ↗", d["link"], use_container_width=True)
    st.divider()

st.caption(
    "⚠️ 本库为政策索引与摘要，具体申报条件、额度与时限以官方最新发布为准；"
    "链接指向政府 / 官方发布页，第三方解读站点已单独标注为非官方。"
)
