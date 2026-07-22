"""
core/leads.py — 线索工单分级引擎

实现"线上智能体引流 + 线下专家交付"商业闭环的工单打分与分级。
当 AI 智能体无法满足企业深度需求时，引导企业填写引流单，
系统根据预算、紧急度、企业规模、成熟度等维度自动打分分级为 A/B/C 三类，
作为精准线索推送给协会认证的线下服务机构。

分级口径（双轨：规则打分为主，LLM 校验为辅）：
  A 类（高优先级）：高预算 + 需求紧急 + 已有成熟度评估 → 优先派单
  B 类（中优先级）：中等预算/时间 → 次优派单
  C 类（低优先级）：仅了解信息 → 培育跟进

离线（无 LLM Key）也能完整跑通：确定性规则打分。
配置 OpenAI 兼容接口后，可调用大模型对分级结果做智能校验。
"""
from __future__ import annotations

import json
import datetime

# ============================================================
# 选项常量（与表单 dropdown 选项一一对应）
# ============================================================
BUDGET_OPTS = [
    "5万以下",
    "5-10万",
    "10-30万",
    "30-100万",
    "100万以上",
    "暂未确定",
]
URGENCY_OPTS = [
    "立即需要（1周内）",
    "1个月内",
    "1-3个月内",
    "仅先了解一下",
]
DELIVERY_OPTS = [
    "驻场辅导",
    "远程辅导",
    "均可",
]
SCALE_OPTS = [
    "微型（<20人）",
    "小型（20-100人）",
    "中型（100-500人）",
    "大型（500-2000人）",
    "特大型（>2000人）",
]

# 预算 → 分数映射（高预算 = 高付费意愿 = 高分）
BUDGET_SCORE = {
    "5万以下": 1,
    "5-10万": 3,
    "10-30万": 5,
    "30-100万": 8,
    "100万以上": 10,
    "暂未确定": 2,
}
# 紧急度 → 分数映射
URGENCY_SCORE = {
    "立即需要（1周内）": 10,
    "1个月内": 7,
    "1-3个月内": 5,
    "仅先了解一下": 1,
}
# 营收（万元）→ 分数映射（分段打分）
def _revenue_score(rev: float) -> int:
    if rev >= 50000:
        return 8
    if rev >= 20000:
        return 6
    if rev >= 5000:
        return 4
    if rev > 0:
        return 2
    return 0


# ============================================================
# 规则打分（离线确定性引擎）
# ============================================================
def score_lead(form: dict) -> dict:
    """
    根据引流单表单数据，返回打分明细与总分。

    参数 form: 与表单字段对应的 dict，键包括：
        - revenue (float): 上年度营收（万元）
        - budget (str): 服务预算范围
        - urgency (str): 希望何时开始服务
        - maturity (str): 已做智能制造能力成熟度评估等级
        - target_level (str): 目标申报等级
        - scenes_count (int): 已规划/已建场景数
        - challenge (str): 主要挑战
        - need_desc (str): 具体需求描述（长度也作为信号）
    返回:
        {total, grade, breakdown, rationale}
    """
    breakdown = {}

    # 1. 预算维度（满分 10）
    budget = form.get("budget", "暂未确定")
    breakdown["预算付费意愿"] = BUDGET_SCORE.get(budget, 2)

    # 2. 紧急度维度（满分 10）
    urgency = form.get("urgency", "仅先了解一下")
    breakdown["需求紧急度"] = URGENCY_SCORE.get(urgency, 1)

    # 3. 企业规模/营收维度（满分 8）
    rev = form.get("revenue", 0)
    try:
        rev = float(rev) if rev else 0
    except (TypeError, ValueError):
        rev = 0
    breakdown["企业规模(营收)"] = _revenue_score(rev)

    # 4. 成熟度就绪度（满分 5）：已有评估 = 已做好准备 = 高分
    mat = form.get("maturity", "未评估")
    if mat and mat != "未评估":
        breakdown["成熟度就绪度"] = 5
    else:
        breakdown["成熟度就绪度"] = 1

    # 5. 目标等级（满分 4）：目标越高 = 改造空间越大 = 线下服务价值越高
    tl = form.get("target_level", "")
    tl_score = {"领航级": 4, "卓越级": 3, "先进级": 2, "基础级": 1}.get(tl, 1)
    breakdown["目标等级"] = tl_score

    # 6. 需求描述丰富度（满分 3）：描述越详细 = 意向越明确
    desc = form.get("need_desc", "")
    desc_len = len(str(desc).strip())
    if desc_len >= 100:
        breakdown["需求描述丰富度"] = 3
    elif desc_len >= 30:
        breakdown["需求描述丰富度"] = 2
    elif desc_len > 0:
        breakdown["需求描述丰富度"] = 1
    else:
        breakdown["需求描述丰富度"] = 0

    total = sum(breakdown.values())
    grade, rationale = _classify(total, form)

    return {
        "total": total,
        "max_total": 40,
        "grade": grade,
        "breakdown": breakdown,
        "rationale": rationale,
    }


