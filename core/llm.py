"""
core/llm.py — 统一的 OpenAI 兼容大模型客户端

所有需要调用大模型的模块（企业画像、大纲生成、研判优化、专家评定）共用本客户端，
配置通过环境变量注入（详见 .env.example）：

    OPENAI_API_KEY   必填，模型 API Key
    OPENAI_BASE_URL  必填，兼容 OpenAI 的接口地址（支持智谱/DeepSeek/通义等国产模型）
    MODEL_NAME       模型名称，默认 glm-4.5-air
"""
from __future__ import annotations

import os
import sys

# 让本包可在 streamlit 多页应用中被稳定导入
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # 未安装 openai 时给出友好提示


def _secret(key: str, default=None):
    """读取密钥：优先环境变量（本地 .env / Streamlit Cloud 注入），其次 st.secrets。"""
    v = os.getenv(key)
    if v:
        return v
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


def is_configured() -> bool:
    """是否已正确配置可用的模型接口。"""
    return bool(_secret("OPENAI_API_KEY")) and OpenAI is not None


def get_client():
    """构造 OpenAI 兼容客户端；未配置时抛错。"""
    if OpenAI is None:
        raise RuntimeError(
            "未检测到 openai 库，请执行 `pip install openai`。"
        )
    return OpenAI(
        api_key=_secret("OPENAI_API_KEY"),
        base_url=_secret("OPENAI_BASE_URL"),
    )


def call_llm(
    system_prompt: str,
    user_content: str,
    *,
    temperature: float = 0.3,
    max_tokens: int = 4096,
    timeout: float = 300.0,
) -> str:
    """
    调用大模型，返回文本。任何异常都会转成可读的错误提示文本返回，
    保证 Streamlit 页面不会因接口问题而整体崩溃。
    """
    if not is_configured():
        return (
            "⚠️ 尚未配置模型接口。请在 `.env` 中填写 `OPENAI_API_KEY` 与 "
            "`OPENAI_BASE_URL` 后重启应用。\n\n"
            "（本系统的「政策标准问答」模块可不依赖大模型离线运行；"
            "其余模块需配置后可生成完整报告。）"
        )
    try:
        client = get_client()
        resp = client.chat.completions.create(
            model=_secret("MODEL_NAME", "glm-4.5-air"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        return resp.choices[0].message.content or ""
    except Exception as e:  # noqa: BLE001
        msg = str(e).lower()
        if "timeout" in msg:
            return "❌ 请求超时（超过设定时限）。请检查网络或稍后重试。"
        if "connection" in msg:
            return f"❌ 网络连接失败，请检查能否访问接口地址：{e}"
        if "authentication" in msg or "api key" in msg or "401" in msg:
            return "❌ API Key 认证失败，请检查 .env 中的密钥是否正确。"
        if "model" in msg and ("not" in msg or "exist" in msg):
            return f"❌ 模型不存在，请检查 MODEL_NAME 设置：{e}"
        return f"❌ 调用接口失败：{e}"


# 系统统一免责声明（用于各模块报告末尾）
DISCLAIMER = (
    "⚠️ 免责声明：本报告/建议由「天工智梯」AI 智能体生成，仅供企业自检与规划参考，"
    "不构成官方结论。最终申报等级、评审结果与奖补金额，请以专家评定及工信部门审核为准。"
)
