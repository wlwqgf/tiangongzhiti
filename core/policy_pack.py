# -*- coding: utf-8 -*-
"""
core/policy_pack.py —— 政策包推荐引擎（改动2，强化F3）

横向拉通「智能工厂梯度培育 / 专精特新 / 数字化车间 / 工业设计中心 / 单项冠军 /
新型技改 / 高企 / 科技型中小 / 研发加计 / 先进制造业增值税 / 超长期国债」等政策，
并内置「最优不冲突申请组合求解器」：

  · 互斥组取高：同一组内只取最高一档（梯度培育四档、专精特初三档、工业设计中心三级）
  · 叠加上限：大连市奖补以最新申报指南封顶为准（默认不封顶，规则透明可查）
  · 最优选择：给定企业画像 → 算出"拿满且不冲突"的最大金额组合
  · 透明输出：列出已选 / 因互斥未重复享受 / 待补政策（首台套·东北振兴金融工具）/ 升级建议

资金口径来源：ima 共享知识库「智能工厂政策」→《（最新版）惠企政策30条20260225》（大连）
  标注 [真实] 的为惠企30条明确值；标注 [待补] 为国家级政策（首台套 / 东北振兴金融工具）
  等30条未含、待接入数据，不计入总额、单独列示；标注 [暂无] 为政策明文"暂无补助"。

离线规则引擎兜底（无需 API Key）；配置大模型后可生成更自然的申报建议叙述。
"""
try:
    from core.llm import call_llm, is_configured  # 仓库内置 core/llm.py
except Exception:  # 离线/独立验证时兜底，不影响仓库内运行
    def is_configured():
        return False
    def call_llm(*_a, **_k):
        raise RuntimeError("未配置模型接口（离线模式）")


def _gradient_amt(p):
    # 国家级（卓越级及以上）/优秀场景 ≤200万[真实]；省级（先进级）≤100万[真实]
    # 基础级、领航级 30条未给明确市级奖补 → [暂无]
    return {"基础级": None, "先进级": 100, "卓越级": 200, "领航级": None}.get(p.get("level"))


def _zjtx_amt(p):
    # 小巨人 50万[真实]、省级专精特新 30万[真实]；创新型中小企业无定额奖励[暂无]
    return {"创新型中小企业": 0, "专精特新中小企业": 30, "专精特新小巨人": 50}.get(p.get("cert"))


def _idc_amt(p):
    # 国家 50万[真实] / 省级 30万[真实] / 市级无[真实]
    return {"市级": 0, "省级": 30, "国家级": 50}.get(p.get("idc"))


def _tech_amt(p):
    # 大连市制造业新型技术改造专项：设备更新10% / 新型技改20%，单项目最高200万[真实]
    t = p.get("tech_type")
    inv = p.get("tech_invest") or 0
    if t == "设备更新":
        return min(inv * 0.10, 200)
    if t == "新型技改":
        return min(inv * 0.20, 200)
    return 0


def _hightech_amt(p):
    # 高企研发投入阶梯奖励[真实]：50万→5万；100万→10万；1000万→20万
    rnd = p.get("rnd_invest") or 0
    if rnd >= 1000:
        return 20
    if rnd >= 100:
        return 10
    if rnd >= 50:
        return 5
    return 0


def _vat_amt(p):
    # 先进制造业企业增值税加计抵减：当期可抵扣进项税 5%[真实]
    if p.get("is_hightech") and (p.get("vat_base") or 0) > 0:
        return (p.get("vat_base") or 0) * 0.05
    return 0


def _bond_amt(p):
    # 超长期特别国债—工业设备更新和技术改造：固定资产投入 15%[真实]
    inv = p.get("fixed_asset_invest") or 0
    return inv * 0.15 if inv > 0 else 0