def _classify(total: int, form: dict) -> tuple:
    """根据总分 + 关键字段，判定 A/B/C 等级与处置建议。"""
    urgency = form.get("urgency", "")
    budget = form.get("budget", "")

    # A 类：高优先级（总分≥25 或 高预算+紧急）
    if total >= 25 or (BUDGET_SCORE.get(budget, 0) >= 8 and URGENCY_SCORE.get(urgency, 0) >= 7):
        return "A", (
            "🔴 A 类（高优先级线索）：企业预算充足且需求紧急，已具备一定成熟度基础。"
            "建议 24 小时内由协会优先派单至认证线下机构，安排专家一对一对接。"
        )

    # C 类：低优先级（总分<12 或 仅了解一下 且 低预算）
    if total < 12 or (urgency == "仅先了解一下" and BUDGET_SCORE.get(budget, 0) <= 2):
        return "C", (
            "🔵 C 类（培育跟进线索）：企业目前处于了解阶段，付费意愿或紧迫度较低。"
            "建议纳入协会会员培育池，定期推送政策解读与公益讲座，待条件成熟再激活。"
        )

    # B 类：中优先级
    return "B", (
        "🟠 B 类（中优先级线索）：企业有明确需求与一定预算，但紧迫度中等。"
        "建议 3 个工作日内由协会联系企业进一步沟通需求细节，匹配适合的线下服务方案。"
    )


# ============================================================
# 工单摘要生成
# ============================================================
def build_summary(form: dict, score_result: dict) -> str:
    """生成工单摘要文本（提交后展示给用户确认）。"""
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    bk = score_result["breakdown"]
    lines = [
        f"# 智能需求工单 · 摘要",
        "",
        f"**工单编号**：DL-{now[:10].replace('-','')}-{abs(hash(str(form)))%10000:04d}",
        f"**提交时间**：{now}",
        f"**线索分级**：{score_result['grade']} 类（总分 {score_result['total']}/{score_result['max_total']}）",
        "",
        "## 一、企业基本信息",
        f"- 企业全称：{form.get('company','—')}",
        f"- 所属行业：{form.get('industry','—')}",
        f"- 所在地区：{form.get('region','—')}",
        f"- 上年度营收：{form.get('revenue','—')} 万元",
        f"- 企业规模：{form.get('scale','—')}",
        f"- 联系人：{form.get('contact_name','—')}（{form.get('contact_title','—')}）",
        f"- 联系电话：{form.get('contact_phone','—')}",
        f"- 邮箱：{form.get('contact_email','—')}",
        "",
        "## 二、需求描述",
        f"- 目标申报等级：{form.get('target_level','—')}",
        f"- 智能制造成熟度：{form.get('maturity','—')}",
        f"- 已规划/已建场景：{', '.join(form.get('scenes', [])) or '—'}",
        f"- 主要挑战：{', '.join(form.get('challenges', [])) or '—'}",
        f"- 期望交付方式：{form.get('delivery','—')}",
        f"- 具体需求描述：{form.get('need_desc','—')}",
        "",
        "## 三、预算与意向",
        f"- 服务预算：{form.get('budget','—')}",
        f"- 期望开始时间：{form.get('urgency','—')}",
        "",
        "## 四、打分明细",
    ]
    for dim, val in bk.items():
        lines.append(f"- {dim}：**{val}** 分")
    lines.append(f"- **合计：{score_result['total']}/{score_result['max_total']}**")
    lines.append("")
    lines.append(f"## 五、分级处置建议")
    lines.append(score_result["rationale"])
    lines.append("")
    lines.append(
        "> 本工单由「天工智梯」AI 智能体自动分级，仅供协会线下服务对接参考。"
        "最终派单与服务方案由协会线下专家确认。"
    )
    return "\n".join(lines)


# ============================================================
# LLM 校验（可选，需配置接口）
# ============================================================
LLM_VERIFY_PROMPT = """你是大连市智能制造产业协会的线索分级审核员。
请根据以下企业提交的智能需求工单数据，校验系统给出的 A/B/C 分级是否合理。

工单数据（JSON）：
{form_json}

系统规则打分结果：
- 总分：{total}/{max_total}
- 分级：{grade} 类
- 各维度得分：{breakdown}

请用 2-3 句话给出校验意见：
1. 分级是否合理（合理/偏高/偏低）
2. 如有偏差，给出建议等级与一句理由
3. 补充一条线下服务注意事项

注意：只输出校验意见文本，不要重复工单数据。"""


def verify_with_llm(form: dict, score_result: dict) -> str | None:
    """
    调用大模型对分级结果做智能校验。
    需配置 OPENAI_API_KEY；未配置时返回 None（走纯规则）。
    """
    try:
        from core.llm import call_llm, is_configured
    except Exception:
        return None
    if not is_configured():
        return None
    prompt = LLM_VERIFY_PROMPT.format(
        form_json=json.dumps(form, ensure_ascii=False, indent=2),
        total=score_result["total"],
        max_total=score_result["max_total"],
        grade=score_result["grade"],
        breakdown=json.dumps(score_result["breakdown"], ensure_ascii=False),
    )
    return call_llm("你是协会线索分级审核员，请简洁专业地输出校验意见。", prompt,
                    temperature=0.2, max_tokens=500)
