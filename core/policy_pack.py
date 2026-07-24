# -*- coding: utf-8 -*-
"""
core/policy_pack.py —— 政策包推荐引擎（改动2，强化F3）

横向拉通「智能工厂梯度培育 / 专精特新 / 数字化车间 / 工业设计中心 / 单项冠军 /
新型技改 / 高企 / 科技型中小 / 研发加计 / 先进制造业增值税 / 超长期国债 / 首台套 /
东北振兴金融工具 / 东北区域省级奖补（辽·吉·黑）」等政策，
并内置「最优不冲突申请组合求解器」：

  · 互斥组取高：同一组内只取最高一档（梯度培育四档、专精特初三档、工业设计中心三级）
  · 叠加上限：大连市奖补以最新申报指南封顶为准（默认不封顶，规则透明可查）
  · 最优选择：给定企业画像 + 申报省份 → 算出"拿满且不冲突"的最大金额组合
  · 透明输出：列出已选 / 因互斥未重复享受 / 待补政策 / 升级建议
  · 区域感知：通过 profile["region"] 选择"辽宁（含大连）/ 黑龙江 / 吉林"，
    仅展示所选省份可叠加的省级奖补；标注"全国/东北"的国家级政策始终参与

资金口径来源：
  · 大连市《惠企政策30条（20260225）》→ 标注 [真实·大连]
  · 《数字辽宁智造强省专项资金（智造强省方向）管理办法》(辽财经规〔2024〕7号)
  · 财政部等《关于优化实施设备更新贷款财政贴息政策的通知》(财金〔2026〕2号)
  · 《黑龙江省推动工业振兴若干政策措施》(黑政办规〔2022〕8号)
  · 《黑龙江省加快推动制造业和中小企业数字化网络化智能化发展若干政策措施》(2023.12)
  · 《吉林省知识产权质押融资补助实施细则》
  · 标注 [真实·东北] 为东北区域省级政策明文值；[暂无] 为政策明文暂无补助

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
    # 国家级（卓越级及以上）/优秀场景 ≤200万[真实·大连]；省级（先进级）≤100万[真实·大连]
    # 基础级、领航级 30条未给明确市级奖补 → [暂无]
    return {"基础级": None, "先进级": 100, "卓越级": 200, "领航级": None}.get(p.get("level"))


def _zjtx_amt(p):
    # 小巨人 50万[真实·大连]、省级专精特新 30万[真实·大连]；创新型中小企业无定额奖励[暂无]
    return {"创新型中小企业": 0, "专精特新中小企业": 30, "专精特新小巨人": 50}.get(p.get("cert"))


def _idc_amt(p):
    # 国家 50万[真实·大连] / 省级 30万[真实·大连] / 市级无[真实]
    return {"市级": 0, "省级": 30, "国家级": 50}.get(p.get("idc"))


def _tech_amt(p):
    # 大连市制造业新型技术改造专项：设备更新10% / 新型技改20%，单项目最高200万[真实·大连]
    t = p.get("tech_type")
    inv = p.get("tech_invest") or 0
    if t == "设备更新":
        return min(inv * 0.10, 200)
    if t == "新型技改":
        return min(inv * 0.20, 200)
    return 0


def _hightech_amt(p):
    # 高企研发投入阶梯奖励[真实·全国]：50万→5万；100万→10万；1000万→20万
    rnd = p.get("rnd_invest") or 0
    if rnd >= 1000:
        return 20
    if rnd >= 100:
        return 10
    if rnd >= 50:
        return 5
    return 0


def _vat_amt(p):
    # 先进制造业企业增值税加计抵减：当期可抵扣进项税 5%[真实·全国]
    if p.get("is_hightech") and (p.get("vat_base") or 0) > 0:
        return (p.get("vat_base") or 0) * 0.05
    return 0


def _bond_amt(p):
    # 超长期特别国债—工业设备更新和技术改造：固定资产投入 15%[真实·全国]
    inv = p.get("fixed_asset_invest") or 0
    return inv * 0.15 if inv > 0 else 0


# —— 东北区域省级奖补测算函数 ——
def _jl_zgsz_after_amt(p):
    # 吉林智改数转事后奖补（吉工信办联规〔2025〕59号）：软硬件投入≥100万按10%，
    # 数字化车间≤300万 / 智能工厂≤1000万 / 未来工厂≤2000万
    inv = p.get("jl_zgsz_invest") or 0
    cap = {"数字化车间": 300, "智能工厂": 1000, "未来工厂": 2000}.get(p.get("jl_zgsz_type"), 1000)
    return min(inv * 0.10, cap) if inv >= 100 else None


def _dl_tech_central_amt(p):
    # 大连新型技改城市试点中央奖补（大工信发〔2025〕38号）：单项目≤总投资20%，最高3000万
    inv = p.get("dl_tech_central_invest") or 0
    return min(inv * 0.20, 3000) if inv > 0 else None


def _hl_digi_factory_amt(p):
    # 黑龙江：经省级认定的智能工厂，按项目合同金额10%一次性补助，最高1000万[真实·东北]
    inv = p.get("hl_digi_invest") or 0
    return min(inv * 0.10, 1000) if inv > 0 else None


def _hl_digi_ws_amt(p):
    # 黑龙江：经省级认定的数字化车间（生产线），按合同金额10%一次性补助，最高200万[真实·东北]
    inv = p.get("hl_digi_invest") or 0
    return min(inv * 0.10, 200) if inv > 0 else None


def _jl_pledge_amt(p):
    # 吉林：知识产权质押融资金额贴息2%，每户年度最高20万[真实·东北]
    amt = p.get("pledge_amount") or 0
    return min(amt * 0.02, 20) if amt > 0 else None


def _first_set_amt(p):
    # 首台(套)重大技术装备：
    #  · 黑龙江按产品实际成交价50%奖励，单台≤200万、每户年合计≤500万[真实·东北]
    #  · 辽宁按《首台套保险费补贴办法》补贴保费；黑龙江对"综合险"按投保费率(≤3%)的80%补偿(≤500万/年)
    price = p.get("first_set_price") or 0
    if price > 0:
        return min(price * 0.50, 200)
    return None  # 需填成交价方可测算奖励额


def _revival_amt(p):
    # 东北振兴金融工具（设备更新贷款贴息）：
    #  · 中央财政贴息 1.5个百分点、贴息≤2年（财金〔2026〕2号）[真实·东北]
    #  · 辽宁贷款贴息≤同期LPR、单项上限1000万；黑龙江技改贴息按LPR给12/24个月、最高800/2500万
    loan = p.get("loan_amount") or 0
    return round(loan * 0.015, 1) if loan > 0 else None  # 按国家1.5%年度贴息口径测算


# ---------------------------------------------------------------------------
# 政策库：每条含 硬性条件判定 + 资金测算 + 互斥组 + 数据状态 + 适用区域
#   amount:  callable(profile) -> 数值(万) 或 None(暂无/待补/需补字段)
#   group:   互斥组标识（同组取高）；None 表示可独立叠加
#   status:  "active" 已接入真实值 | "pending" 待补数据 | "none" 政策明文暂无补助
#   region:  适用区域；"全国"/"东北"始终参与，其余按 profile["region"] 过滤
# ---------------------------------------------------------------------------
POLICIES = [
    # —— 梯度培育（互斥组：四档取一）· 辽宁（含大连）——
    {"key": "grad_basic", "name": "智能工厂梯度培育·基础级", "level": "国家级/省级", "group": "梯度培育",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("level") == "基础级", "amount": _gradient_amt, "status": "none",
     "basis": "基础级暂无明确市级奖补，以国家/省级最新通知为准", "note": "[暂无]"},
    {"key": "grad_adv", "name": "智能工厂梯度培育·先进级", "level": "省级", "group": "梯度培育",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("level") == "先进级", "amount": _gradient_amt, "status": "active",
     "basis": "省级（先进级）≤100万（首次认定，一次性）", "note": "[真实·大连]"},
    {"key": "grad_exc", "name": "智能工厂梯度培育·卓越级", "level": "国家级", "group": "梯度培育",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("level") == "卓越级", "amount": _gradient_amt, "status": "active",
     "basis": "国家级（卓越级及以上）/优秀场景 ≤200万", "note": "[真实·大连]"},
    {"key": "grad_lead", "name": "智能工厂梯度培育·领航级", "level": "国家级", "group": "梯度培育",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("level") == "领航级", "amount": _gradient_amt, "status": "none",
     "basis": "领航级暂无明确市级奖补，以国家/省级最新通知为准", "note": "[暂无]"},

    # —— 专精特新（互斥组：三档取高）· 辽宁（含大连）——
    {"key": "zjtx_innov", "name": "专精特新·创新型中小企业", "level": "省级", "group": "专精特新",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("cert") == "创新型中小企业", "amount": _zjtx_amt, "status": "none",
     "basis": "创新型中小企业无直接定额奖励（培育阶段）", "note": "[暂无]"},
    {"key": "zjtx_prov", "name": "专精特新·省级专精特新", "level": "省级", "group": "专精特新",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("cert") == "专精特新中小企业", "amount": _zjtx_amt, "status": "active",
     "basis": "省级专精特新中小企业 30万（首次认定，一次性）", "note": "[真实·大连]"},
    {"key": "zjtx_giant", "name": "专精特新·小巨人", "level": "国家级", "group": "专精特新",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("cert") == "专精特新小巨人", "amount": _zjtx_amt, "status": "active",
     "basis": "国家级专精特新小巨人 50万（大连市级，一次性）", "note": "[真实·大连]"},

    # —— 数字化车间（独立，可与梯度叠加）· 辽宁（含大连）——
    {"key": "digital_ws", "name": "辽宁省数字化车间", "level": "辽宁省", "group": None,
     "region": "辽宁（含大连）","eligible": lambda p: bool(p.get("digital_workshop")), "amount": lambda p: 30, "status": "active",
     "basis": "省级数字化车间 ≤30万", "note": "[真实·大连]"},

    # —— 工业设计中心（互斥组：三级取高）· 辽宁（含大连）——
    {"key": "idc_city", "name": "工业设计中心·市级", "level": "大连市", "group": "工业设计中心",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("idc") == "市级", "amount": _idc_amt, "status": "none",
     "basis": "市级工业设计中心无定额奖励", "note": "[真实·大连]"},
    {"key": "idc_prov", "name": "工业设计中心·省级", "level": "辽宁省", "group": "工业设计中心",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("idc") == "省级", "amount": _idc_amt, "status": "active",
     "basis": "省级工业设计中心 30万", "note": "[真实·大连]"},
    {"key": "idc_natl", "name": "工业设计中心·国家级", "level": "国家级", "group": "工业设计中心",
     "region": "辽宁（含大连）","eligible": lambda p: p.get("idc") == "国家级", "amount": _idc_amt, "status": "active",
     "basis": "国家级工业设计中心 50万", "note": "[真实·大连]"},

    # —— 单项冠军（独立；部分地区与小巨人互斥，需确认）· 辽宁（含大连）——
    {"key": "champion", "name": "制造业单项冠军", "level": "国家级/省级", "group": None,
     "region": "辽宁（含大连）","eligible": lambda p: bool(p.get("champion")), "amount": lambda p: 100, "status": "active",
     "basis": "国家/省制造业单项冠军 不超过100万；注：部分地区与专精特新小巨人互斥申报，需确认", "note": "[真实·大连]"},

    # —— 新型技改（独立）· 辽宁（含大连）——
    {"key": "tech", "name": "大连市制造业新型技术改造专项", "level": "大连市", "group": None,
     "region": "辽宁（含大连）","eligible": lambda p: (p.get("tech_type") in ("设备更新", "新型技改")) and (p.get("tech_invest") or 0) > 0,
     "amount": _tech_amt, "status": "active",
     "basis": "设备更新按投资额10% / 新型技改按20%，单项目最高200万", "note": "[真实·大连]"},

    # —— 高企（独立，全国）——
    {"key": "hightech", "name": "国家高新技术企业", "level": "国家级", "group": None,
     "region": "全国", "eligible": lambda p: bool(p.get("is_hightech")), "amount": _hightech_amt, "status": "active",
     "basis": "研发投入阶梯奖励：50万→5万 / 100万→10万 / 1000万→20万；另享所得税15%优惠", "note": "[真实·全国]"},

    # —— 科技型中小企业（独立，研发加计100%减税，全国）——
    {"key": "tech_sme", "name": "科技型中小企业（研发费用加计扣除）", "level": "国家级", "group": None,
     "region": "全国", "eligible": lambda p: bool(p.get("is_tech_sme")), "amount": lambda p: 0, "status": "active",
     "basis": "研发费用加计扣除100%（减税，非定额）；与高企可叠加享受", "note": "[真实·全国]"},

    # —— 先进制造业增值税加计抵减（独立，全国）——
    {"key": "vat", "name": "先进制造业企业增值税加计抵减", "level": "国家级", "group": None,
     "region": "全国", "eligible": lambda p: bool(p.get("is_hightech")) and (p.get("vat_base") or 0) > 0,
     "amount": _vat_amt, "status": "active",
     "basis": "当期可抵扣进项税额 5%（针对高企制造业）", "note": "[真实·全国]"},

    # —— 超长期特别国债（独立，全国）——
    {"key": "bond", "name": "超长期特别国债·工业设备更新", "level": "国家级", "group": None,
     "region": "全国", "eligible": lambda p: (p.get("fixed_asset_invest") or 0) > 0, "amount": _bond_amt, "status": "active",
     "basis": "固定资产投入 15%（国家级贴息类）", "note": "[真实·全国]"},

    # —— 绿色工厂（辽宁：30条明文暂无市级奖补）——
    {"key": "green", "name": "绿色工厂（辽宁）", "level": "国家级/省级", "group": None,
     "region": "辽宁（含大连）","eligible": lambda p: bool(p.get("green_factory")), "amount": lambda p: 0, "status": "none",
     "basis": "大连惠企30条明文：绿色工厂暂无市级奖补（国家级绿色制造另有配套，以最新通知为准）", "note": "[暂无]"},

    # —— 首台(套)重大技术装备（东北/全国，已接入真实口径）——
    {"key": "first_set", "name": "黑龙江·首台(套)产品奖励", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: bool(p.get("first_set")), "amount": _first_set_amt, "status": "active",
     "basis": "黑龙江对省工信厅认定的首台(套)产品，按单台(套)实际成交价50%一次性奖励，"
              "单台≤200万、每户年合计≤500万（设备类单价≥50万）。填'首台套成交价'可测奖励额",
     "note": "[真实·东北]"},
    {"key": "first_set_insurance", "name": "首台(套)保险补偿·国家级保费补贴", "level": "国家级", "group": None,
     "region": "东北", "eligible": lambda p: bool(p.get("first_set")), "amount": lambda p: None, "status": "active",
     "basis": "国家级：对符合条件的投保企业按不超过实际缴纳保费80%给予补助，资格审定有效期5年"
              "（工信部联通装〔2024〕89号）。辽宁、吉林执行此国家级保费补贴；黑龙江另设综合险专项（见下）",
     "note": "[真实·东北]"},
    {"key": "hl_fs_insurance", "name": "黑龙江·首台(套)保险补偿（综合险）", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: bool(p.get("hl_fs_insurance")), "amount": lambda p: 50, "status": "active",
     "basis": "黑龙江对企业购买首台(套)产品综合险，按年度保费80%补偿，费率上限3%，补偿期最长3年，"
              "每户企业每年最高补偿50万元",
     "note": "[真实·东北]"},

    # —— 东北振兴金融工具 / 设备更新贷款贴息（东北/全国，已接入真实口径）——
    {"key": "revival_fin", "name": "设备更新贷款财政贴息（东北振兴金融工具）", "level": "国家级/省级", "group": None,
     "region": "东北", "eligible": lambda p: (p.get("loan_amount") or 0) > 0, "amount": _revival_amt, "status": "active",
     "basis": "中央财政设备更新贷款贴息1.5个百分点、贴息≤2年(财金〔2026〕2号)；辽宁贷款贴息≤同期LPR、单项上限1000万；"
              "黑龙江技改贴息按LPR给12/24个月、最高800万/2500万。按国家1.5%年度口径测算",
     "note": "[真实·东北]"},

    # ===================== 东北区域省级奖补（新增） =====================
    # —— 黑龙江：智能工厂 / 数字化车间（按合同金额10%）——
    {"key": "hl_digital_factory", "name": "黑龙江·智能工厂（省级认定）", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: (p.get("hl_digi_invest") or 0) > 0 and bool(p.get("digital_factory_hl")),
     "amount": _hl_digi_factory_amt, "status": "active",
     "basis": "经省级认定的智能工厂，按项目合同金额(含设备+工业软件)10%一次性补助，最高1000万", "note": "[真实·东北]"},
    {"key": "hl_digital_ws", "name": "黑龙江·数字化车间（省级认定）", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: (p.get("hl_digi_invest") or 0) > 0 and bool(p.get("digital_workshop_hl")),
     "amount": _hl_digi_ws_amt, "status": "active",
     "basis": "经省级认定的数字化车间(生产线)，按合同金额10%一次性补助，最高200万", "note": "[真实·东北]"},

    # —— 黑龙江：国家级绿色工厂 100万（与辽宁[暂无]分属不同资金池）——
    {"key": "hl_green", "name": "黑龙江·国家级绿色工厂", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: bool(p.get("green_factory")), "amount": lambda p: 100, "status": "active",
     "basis": "上一年度被评为国家级绿色工厂，一次性奖励100万（黑政办规〔2022〕8号）", "note": "[真实·东北]"},

    # —— 黑龙江：国家级专精特新小巨人 100万（与大连市级50万分属省/市资金池，可叠加）——
    {"key": "hl_giant", "name": "黑龙江·专精特新小巨人（省级奖励）", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: p.get("cert") == "专精特新小巨人", "amount": lambda p: 100, "status": "active",
     "basis": "国家级专精特新'小巨人'一次性奖励100万；与大连市级50万分属省/市不同资金池，可叠加", "note": "[真实·东北]"},

    # —— 黑龙江：省级制造业隐形冠军 50万 ——
    {"key": "hl_hidden_champion", "name": "黑龙江·省级制造业隐形冠军", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: bool(p.get("hidden_champion")), "amount": lambda p: 50, "status": "active",
     "basis": "认定为省级制造业'隐形冠军'企业，一次性奖励50万", "note": "[真实·东北]"},

    # —— 黑龙江：工业设计中心（并入'工业设计中心'互斥组，取高）——
    {"key": "hl_idc_prov", "name": "黑龙江·工业设计中心·省级", "level": "黑龙江省", "group": "工业设计中心",
     "region": "黑龙江", "eligible": lambda p: p.get("idc") == "省级", "amount": lambda p: 100, "status": "active",
     "basis": "省级工业设计中心一次性奖励100万（与辽宁省级30万同组取高）", "note": "[真实·东北]"},
    {"key": "hl_idc_natl", "name": "黑龙江·工业设计中心·国家级", "level": "黑龙江省", "group": "工业设计中心",
     "region": "黑龙江", "eligible": lambda p: p.get("idc") == "国家级", "amount": lambda p: 200, "status": "active",
     "basis": "国家级工业设计中心一次性奖励200万（与辽宁国家级50万同组取高）", "note": "[真实·东北]"},

    # —— 吉林：知识产权质押融资贴息 2%（≤20万/年）——
    {"key": "jl_ip_pledge", "name": "吉林·知识产权质押融资贴息", "level": "吉林省", "group": None,
     "region": "吉林", "eligible": lambda p: (p.get("pledge_amount") or 0) > 0, "amount": _jl_pledge_amt, "status": "active",
     "basis": "知识产权质押融资金额贴息2%，每户年度最高20万；另评估费50%(≤2万)、保险费担保费50%(≤5万)", "note": "[真实·东北]"},

    # ===================== 东北区域补充政策（本轮新增） =====================
    # —— 吉林：智改数转事后奖补（吉工信办联规〔2025〕59号）——
    {"key": "jl_zgsz_after", "name": "吉林·智改数转事后奖补", "level": "吉林省", "group": None,
     "region": "吉林", "eligible": lambda p: (p.get("jl_zgsz_invest") or 0) >= 100, "amount": _jl_zgsz_after_amt, "status": "active",
     "basis": "对工厂(车间)建设软硬件投入≥100万，按10%事后奖补：数字化车间(生产线)≤300万、"
              "智能工厂≤1000万、未来工厂≤2000万（吉工信办联规〔2025〕59号）",
     "note": "[真实·东北]"},

    # —— 大连：新型技改城市试点中央奖补（大工信发〔2025〕38号）——
    {"key": "dl_tech_central", "name": "大连·新型技改中央奖补", "level": "大连市", "group": None,
     "region": "辽宁（含大连）", "eligible": lambda p: (p.get("dl_tech_central_invest") or 0) > 0, "amount": _dl_tech_central_amt, "status": "active",
     "basis": "国家制造业新型技改城市试点中央专项资金：单项目支持≤项目总投资20%，最高3000万元"
              "（大工信发〔2025〕38号）；对国家级智能工厂/链主/省级智能工厂/数字化车间另予50-200万奖励",
     "note": "[真实·大连]"},

    # —— 大连：新型技改标杆奖励（大工信发〔2025〕39号）——
    {"key": "dl_tech_benchmark", "name": "大连·新型技改标杆奖励", "level": "大连市", "group": None,
     "region": "辽宁（含大连）", "eligible": lambda p: bool(p.get("dl_tech_benchmark")), "amount": lambda p: 200, "status": "active",
     "basis": "对国家级智能工厂、产业链链主企业、省级智能工厂、数字化车间等给予50-200万元奖励"
              "（大工信发〔2025〕39号，中央奖补资金约10%按成效支持）",
     "note": "[真实·大连]"},

    # —— 大连：中小企业融资担保补助（大工信发〔2023〕134号）——
    {"key": "dl_sme_guarantee", "name": "大连·中小企业融资担保补助", "level": "大连市", "group": None,
     "region": "辽宁（含大连）", "eligible": lambda p: bool(p.get("dl_sme_guarantee")), "amount": lambda p: 20, "status": "active",
     "basis": "对国家级专精特新小巨人/省级专精特新中小企业上年度按时偿还贷款的担保费给予50%补助，最高20万"
              "（大工信发〔2023〕134号）",
     "note": "[真实·大连]"},

    # —— 大连：小升规奖励（大工信发〔2023〕134号）——
    {"key": "dl_xiaoshenggui", "name": "大连·小升规奖励", "level": "大连市", "group": None,
     "region": "辽宁（含大连）", "eligible": lambda p: bool(p.get("dl_xiaoshenggui")), "amount": lambda p: 10, "status": "active",
     "basis": "对首次纳入规上的工业企业给予5万元一次性奖励（战新企业10万）；连续三年规上再奖3万"
              "（大工信发〔2023〕134号）",
     "note": "[真实·大连]"},

    # —— 辽宁省级：低空经济贷款贴息（辽政发〔2026〕3号）——
    {"key": "ln_lowaltitude", "name": "辽宁·低空经济贷款贴息", "level": "辽宁省", "group": None,
     "region": "辽宁（含大连）", "eligible": lambda p: bool(p.get("ln_lowaltitude")), "amount": lambda p: 500, "status": "active",
     "basis": "对低空经济项目按贷款本金年化1.5%贴息，单项目年最高100万、单企业年最高500万（辽政发〔2026〕3号）",
     "note": "[真实·东北]"},

    # —— 辽宁省级：算力使用补助（辽政发〔2026〕3号）——
    {"key": "ln_compute", "name": "辽宁·算力使用补助", "level": "辽宁省", "group": None,
     "region": "辽宁（含大连）", "eligible": lambda p: bool(p.get("ln_compute")), "amount": lambda p: 200, "status": "active",
     "basis": "对重点行业企业等购买算力服务给予每年最高200万元资金补助（辽政发〔2026〕3号）",
     "note": "[真实·东北]"},

    # —— 辽宁省级：化工设备更新补贴（辽政发〔2026〕3号）——
    {"key": "ln_chemical", "name": "辽宁·化工设备更新补贴", "level": "辽宁省", "group": None,
     "region": "辽宁（含大连）", "eligible": lambda p: bool(p.get("ln_chemical")), "amount": lambda p: 1000, "status": "active",
     "basis": "对化工行业老旧装置设备更新改造，以贷款贴息/担保费补贴/保险保费补贴等形式支持，单企业最高1000万"
              "（辽政发〔2026〕3号）",
     "note": "[真实·东北]"},

    # —— 长春新区：技改/智改数转配套奖励 ——
    {"key": "ccxq_tech", "name": "长春新区·技改/智改数转配套奖励", "level": "长春新区", "group": None,
     "region": "吉林", "eligible": lambda p: bool(p.get("ccxq_tech")), "amount": lambda p: 200, "status": "active",
     "basis": "对获国家/省市支持的技改扩能、智改数转项目，按国家、省市奖励金额的20%、10%给予配套，单企业最高200万"
              "（长春新区推动经济持续向好若干措施）",
     "note": "[真实·东北]"},

    # —— 长春新区：首台套配套奖励 ——
    {"key": "ccxq_fs", "name": "长春新区·首台套配套奖励", "level": "长春新区", "group": None,
     "region": "吉林", "eligible": lambda p: bool(p.get("ccxq_fs")), "amount": lambda p: 50, "status": "active",
     "basis": "企业产品首次纳入工信部首台(套)目录，按国家、省市奖励金额最高20%配套，最高50万"
              "（长春新区推动经济持续向好若干措施）",
     "note": "[真实·东北]"},

    # —— 黑龙江：规上工业企业贷款贴息80%（黑工信融训联规〔2025〕15号）——
    {"key": "hl_loan_80", "name": "黑龙江·规上工业企业贷款贴息(80%)", "level": "黑龙江省", "group": None,
     "region": "黑龙江", "eligible": lambda p: bool(p.get("hl_loan_80")), "amount": lambda p: 1000, "status": "active",
     "basis": "对规上工业企业贷款实付利息的80%给予贴息，单个企业年度最高1000万元"
              "（黑工信融训联规〔2025〕15号，有效期至2026.12.31）",
     "note": "[真实·东北]"},
]


def _safe_amount(pol, profile):
    try:
        return pol["amount"](profile)
    except Exception:
        return None


def _region_ok(pol, selected_regions):
    r = pol.get("region", "辽宁")
    if r in ("全国", "东北"):
        return True
    return r in selected_regions


def _upgrade_suggestions(profile):
    sug = []
    if profile.get("level") in ("基础级", "先进级"):
        nxt = {"基础级": ("先进级", 100), "先进级": ("卓越级", 200)}[profile["level"]]
        sug.append(f"若将申报等级由「{profile['level']}」提升至「{nxt[0]}」，梯度培育奖励可增至约 {nxt[1]} 万元。")
    if profile.get("cert") == "专精特新中小企业":
        sug.append("若进一步认定为专精特新'小巨人'，可多拿约 20 万元（50-30，大连）；若在黑龙江另享省级100万奖励。")
    if profile.get("cert") == "创新型中小企业":
        sug.append("若升级为省级专精特新/小巨人，专精特新奖励可再增 30~50 万元。")
    if profile.get("idc") in ("市级", "省级"):
        nxt = {"市级": ("省级", 30), "省级": ("国家级", 50)}[profile["idc"]]
        sug.append(f"工业设计中心由「{profile['idc']}」升级至「{nxt[0]}」，可多拿约 {nxt[1]} 万元（辽宁）。")
    if not profile.get("champion"):
        sug.append("若产品市场份额居细分行业前列，可同步申报制造业单项冠军（≤100万），与梯度培育不冲突。")
    if profile.get("region") and "黑龙江" in profile["region"] and not profile.get("hidden_champion"):
        sug.append("黑龙江企业对标省级制造业'隐形冠军'（50万），与单项冠军可分别申报。")
    return sug


def recommend_policy_package(profile: dict) -> dict:
    """横向拉通多政策 + 最优不冲突求解，输出结构化结论（离线版）。"""
    from collections import defaultdict
    selected_regions = profile.get("region") or ["辽宁（含大连）"]
    if isinstance(selected_regions, str):
        selected_regions = [selected_regions]

    eligible = [p for p in POLICIES if _safe_call(p["eligible"], profile) and _region_ok(p, selected_regions)]
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
        parts.append(f"另有{len(pending)}项需补充字段或待核定政策（首台套/东北振兴金融工具等）")
    text = "；".join(parts) + (f"。当前可测算总额约 {round(total, 1)} 万元（取高、不冲突；封顶以各省最新申报指南为准）。"
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
    prompt = (f"你是东北区域智能制造产业协会的AI顾问。企业画像：{profile}。\n"
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
        "region": ["辽宁（含大连）", "黑龙江", "吉林"],
        "hl_digi_invest": 3000, "digital_factory_hl": True, "digital_workshop_hl": False,
        "hidden_champion": True, "first_set_price": 400, "pledge_amount": 500,
    }
    rec = recommend_policy_package(profile)
    print("=== 政策包求解结果（东北区域） ===")
    print(rec["text"])
    print("\n[已选·取高不冲突]")
    for m in rec["matched"]:
        print(f"  - {m['policy']}：{m['amount_wan']} 万  ({m['note']} {m['basis']})")
    print(f"\n[可测算总额] {rec['total_wan']} 万元")
    print("\n[需补字段/待核定]")
    for p in rec["pending"]:
        print(f"  - {p['policy']}：{p['basis']}")
    print("\n[互斥/取高说明]")
    for e in rec["excluded"]:
        print(f"  - {e}")
    print("\n[升级建议]")
    for u in rec["upgrades"]:
        print(f"  - {u}")