# ---------------------------------------------------------------------------
# 政策库：每条含 硬性条件判定 + 资金测算 + 互斥组 + 数据状态
#   amount:  callable(profile) -> 数值(万) 或 None(暂无/待补)
#   group:   互斥组标识（同组取高）；None 表示可独立叠加
#   status:  "active" 已接入真实值 | "pending" 待补数据 | "none" 政策明文暂无补助
# ---------------------------------------------------------------------------
POLICIES = [
    # —— 梯度培育（互斥组：四档取一）——
    {"key": "grad_basic", "name": "智能工厂梯度培育·基础级", "level": "国家级/省级", "group": "梯度培育",
     "eligible": lambda p: p.get("level") == "基础级", "amount": _gradient_amt, "status": "none",
     "basis": "基础级暂无明确市级奖补，以国家/省级最新通知为准", "note": "[暂无]"},
    {"key": "grad_adv", "name": "智能工厂梯度培育·先进级", "level": "省级", "group": "梯度培育",
     "eligible": lambda p: p.get("level") == "先进级", "amount": _gradient_amt, "status": "active",
     "basis": "省级（先进级）≤100万（首次认定，一次性）", "note": "[真实]"},
    {"key": "grad_exc", "name": "智能工厂梯度培育·卓越级", "level": "国家级", "group": "梯度培育",
     "eligible": lambda p: p.get("level") == "卓越级", "amount": _gradient_amt, "status": "active",
     "basis": "国家级（卓越级及以上）/优秀场景 ≤200万", "note": "[真实]"},
    {"key": "grad_lead", "name": "智能工厂梯度培育·领航级", "level": "国家级", "group": "梯度培育",
     "eligible": lambda p: p.get("level") == "领航级", "amount": _gradient_amt, "status": "none",
     "basis": "领航级暂无明确市级奖补，以国家/省级最新通知为准", "note": "[暂无]"},

    # —— 专精特新（互斥组：三档取高）——
    {"key": "zjtx_innov", "name": "专精特新·创新型中小企业", "level": "省级", "group": "专精特新",
     "eligible": lambda p: p.get("cert") == "创新型中小企业", "amount": _zjtx_amt, "status": "none",
     "basis": "创新型中小企业无直接定额奖励（培育阶段）", "note": "[暂无]"},
    {"key": "zjtx_prov", "name": "专精特新·省级专精特新", "level": "省级", "group": "专精特新",
     "eligible": lambda p: p.get("cert") == "专精特新中小企业", "amount": _zjtx_amt, "status": "active",
     "basis": "省级专精特新中小企业 30万（首次认定，一次性）", "note": "[真实]"},
    {"key": "zjtx_giant", "name": "专精特新·小巨人", "level": "国家级", "group": "专精特新",
     "eligible": lambda p: p.get("cert") == "专精特新小巨人", "amount": _zjtx_amt, "status": "active",
     "basis": "国家级专精特新小巨人 50万；另享上一年度贷款担保费一定比例贴息[真实·贴息比例待补]", "note": "[真实]"},

    # —— 数字化车间（独立，可与梯度叠加）——
    {"key": "digital_ws", "name": "辽宁省数字化车间", "level": "辽宁省", "group": None,
     "eligible": lambda p: bool(p.get("digital_workshop")), "amount": lambda p: 30, "status": "active",
     "basis": "省级数字化车间 ≤30万", "note": "[真实]"},

    # —— 工业设计中心（互斥组：三级取高）——
    {"key": "idc_city", "name": "工业设计中心·市级", "level": "大连市", "group": "工业设计中心",
     "eligible": lambda p: p.get("idc") == "市级", "amount": _idc_amt, "status": "none",
     "basis": "市级工业设计中心无定额奖励", "note": "[真实]"},
    {"key": "idc_prov", "name": "工业设计中心·省级", "level": "辽宁省", "group": "工业设计中心",
     "eligible": lambda p: p.get("idc") == "省级", "amount": _idc_amt, "status": "active",
     "basis": "省级工业设计中心 30万", "note": "[真实]"},
    {"key": "idc_natl", "name": "工业设计中心·国家级", "level": "国家级", "group": "工业设计中心",
     "eligible": lambda p: p.get("idc") == "国家级", "amount": _idc_amt, "status": "active",
     "basis": "国家级工业设计中心 50万", "note": "[真实]"},

    # —— 单项冠军（独立；部分地区与小巨人互斥，需确认）——
    {"key": "champion", "name": "制造业单项冠军", "level": "国家级/省级", "group": None,
     "eligible": lambda p: bool(p.get("champion")), "amount": lambda p: 100, "status": "active",
     "basis": "国家/省制造业单项冠军 不超过100万；注：部分地区与专精特新小巨人互斥申报，需确认", "note": "[真实]"},

    # —— 新型技改（独立）——
    {"key": "tech", "name": "大连市制造业新型技术改造专项", "level": "大连市", "group": None,
     "eligible": lambda p: (p.get("tech_type") in ("设备更新", "新型技改")) and (p.get("tech_invest") or 0) > 0,
     "amount": _tech_amt, "status": "active",
     "basis": "设备更新按投资额10% / 新型技改按20%，单项目最高200万", "note": "[真实]"},

    # —— 高企（独立）——
    {"key": "hightech", "name": "国家高新技术企业", "level": "国家级", "group": None,
     "eligible": lambda p: bool(p.get("is_hightech")), "amount": _hightech_amt, "status": "active",
     "basis": "研发投入阶梯奖励：50万→5万 / 100万→10万 / 1000万→20万；另享所得税15%优惠", "note": "[真实]"},

    # —— 科技型中小企业（独立，研发加计100%减税）——
    {"key": "tech_sme", "name": "科技型中小企业（研发费用加计扣除）", "level": "国家级", "group": None,
     "eligible": lambda p: bool(p.get("is_tech_sme")), "amount": lambda p: 0, "status": "active",
     "basis": "研发费用加计扣除100%（减税，非定额）；与高企可叠加享受", "note": "[真实]"},

    # —— 先进制造业增值税加计抵减（独立）——
    {"key": "vat", "name": "先进制造业企业增值税加计抵减", "level": "国家级", "group": None,
     "eligible": lambda p: bool(p.get("is_hightech")) and (p.get("vat_base") or 0) > 0,
     "amount": _vat_amt, "status": "active",
     "basis": "当期可抵扣进项税额 5%（针对高企制造业）", "note": "[真实]"},

    # —— 超长期特别国债（独立）——
    {"key": "bond", "name": "超长期特别国债·工业设备更新", "level": "国家级", "group": None,
     "eligible": lambda p: (p.get("fixed_asset_invest") or 0) > 0, "amount": _bond_amt, "status": "active",
     "basis": "固定资产投入 15%（国家级贴息类）", "note": "[真实]"},

    # —— 绿色工厂（政策明文暂无补助）——
    {"key": "green", "name": "绿色工厂", "level": "国家级/省级", "group": None,
     "eligible": lambda p: bool(p.get("green_factory")), "amount": lambda p: 0, "status": "none",
     "basis": "30条明文：绿色工厂暂无市级奖补（国家级绿色制造另有配套，以最新通知为准）", "note": "[暂无]"},

    # —— 首台套（待补，30条未含）——
    {"key": "first_set", "name": "首台(套)重大技术装备保险补偿", "level": "国家级", "group": None,
     "eligible": lambda p: bool(p.get("first_set")), "amount": lambda p: None, "status": "pending",
     "basis": "国家工信部+财政部政策，30条未含，待接入补偿比例/封顶数据", "note": "[待补]"},

    # —— 东北振兴金融工具（待补，30条未含）——
    {"key": "revival_fin", "name": "东北振兴政策性贷款/贴息", "level": "国家级", "group": None,
     "eligible": lambda p: (p.get("loan_amount") or 0) > 0, "amount": lambda p: None, "status": "pending",
     "basis": "国开行/进出口银行政策性贷款、专项再贷款贴息，30条未含，待接入利率/贴息口径", "note": "[待补]"},
]


