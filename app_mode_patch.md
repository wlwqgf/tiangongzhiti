# app.py 双模式开关接入补丁（改动3）

> 说明：仓库 `app.py` 已是双入口（企业端 ①②③④ / 专家端 ⑤）。本补丁在其侧边栏加一个**全局模式开关**，
> 并把开关值注入到所有页面的 `st.session_state["agent_mode"]`，由 `core/agent_mode.py` 统一做合规路由。
> 把下面两段分别粘进你的 `app.py`（或等价的入口文件）即可，无需改动现有页面逻辑。

## 1) 在侧边栏顶部加入模式开关（放在 `st.sidebar` 区域最前）

```python
import streamlit as st
from core.agent_mode import ENTERPRISE, EXPERT, MODES

# —— 改动3：双智能体分离 模式开关 ——
st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ 智能体模式")
agent_mode = st.sidebar.radio(
    "选择当前智能体", MODES,
    index=0 if st.session_state.get("agent_mode", ENTERPRISE) == ENTERPRISE else 1,
    key="agent_mode_radio",
)
st.session_state["agent_mode"] = agent_mode
if agent_mode == EXPERT:
    st.sidebar.warning("专家端：含评分权重与评审细则，仅评审人员使用。")
else:
    st.sidebar.info("企业端：辅助申报撰写，不含评审口径。")
```

## 2) 在每个页面调用大模型前，用路由做合规拦截

在 `pages/*.py` 真正调用 `call_llm(...)` 之前加一段（以企业端页面为例）：

```python
from core.agent_mode import route_query, build_system_prompt

mode = st.session_state.get("agent_mode", "企业端")
routed = route_query(mode, user_query)
if not routed["allowed"]:
    st.error(routed["prompt_hint"])   # 企业端问权重 → 拒答 + 引导切专家端
else:
    system_prompt = build_system_prompt(mode)
    # call_llm(system_prompt, user_query)  ← 你的原有调用
```

## 验收点（提交前必跑）

- [ ] 企业端问"评分权重是多少" → 出现 ⚠️ 拒答提示，且页面**不出现任何权重数字**
- [ ] 企业端问"生产作业写几个场景" → 正常回答
- [ ] 专家端问"评分权重是多少" → 正常给出权重表（企业端看不到）
- [ ] 切到专家端时侧边栏出现"仅评审人员使用"提示
