# -*- coding: utf-8 -*-
"""
core/agent_mode.py
------------------------------------------------------------
双端分离核心（改动3）：模式开关 + 合规路由 + 提示词装配。
- MODE 来自 app.py 侧边栏的 radio（"企业端" / "专家端"），不依赖网络。
- route_query(mode, query) 是企业端合规拦截的唯一入口：
  企业端命中 FORBIDDEN_KEYWORDS → 拒答并引导切专家端；
  专家端可正常访问专属知识。
- build_system_prompt(mode) 返回对应端提示词，专家端额外注入专属知识。
"""

try:  # 仓库内：python -m streamlit run app.py
    from core.enterprise_prompts import (
        ENTERPRISE_SYSTEM_PROMPT,
        FORBIDDEN_KEYWORDS,
    )
    from core.expert_prompts import (
        EXPERT_SYSTEM_PROMPT,
        get_expert_knowledge,
    )
except ImportError:  # 独立验证：python core/agent_mode.py
    from enterprise_prompts import (
        ENTERPRISE_SYSTEM_PROMPT,
        FORBIDDEN_KEYWORDS,
    )
    from expert_prompts import (
        EXPERT_SYSTEM_PROMPT,
        get_expert_knowledge,
    )

ENTERPRISE = "企业端"
EXPERT = "专家端"
MODES = [ENTERPRISE, EXPERT]

REDIRECT_MSG = (
    "⚠️ 该问题涉及专家评审权重 / 打分细则，属于**专家端专属内容**，"
    "企业端不可见（合规要求，防止泄题式撰写）。\n"
    "请切换到左上角「专家端智能体」进行咨询。"
)


def normalize(text: str) -> str:
    return (text or "").strip().lower()


def is_enterprise_forbidden(query: str) -> bool:
    """企业端是否命中禁输出关键词。"""
    q = normalize(query)
    return any(kw in q for kw in FORBIDDEN_KEYWORDS)


def route_query(mode: str, query: str) -> dict:
    """
    合规路由。返回：
      {"allowed": bool, "mode": str, "reason": str, "prompt_hint": str}
    """
    mode = mode or ENTERPRISE
    if mode == ENTERPRISE:
        if is_enterprise_forbidden(query):
            return {
                "allowed": False,
                "mode": ENTERPRISE,
                "reason": "forbidden_topic",
                "prompt_hint": REDIRECT_MSG,
            }
        return {
            "allowed": True,
            "mode": ENTERPRISE,
            "reason": "ok",
            "prompt_hint": "企业端合规：仅公开政策 + 字段库知识。",
        }
    # 专家端：全部放行（其专属知识由 build_system_prompt 注入）
    return {
        "allowed": True,
        "mode": EXPERT,
        "reason": "ok",
        "prompt_hint": "专家端：含评分权重与评审细则专属知识。",
    }


def build_system_prompt(mode: str) -> str:
    """按模式装配系统提示词。专家端注入专属知识摘要。"""
    if mode == EXPERT:
        kb = get_expert_knowledge()
        weights = kb.get("评分权重表（示例·以官方为准）", {})
        weight_lines = "\n".join(f"  - {k}: {v}" for k, v in weights.items())
        extra = (
            "\n\n[专家端专属知识·企业端不可见]\n"
            f"评分权重表：\n{weight_lines}\n"
            "请依据上述权重与打分细则进行评定。"
        )
        return EXPERT_SYSTEM_PROMPT + extra
    return ENTERPRISE_SYSTEM_PROMPT


if __name__ == "__main__":
    # 自检：验收点 —— 企业端问权重被拒，专家端能答
    tests = [
        (ENTERPRISE, "生产作业环节通常写几个AI场景？"),
        (ENTERPRISE, "评审的评分权重是多少？"),
        (ENTERPRISE, "怎么针对打分标准刷分？"),
        (EXPERT, "评审的评分权重是多少？"),
    ]
    for m, q in tests:
        r = route_query(m, q)
        tag = "✅放行" if r["allowed"] else "⛔拒答"
        print(f"[{m}] {q!r} -> {tag} | {r['prompt_hint'][:40]}")