def _safe_amount(pol, profile):
    try:
        return pol["amount"](profile)
    except Exception:
        return None


def _upgrade_suggestions(profile):
    sug = []
    if profile.get("level") in ("基础级", "先进级"):
        nxt = {"基础级": ("先进级", 100), "先进级": ("卓越级", 200)}[profile["level"]]
        sug.append(f"若将申报等级由「{profile['level']}」提升至「{nxt[0]}」，梯度培育奖励可增至约 {nxt[1]} 万元。")
    if profile.get("cert") == "专精特新中小企业":
        sug.append("若进一步认定为专精特新'小巨人'，可多拿约 20 万元（50-30）。")
    if profile.get("cert") == "创新型中小企业":
        sug.append("若升级为省级专精特新/小巨人，专精特新奖励可再增 30~50 万元。")
    if profile.get("idc") in ("市级", "省级"):
        nxt = {"市级": ("省级", 30), "省级": ("国家级", 50)}[profile["idc"]]
        sug.append(f"工业设计中心由「{profile['idc']}」升级至「{nxt[0]}」，可多拿约 {nxt[1]} 万元。")
    if not profile.get("champion"):
        sug.append("若产品市场份额居细分行业前列，可同步申报制造业单项冠军（≤100万），与梯度培育不冲突。")
    return sug


def recommend_policy_package(profile: dict) -> dict:
    """横向拉通多政策 + 最优不冲突求解，输出结构化结论（离线版）。"""
    from collections import defaultdict
    eligible = [p for p in POLICIES if _safe_call(p["eligible"], profile)]
    if not eligible:
        return {"matched": [], "pending": [], "excluded": [], "upgrades": [],
                "total_wan": 0, "text": "当前画像暂不满足已接入政策的硬性条件，建议先补齐资质（见资源库·政策文件库）。"}

    # 互斥组取高
    groups = defaultdict(list)
    nongroup = []
    for p in eligible:
        (groups[p["group"]].append(p) if p["group"] else nongroup.append(p))

    selected = []
    for g, items in groups.items():
        valid = [x for x in items if (_safe_amount(x, profile) or 0) > 0]
        if valid:
            selected.append(max(valid, key=lambda x: _safe_amount(x, profile)))
        else:
            selected.append(items[0])  # 待核定/暂无，列入但不计金额
    selected += nongroup

    matched, pending, excluded = [], [], []
    for p in selected:
        amt = _safe_amount(p, profile)
        if p["status"] == "pending" or amt is None:
            pending.append({"policy": p["name"], "basis": p["basis"], "note": p["note"]})
        elif (amt or 0) > 0:
            matched.append({"policy": p["name"], "level": p["level"],
                            "amount_wan": round(amt, 1), "basis": p["basis"], "note": p["note"]})
        else:
            # 0 元但已接入（如科技型中小、绿色工厂）：放入 excluded 说明区，避免与待补混淆
            excluded.append(f"{p['name']}：已满足但无定额奖励（{p['basis']}）")

    # 互斥未重复享受说明
    for g, items in groups.items():
        if len(items) > 1:
            chosen = [x for x in selected if x in items][0]
            lower = [x["name"] for x in items if x is not chosen]
            excluded.append(f"「{g}」组内取高：已计「{chosen['name']}」，不再重复享受 { '、'.join(lower) }。")

    total = sum(m["amount_wan"] for m in matched)
    upgrades = _upgrade_suggestions(profile)

    names = "、".join(m["policy"] for m in matched)
    parts = []
    if matched:
        parts.append(f"您满足{names}共{len(matched)}项可获资金政策")
    if pending:
        parts.append(f"另有{len(pending)}项待补政策（首台套/东北振兴金融工具等，数据接入后自动测算）")
    text = "；".join(parts) + (f"。当前可测算总额约 {round(total, 1)} 万元（取高、不冲突；封顶以大连最新申报指南为准）。"
                              if matched else "。")

    return {"matched": matched, "pending": pending, "excluded": excluded,
            "upgrades": upgrades, "total_wan": round(total, 1), "text": text}


def _safe_call(fn, profile):
    try:
        return bool(fn(profile))
    except Exception:
        return False


def recommend_policy_package_llm(profile: dict) -> dict:
    """配置大模型时，在离线结论基础上生成更自然的申报建议；未配置则回退离线版。"""
    base = recommend_policy_package(profile)
    if not is_configured():
        return base
    lines = "\n".join(f"- {m['policy']}（{m['level']}）：约 {m['amount_wan']} 万元 — {m['basis']}"
                      for m in base["matched"])
    prompt = (f"你是大连智能制造产业协会的AI顾问。企业画像：{profile}。\n"
              f"已匹配政策与测算：\n{lines}\n"
              f"请用一段正式、鼓励企业'同步申报、应报尽报、取高不冲突'的话术复述上述结论，"
              f"并提示资金含封顶值、以当年政策为准。不要编造额外政策。")
    try:
        narr = call_llm(prompt)
        if narr:
            base["narrative"] = narr
    except Exception:
        pass
    return base


if __name__ == "__main__":
    profile = {
        "industry": "装备制造", "level": "先进级",
        "cert": "专精特新中小企业", "tech_invest": 2000, "tech_type": "新型技改",
        "is_hightech": True, "rnd_invest": 200, "is_tech_sme": True,
        "idc": "省级", "champion": True, "digital_workshop": True,
        "first_set": True, "green_factory": False, "fixed_asset_invest": 1000,
        "vat_base": 100, "loan_amount": 8000,
    }
    rec = recommend_policy_package(profile)
    print("=== 政策包求解结果 ===")
    print(rec["text"])
    print("\n[已选·取高不冲突]")
    for m in rec["matched"]:
        print(f"  - {m['policy']}：{m['amount_wan']} 万  ({m['note']} {m['basis']})")
    print(f"\n[可测算总额] {rec['total_wan']} 万元")
    print("\n[待补政策]")
    for p in rec["pending"]:
        print(f"  - {p['policy']}：{p['basis']}")
    print("\n[互斥/取高说明]")
    for e in rec["excluded"]:
        print(f"  - {e}")
    print("\n[升级建议]")
    for u in rec["upgrades"]:
        print(f"  - {u}")
