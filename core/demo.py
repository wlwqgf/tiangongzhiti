"""
core/demo.py — 天工智梯「全系统案例演示」离线数据 + 生成器（零 Key 可跑）

用途：用户无需充值大模型，即可用三个真实风格的案例工厂（华锐重工/新兴机械/精密电子）
完整演示 ①②③④⑤ 五大模块。生成器为确定性规则引擎（非大模型），内容基于案例脱敏数据与
《要素条件(2025版)》政策阈值，契合"只模拟"诉求。

- ① 企业画像：build_profile_report(form)  -> 六维度评分 + 推荐等级 + 冲稳保 + 改造路径
- ③ 申报书大纲：build_outline(qdata, level, gaps) -> 10 模块分级大纲
- ④ 申报书研判：build_review_report(submission, level) -> 六步预审 + 🔴🟡🔵 三级标记
（⑤ 专家评定已由 pages/5 离线引擎覆盖，本模块复用其案例数据）
"""
import os
import re
from core.knowledge import LEVEL_THRESHOLDS
from core import e_prompts as E

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXPERT_PACK = os.path.join(_ROOT, "expert_pack")

# ============================================================
# 一、三个案例工厂的脱敏演示数据
# ============================================================
CASES = {
    "华锐重工": {
        "label": "华锐重工（先进级·应通过）",
        "level": "先进级",
        "industry": "通用设备制造业",
        "submission": f"{EXPERT_PACK}/1784556664650137524-sample1_先进级_华锐重工.txt",
        "scores": {"智能制造成熟度": 18, "信息基础建设水平": 26, "技术应用先进性": 17,
                   "解决方案示范性和可推广性": 8, "经济社会效益情况": 8, "后续实施计划": 7},
        # ① 表单（中文键，对齐 pages/1 的 user_data）
        "form": {
            "企业名称": "大连华锐重工集团有限公司", "所属行业": "通用设备制造业",
            "年营业收入": 528000, "员工人数": 3650,
            "是否高新技术企业": "是", "是否专精特新企业": "否",
            "是否已有数字化车间/智能工厂认证": "否", "近三年有无安全/环保重大事故": "无",
            "关键设备总数": 150, "已联网关键设备数": 117, "已数控化关键设备数": 128,
            "主要生产工序总数": 25, "已实现自动化生产工序数": 20, "已实现数据采集工序数": 20,
            "关键设备联网率": 82.0, "关键设备数控化率": 85.0,
            "生产工序自动化率": 80.0, "生产工序数据采集率": 80.0,
            "现有业务系统": "ERP, MES, PLM, SCADA, WMS", "系统覆盖数量": 5,
            "是否具备研发设计数字化工具": "是", "是否具备生产计划排程系统": "是",
            "是否具备质量追溯系统": "是", "是否具备能源管理系统": "是",
            "是否具备安全环保数字化系统": "是", "已打通数据集成的业务系统数量": 5,
            "是否具备跨系统数据看板": "是", "供应链协同系统是否打通": "是",
            "是否具备全价值链数据协同": "是", "系统间数据集成贯通程度": "高",
            "研发投入占比": 3.5, "专利数量": 20, "是否开展产品/工艺数字化仿真": "是",
            "AI应用场景数量": 15, "AI应用覆盖比例": 18.0,
            "智能制造能力成熟度评估等级": "三级", "两化融合贯标等级": "AA",
            "近三年智能化改造累计投入": 32000, "全员劳动生产率": 100.0, "关键设备综合效率 OEE": 78.0,
        },
        # ③ 问卷（英文键，对齐 QUESTIONNAIRE_SCHEMA）
        "qdata": {
            "entName": "大连华锐重工集团有限公司", "mainBiz": "高端装备制造/通用设备",
            "industry": "通用设备制造业", "employees": "3650人", "revenue": 528000,
            "factoryName": "华锐重工核心制造基地智能工厂", "totalInvest": 32000, "integrator": "用友网络",
            "systems": ["MES 制造执行系统", "ERP 企业资源计划", "PLM 产品生命周期", "SCADA 数据采集", "WMS 仓储管理", "BI 商业智能"],
            "equipment": ["工业机器人", "数控机床(CNC)", "AGV/AMR", "机器视觉检测", "自动化产线", "PLC/DCS控制系统"],
            "netRate": 82, "prodLines": 8,
            "cmmmDone": "已评估", "cmmmLevel": "三级(系统级集成)", "cmmmScore": 3.45,
            "effEfficiency": 25, "effQuality": 12, "effCost": 18, "effEnergy": 12,
            "investEquip": 20000, "investSoft": 6000, "investInteg": 5000, "investOther": 1000,
            "fundSource": ["企业自筹", "政府补贴"],
            "certs": ["ISO 9001 质量管理", "ISO 14001 环境管理"], "petType": "未认定",
            "safeRecord": "是", "netSecurity": "已评估", "remark": "",
        },
    },
    "新兴机械": {
        "label": "新兴机械（先进级·应拦截）",
        "level": "先进级",
        "industry": "通用机械零部件",
        "submission": f"{EXPERT_PACK}/1784556664710279767-sample2_不合格_新兴机械.txt",
        "scores": {"智能制造成熟度": 2, "信息基础建设水平": 8, "技术应用先进性": 3,
                   "解决方案示范性和可推广性": 2, "经济社会效益情况": 5, "后续实施计划": 8},
        "form": {
            "企业名称": "大连新兴机械加工厂", "所属行业": "通用机械零部件",
            "年营业收入": 800, "员工人数": 45,
            "是否高新技术企业": "否", "是否专精特新企业": "否",
            "是否已有数字化车间/智能工厂认证": "否", "近三年有无安全/环保重大事故": "无",
            "关键设备总数": 18, "已联网关键设备数": 0, "已数控化关键设备数": 2,
            "主要生产工序总数": 10, "已实现自动化生产工序数": 2, "已实现数据采集工序数": 0,
            "关键设备联网率": 0.0, "关键设备数控化率": 11.0,
            "生产工序自动化率": 20.0, "生产工序数据采集率": 0.0,
            "现有业务系统": "Excel", "系统覆盖数量": 0,
            "是否具备研发设计数字化工具": "否", "是否具备生产计划排程系统": "否",
            "是否具备质量追溯系统": "否", "是否具备能源管理系统": "否",
            "是否具备安全环保数字化系统": "否", "已打通数据集成的业务系统数量": 0,
            "是否具备跨系统数据看板": "否", "供应链协同系统是否打通": "否",
            "是否具备全价值链数据协同": "否", "系统间数据集成贯通程度": "低",
            "研发投入占比": 1.0, "专利数量": 0, "是否开展产品/工艺数字化仿真": "否",
            "AI应用场景数量": 0, "AI应用覆盖比例": 0.0,
            "智能制造能力成熟度评估等级": "未评估", "两化融合贯标等级": "未贯标",
            "近三年智能化改造累计投入": 30, "全员劳动生产率": 18.0, "关键设备综合效率 OEE": 45.0,
        },
        "qdata": {
            "entName": "大连新兴机械加工厂", "mainBiz": "通用机械零部件",
            "industry": "通用设备制造业", "employees": "45人", "revenue": 800,
            "factoryName": "新兴机械数字化改造项目", "totalInvest": 30, "integrator": "",
            "systems": [], "equipment": ["数控机床(CNC)"],
            "netRate": 0, "prodLines": 0,
            "cmmmDone": "未评估", "cmmmLevel": "（未填）", "cmmmScore": "",
            "effEfficiency": 10, "effQuality": 0, "effCost": 0, "effEnergy": 0,
            "investEquip": 30, "investSoft": 0, "investInteg": 0, "investOther": 0,
            "fundSource": ["企业自筹"],
            "certs": [], "petType": "未认定",
            "safeRecord": "是", "netSecurity": "未评估", "remark": "",
        },
    },
    "精密电子": {
        "label": "精密电子（基础级·应通过）",
        "level": "基础级",
        "industry": "计算机、通信和其他电子设备制造业",
        "submission": f"{EXPERT_PACK}/1784556664798354131-sample3_基础级_精密电子.txt",
        "scores": {"智能制造成熟度": 10, "信息基础建设水平": 22, "技术应用先进性": 14,
                   "解决方案示范性和可推广性": 7, "经济社会效益情况": 8, "后续实施计划": 9},
        "form": {
            "企业名称": "大连精密电子科技有限公司", "所属行业": "计算机、通信和其他电子设备制造业",
            "年营业收入": 8500, "员工人数": 280,
            "是否高新技术企业": "是", "是否专精特新企业": "否",
            "是否已有数字化车间/智能工厂认证": "否", "近三年有无安全/环保重大事故": "无",
            "关键设备总数": 40, "已联网关键设备数": 26, "已数控化关键设备数": 28,
            "主要生产工序总数": 15, "已实现自动化生产工序数": 12, "已实现数据采集工序数": 12,
            "关键设备联网率": 65.0, "关键设备数控化率": 70.0,
            "生产工序自动化率": 80.0, "生产工序数据采集率": 80.0,
            "现有业务系统": "ERP, MES, SCADA, WMS", "系统覆盖数量": 4,
            "是否具备研发设计数字化工具": "是", "是否具备生产计划排程系统": "否",
            "是否具备质量追溯系统": "是", "是否具备能源管理系统": "否",
            "是否具备安全环保数字化系统": "否", "已打通数据集成的业务系统数量": 2,
            "是否具备跨系统数据看板": "是", "供应链协同系统是否打通": "否",
            "是否具备全价值链数据协同": "否", "系统间数据集成贯通程度": "中",
            "研发投入占比": 4.0, "专利数量": 10, "是否开展产品/工艺数字化仿真": "否",
            "AI应用场景数量": 1, "AI应用覆盖比例": 5.0,
            "智能制造能力成熟度评估等级": "二级", "两化融合贯标等级": "A",
            "近三年智能化改造累计投入": 1200, "全员劳动生产率": 30.0, "关键设备综合效率 OEE": 70.0,
        },
        "qdata": {
            "entName": "大连精密电子科技有限公司", "mainBiz": "SMT贴片/组装",
            "industry": "计算机、通信和其他电子设备制造业", "employees": "280人", "revenue": 8500,
            "factoryName": "精密电子智能制造基地", "totalInvest": 1200, "integrator": "大连智造科技",
            "systems": ["MES 制造执行系统", "ERP 企业资源计划", "SCADA 数据采集", "WMS 仓储管理"],
            "equipment": ["数控机床(CNC)", "机器视觉检测", "自动化产线"],
            "netRate": 65, "prodLines": 3,
            "cmmmDone": "已评估", "cmmmLevel": "二级(局部集成化)", "cmmmScore": 2.15,
            "effEfficiency": 20, "effQuality": 10, "effCost": 15, "effEnergy": 8,
            "investEquip": 900, "investSoft": 200, "investInteg": 100, "investOther": 0,
            "fundSource": ["企业自筹", "政府补贴"],
            "certs": ["ISO 9001 质量管理"], "petType": "未认定",
            "safeRecord": "是", "netSecurity": "未评估", "remark": "",
        },
    },
}


# ============================================================
# 二、关键词信号（对齐 05 参考实现，供④研判）
# ============================================================
def _hit(text, kws):
    return any(k in text for k in kws)


def analyze(text, level):
    signals = {
        "has_mes": _hit(text, E._SIGNAL_KEYWORDS["has_mes"]),
        "has_iot": _hit(text, E._SIGNAL_KEYWORDS["has_iot"]),
        "has_automation": _hit(text, E._SIGNAL_KEYWORDS["has_automation"]),
        "has_digital_design": _hit(text, E._SIGNAL_KEYWORDS["has_digital_design"]),
        "has_ai": _hit(text, E._SIGNAL_KEYWORDS["has_ai"]),
        "has_datashare": _hit(text, E._SIGNAL_KEYWORDS["has_datashare"]),
        "has_safety_env": _hit(text, E._SIGNAL_KEYWORDS["has_safety_env"]),
    }
    covered = [env for env, kws in E._ENV_KEYWORDS.items() if _hit(text, kws)]
    m = re.search(r"总分[：: ]*(\d+\.?\d*)", text)
    maturity = float(m.group(1)) if m else None
    return signals, covered, maturity


# ============================================================
# 三、① 企业画像离线生成器
# ============================================================
def _coverage_from_form(f):
    cov = set()
    if f.get("生产工序自动化率", 0) and f["生产工序自动化率"] > 0:
        cov.add("生产作业")
    systems = str(f.get("现有业务系统", ""))
    if "MES" in systems or f.get("是否具备生产计划排程系统") == "是" or f.get("是否具备质量追溯系统") == "是":
        cov.add("生产管理")
    if "ERP" in systems or "CRM" in systems or f.get("供应链协同系统是否打通") == "是":
        cov.add("运营管理")
    if f.get("是否具备研发设计数字化工具") == "是" or "PLM" in systems:
        cov.add("研发设计")
    if "数字孪生平台" in systems or "工业互联网平台" in systems or f.get("是否开展产品/工艺数字化仿真") == "是":
        cov.add("工厂建设")
    return cov


def _recommend_level(f):
    cnc = f.get("关键设备数控化率", 0) or 0
    net = f.get("关键设备联网率", 0) or 0
    rev = f.get("年营业收入", 0) or 0
    mat_txt = str(f.get("智能制造能力成熟度评估等级", "未评估"))
    _mat_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
    mat_num = _mat_map.get(mat_txt[0], 0) if mat_txt and mat_txt[0] in _mat_map else 0
    cov = _coverage_from_form(f)
    cov_n = len(cov)
    qualifies = {}
    for lv, t in LEVEL_THRESHOLDS.items():
        ok = (cnc >= t["cnc_rate"] and net >= t["network_rate"] and rev >= t["revenue_min"]
              and mat_num >= t["maturity_min"])
        # 环节覆盖要求
        if lv == "基础级":
            ok = ok and cov_n >= 1
        elif lv == "先进级":
            ok = ok and cov_n >= 3
        elif lv in ("卓越级", "领航级"):
            ok = ok and cov_n >= 5
        qualifies[lv] = ok
    order = ["基础级", "先进级", "卓越级", "领航级"]
    rec = "基础级"
    for lv in order:
        if qualifies[lv]:
            rec = lv
    return rec, qualifies


def build_profile_report(f):
    cnc = f.get("关键设备数控化率", 0) or 0
    net = f.get("关键设备联网率", 0) or 0
    auto = f.get("生产工序自动化率", 0) or 0
    coll = f.get("生产工序数据采集率", 0) or 0
    sys_n = f.get("系统覆盖数量", 0) or 0
    integ = f.get("已打通数据集成的业务系统数量", 0) or 0
    rd = f.get("研发投入占比", 0) or 0
    pat = f.get("专利数量", 0) or 0
    ai = f.get("AI应用覆盖比例", 0) or 0
    oee = f.get("关键设备综合效率 OEE", 0) or 0
    mat_txt = str(f.get("智能制造能力成熟度评估等级", "未评估"))

    dims = {
        "装备与自动化": min(100, round((cnc + net + auto + coll) / 4)),
        "软件与系统覆盖": min(100, round(sys_n / 9 * 70 + (40 if integ >= 3 else integ * 10))),
        "互联互通与数据协同": min(100, round(integ / 5 * 100)) if integ else 10,
        "研发与创新能力": min(100, round(rd / 5 * 60 + min(pat, 30) / 30 * 40)),
        "绩效与认证": min(100, round(oee + (20 if mat_txt not in ("未评估", "") else 0))),
        "安全与合规": 90 if f.get("近三年有无安全/环保重大事故") == "无" else 30,
    }
    rec, qualifies = _recommend_level(f)
    gap_count = sum(1 for lv in qualifies if not qualifies[lv])
    # 冲稳保（演示用粗略模型）
    if gap_count == 0:
        prob = {"冲": "70%", "稳": "25%", "保": "5%"}
    elif gap_count == 1:
        prob = {"冲": "40%", "稳": "45%", "保": "15%"}
    else:
        prob = {"冲": "15%", "稳": "40%", "保": "45%"}

    lines = [
        f"# 企业画像与等级推荐报告（离线模拟）",
        "",
        f"**企业**：{f.get('企业名称','')} ｜ **行业**：{f.get('所属行业','')} ｜ **营收**：{f.get('年营业收入','')}万元 ｜ **员工**：{f.get('员工人数','')}人",
        f"**当前关键指标**：数控化率 {cnc}% ｜ 联网率 {net}% ｜ 工序自动化率 {auto}% ｜ 数据采集率 {coll}% ｜ 成熟度 {mat_txt}",
        "",
        "## 一、六维度能力评分",
        "| 维度 | 得分 |",
        "|------|------|",
    ]
    for k, v in dims.items():
        lines.append(f"| {k} | {v} |")
    lines += [
        "",
        f"## 二、推荐申报等级",
        f"**推荐等级：{rec}**（基于《要素条件(2025版)》硬性阈值逐项核对）",
        "",
        "## 三、冲稳保概率模型（演示）",
        f"- 🟥 冲（冲刺更高一档）：{prob['冲']}",
        f"- 🟨 稳（本档通过）：{prob['稳']}",
        f"- 🟩 保（保底/需补强）：{prob['保']}",
        "",
        "## 四、改造路径规划与成本估算（要点）",
    ]
    # 改造路径
    if cnc < 70:
        lines.append(f"- 装备数字化：将关键设备数控化率由 {cnc}% 提升至 ≥70%（先进级门槛），预计投入 800-1500 万元。")
    if net < 80:
        lines.append(f"- 联网改造：设备联网率由 {net}% 提升至 ≥80%，部署 SCADA/工业网关，预计 200-500 万元。")
    if integ < 3:
        lines.append(f"- 系统集成：打通 MES/ERP/PLM 等系统数据（ESB/数据中台），预计 300-800 万元。")
    if ai < 10:
        lines.append(f"- AI 场景：引入机器视觉/预测性维护等，AI 覆盖由 {ai}% 提升至 ≥20%（卓越级门槛）。")
    if mat_txt in ("未评估", ""):
        lines.append("- 成熟度评估：补做 2026 年 CMMM 自评估（www.c3mep.cn），作为申报前置。")
    lines.append("- 注：逐级申报不可跳级；建议先达本档全部要求，再规划下一档。")
    lines.append("")
    lines.append("> 本画像为离线规则模拟，供演示；正式申报请以大模型生成报告及官方评审为准。")
    return "\n".join(lines)


# ============================================================
# 三（补充）、① 改造路径规划与成本估算离线生成器
# ============================================================
def build_upgrade_report(user_data: dict, current_level: str, target_level: str) -> str:
    """零 Key 改造路径规划：对照目标等级阈值逐项算缺口、给动作、估投资区间。"""
    t = LEVEL_THRESHOLDS[target_level]
    cnc = float(user_data.get("关键设备数控化率", 0) or 0)
    net = float(user_data.get("关键设备联网率", 0) or 0)
    rev = float(user_data.get("年营业收入", 0) or 0)
    mat_txt = str(user_data.get("智能制造能力成熟度评估等级", "未评估"))
    _mat_map = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5}
    mat_num = _mat_map.get(mat_txt[0], 0) if mat_txt and mat_txt[0] in _mat_map else 0
    rd = float(user_data.get("研发投入占比", 0) or 0)
    ai = float(user_data.get("AI应用覆盖比例", 0) or 0)
    sys_n = int(user_data.get("系统覆盖数量", 0) or 0)

    # 环节覆盖（与画像口径一致）
    cov = set()
    _sys = str(user_data.get("现有业务系统", ""))
    if float(user_data.get("生产工序自动化率", 0) or 0) > 0:
        cov.add("生产作业")
    if "MES" in _sys or user_data.get("是否具备生产计划排程系统") == "是" or user_data.get("是否具备质量追溯系统") == "是":
        cov.add("生产管理")
    if "ERP" in _sys or user_data.get("供应链协同系统是否打通") == "是":
        cov.add("运营管理")
    if user_data.get("是否具备研发设计数字化工具") == "是" or "PLM" in _sys:
        cov.add("研发设计")
    if user_data.get("是否开展产品/工艺数字化仿真") == "是" or user_data.get("是否具备跨系统数据看板") == "是":
        cov.add("工厂建设")

    steps, total_low, total_high = [], 0, 0

    def _add(title, gap_desc, lo, hi):
        steps.append(f"- {title}：{gap_desc}，预计投入 **{lo}–{hi} 万元**。")
        nonlocal total_low, total_high
        total_low += lo
        total_high += hi

    if cnc < t["cnc_rate"]:
        _add(f"装备数控化（{cnc}%→≥{t['cnc_rate']}%）",
             f"对关键设备增配数控系统/机器人，缺口 {round(t['cnc_rate']-cnc,1)} 个百分点", 800, 1500)
    if net < t["network_rate"]:
        _add(f"设备联网（{net}%→≥{t['network_rate']}%）",
             f"部署 SCADA/工业网关实现应联尽联，缺口 {round(t['network_rate']-net,1)} 个百分点", 200, 500)
    if rev < t["revenue_min"]:
        steps.append(f"- 年营业收入（{rev:.0f} 万 < {t['revenue_min']} 万）：营收为经营规模指标，需通过业务增长达成，**不计入改造投资**，建议先扩产/提质提价。")
    if mat_num < t["maturity_min"]:
        _add(f"成熟度（{mat_txt}→≥{t['maturity_min']}级）",
             f"补做/提升 GB/T 39116 自评估，补齐短板能力域", 30, 80)
    if rd < t["rd_ratio"]:
        steps.append(f"- 研发投入占比（{rd}% < {t['rd_ratio']}%）：研发为经营指标，**不计入改造投资**，建议加大研发费用归集。")
    # 环节覆盖
    _cov_req = {"基础级": 1, "先进级": 3, "卓越级": 5, "领航级": 5}
    need = _cov_req[target_level]
    if len(cov) < need:
        miss = need - len(cov)
        _add(f"环节覆盖（{len(cov)}/5→≥{need}/5）",
             f"补齐 {miss} 个缺失环节（生产作业/生产管理/运营管理/研发设计/工厂建设）的数字化系统", 300 * miss, 800 * miss)
    # 系统覆盖/集成
    if sys_n < 5:
        _add(f"系统覆盖/集成（{sys_n} 个系统）",
             "打通 MES/ERP/PLM 等系统数据（ESB/数据中台），提升集成贯通程度", 300, 800)
    # AI 场景（卓越/领航要求）
    if target_level in ("卓越级", "领航级") and ai < (20 if target_level == "卓越级" else 60):
        _add(f"AI 应用覆盖（{ai}%→≥{'20' if target_level=='卓越级' else '60'}%）",
             "引入机器视觉/预测性维护/智能排产等 AI 场景", 500, 1200)

    lines = [
        f"# 改造路径规划与成本估算清单（离线模拟 · {current_level} → {target_level}）",
        "",
        f"> 依据《要素条件(2025版)》{target_level}硬性阈值逐项核对；投资为**示意性区间**，最终以详细方案为准。",
        "",
        f"## 一、当前指标速览",
        f"- 数控化率 {cnc}% ｜ 联网率 {net}% ｜ 营收 {rev:.0f} 万 ｜ 成熟度 {mat_txt} ｜ 研发占比 {rd}% ｜ AI覆盖 {ai}% ｜ 系统覆盖 {sys_n} 个 ｜ 环节覆盖 {len(cov)}/5",
        "",
        "## 二、改造动作清单（按优先级）",
    ]
    if steps:
        lines += steps
    else:
        lines.append("- ✅ 各项硬性指标已初步达标，重点在于巩固与申报材料打磨，无需大额补强投资。")
    lines += [
        "",
        f"## 三、投资估算合计",
        f"- **合计区间：{total_low}–{total_high} 万元**（不含经营类指标如营收/研发投入）。",
        "",
        "## 四、实施建议",
        f"- 逐级申报不可跳级：先确保 {current_level} 全部达标并稳妥通过，再启动本清单向 {target_level} 的改造。",
        "- 建议分阶段实施：先装备联网与系统集成（见效快），再补环节覆盖与 AI 场景（周期长）。",
        "- 复杂工艺/跨区域政策差异，建议转接协会认证线下专家一对一辅导。",
        "",
        "> 本清单为离线规则模拟，不替代官方评审与正式可研报告；最终投资以企业详细方案与第三方评估为准。",
    ]
    return "\n".join(lines)


# ============================================================
# 四、③ 申报书大纲离线生成器
# ============================================================
MODULE_TITLES = [
    "企业基本信息", "申报工厂基本信息", "智能化建设基础", "智能制造能力成熟度(CMMM)",
    "八大环节建设情况", "建设成效数据（建设前后对比）", "投资预算明细",
    "认证与荣誉", "安全合规情况", "其他补充说明",
]


def build_outline(qdata, level, gaps):
    lines = [
        f"# 智能工厂申报书大纲（离线模拟 · {level}）",
        "",
        f"> 依据《要素条件(2025版)》{level}建设内容与《典型场景指引2025版》8大环节40场景生成。",
        "",
        "## 一、离线缺口分析（对照硬性阈值）",
    ]
    if gaps:
        for g in gaps:
            lines.append(f"- ⚠️ {g}")
        lines.append("- 以下大纲按等级结构生成，缺口项已在对应章节标注【待补齐】。")
    else:
        lines.append("- ✅ 关键硬性指标初步达标，可据此撰写。")
    lines.append("")
    lines.append("## 二、申报书大纲（章节结构）")
    for i, title in enumerate(MODULE_TITLES, 1):
        lines.append(f"{i}. **{title}**")
        if title == "八大环节建设情况":
            lines.append("   - 工厂建设 / 研发设计 / 生产作业 / 生产管理 / 运营管理 五环节对照表（已建/部分/未建）")
        elif title == "建设成效数据（建设前后对比）":
            lines.append("   - 生产效率、良品率、成本、能耗 建设前后对比表")
        elif title == "投资预算明细":
            lines.append("   - 设备/软件/集成/其他 投入分项与资金来源")
    lines.append("")
    lines.append("## 三、典型场景覆盖要点（对齐 40 场景）")
    lines.append("- 按目标等级要求覆盖对应环节场景，标注每个场景的「已建实例 / 建设计划」。")
    lines.append("")
    lines.append("> 本大纲为离线模拟；正式申报书请在大模型辅助下细化各章节量化数据与证据。")
    return "\n".join(lines)


# ============================================================
# 五、④ 申报书研判离线生成器（六步预审）
# ============================================================
def build_review_report(submission_text, level):
    signals, covered, maturity = analyze(submission_text, level)
    t = LEVEL_THRESHOLDS[level]
    red, yellow, blue = [], [], []

    # 步骤2 合规检查
    if maturity is not None and maturity < t["maturity_min"]:
        red.append(f"成熟度 {maturity} 低于 {level} 门槛 ≥{t['maturity_min']}级")
    if level in ("先进级", "卓越级", "领航级") and not signals["has_mes"]:
        red.append("未部署 MES（先进级及以上硬性要求）")
    if level in ("先进级", "卓越级", "领航级") and len(covered) < 3:
        red.append(f"覆盖环节仅 {len(covered)}/5，未达 {level} 覆盖要求")
    if level in ("卓越级", "领航级") and not signals["has_ai"]:
        red.append("未体现 AI 技术应用（卓越/领航级要求 AI 场景 ≥20%/60%）")
    if level in ("卓越级", "领航级") and len(covered) < 5:
        red.append("未覆盖全部五个环节")
    if not signals["has_datashare"] and level != "基础级":
        yellow.append("未充分体现生产经营数据互通共享")
    if maturity is None:
        blue.append("缺失 CMMM 自评估得分，需补充")

    lines = [
        f"# 智能工厂申报书诊断报告（离线模拟 · {level}）",
        "",
        f"**覆盖环节**：{len(covered)}/5（{', '.join(covered) or '无'}） ｜ **成熟度自评估**：{maturity or '缺失'}",
        "",
        "## 步骤1 信息抽取",
        f"- 申报等级：{level}；企业规模/行业由正文提取；关键指标见上方。",
        "",
        "## 步骤2 合规检查（对照《要素条件(2025版)》）",
    ]
    if red:
        lines.append("🔴 **红色（硬性不符合，必须改）**：")
        for r in red:
            lines.append(f"   - {r}")
    else:
        lines.append("🔴 未发现硬性不符合项。")
    lines.append("")
    lines.append("## 步骤3 一致性校验")
    lines.append("- 申报书自述覆盖环节与关键词命中的环节一致性：" + ("一致" if len(covered) >= 1 else "缺失环节"))
    lines.append("")
    lines.append("## 步骤4 证据评估")
    lines.append("- 量化证据强度：" + ("较强（含具体比率/数据）" if (signals["has_iot"] and signals["has_mes"]) else "不足，需补充量化数据"))
    lines.append("")
    lines.append("## 步骤5 三级标记")
    if yellow:
        lines.append("🟡 **黄色（逻辑/数据不一致）**：" + "；".join(yellow))
    if blue:
        lines.append("🔵 **蓝色（表述/证据不充分）**：" + "；".join(blue))
    if not (yellow or blue):
        lines.append("🟡🔵 暂无明显问题。")
    lines.append("")
    lines.append("## 步骤6 诊断结论与转人工建议")
    if red:
        lines.append(f"- **结论**：存在 {len(red)} 项硬性不符合，建议退回补正或降级申报；复杂问题转接协会线下专家。")
    else:
        lines.append("- **结论**：硬性指标基本达标，可进入专家评分环节；建议补充量化证据后提交。")
    lines.append("")
    lines.append("> 本诊断为离线规则模拟，不替代官方评审；最终以专家评定及工信部门审核为准。")
    return "\n".join(lines)


# ============================================================
# 六、F1-F8 辅助功能离线生成器（零 Key 可跑）
# ============================================================
def build_aux_response(aux_name: str, user_input: str, case_form: dict = None) -> str:
    """F1-F8 辅助功能离线回答（基于知识库规则引擎，无需大模型）。"""
    from core.knowledge import LEVEL_THRESHOLDS

    if aux_name == "F1 政策解读":
        return _aux_policy_explain(user_input)
    elif aux_name == "F2 等级自评":
        return _aux_grade_self_eval(user_input, case_form)
    elif aux_name == "F3 政策匹配":
        return _aux_policy_match(user_input, case_form)
    elif aux_name == "F4 范本检索":
        return _aux_template_search(user_input)
    elif aux_name == "F5 补贴测算":
        return _aux_subsidy_calc(user_input)
    elif aux_name == "F6 材料清单":
        return _aux_material_list(user_input)
    elif aux_name == "F7 评审模拟":
        return _aux_review_sim(user_input)
    elif aux_name == "F8 知识问答":
        return _aux_knowledge_qa(user_input, case_form)
    else:
        return f"离线暂不支持【{aux_name}】，请配置模型接口后重试。"


def _aux_policy_explain(text: str) -> str:
    """F1：政策条款通俗解读。"""
    kw_map = {
        "要素条件": ("智能工厂梯度培育要素条件", "工信部发布，含四级等级硬性阈值（数控化率/联网率/营收/成熟度），是申报核心对标依据。"),
        "惠企政策": ("惠企政策30条", "大连市出台，含数字化车间≤50万、先进级≤100万、卓越级≤200万补贴标准。"),
        "管理办法": ("智能工厂梯度培育管理办法", "工信部暂行办法，规定逐级申报不可跳级、复核周期等程序要求。"),
        "典型场景": ("智能制造典型场景指引2025版", "8大环节40场景，是申报书「场景建设情况」章节的填报依据。"),
        "成熟度": ("GB/T 39116 智能制造能力成熟度模型", "国家标准，分一级(基础自动化)~四级(全流程智能化)，基础级/先进级需达二级及以上。"),
        "两化融合": ("两化融合管理体系贯标", "信息化与工业化融合，A级为入门、AAA级为最高，是智能制造能力佐证之一。"),
    }
    found = []
    for k, (title, desc) in kw_map.items():
        if k in text or title in text:
            found.append((k, (title, desc)))
    if not found:
        # 尝试通用匹配
        for k, v in kw_map.items():
            if any(c in text for c in k):
                found.append((k, v))
                break
    lines = ["### 📖 政策解读（离线模拟）\n"]
    if found:
        for _, (title, desc) in found:
            lines.append(f"**{title}**\n- {desc}\n")
    elif text.strip():
        lines.append("- 输入内容未匹配到知识库中的具体政策条款。请尝试输入包含以下关键词的内容：")
        lines.append("  `要素条件` / `惠企政策30条` / `管理办法` / `典型场景` / `成熟度` / `两化融合`\n")
        lines.append("> 如需更详细解读，请配置大模型接口后使用 F1 功能。")
    else:
        lines.append("请粘贴政策条款原文或关键词，例如：\n- 「智能工厂梯度培育要素条件」\n- 「惠企政策30条第3条补贴」\n")
    lines.append("\n> 本解读基于知识库核心政策摘要生成；正式解读请以官方文件原文及协会线下专家意见为准。")
    return "\n".join(lines)


def _aux_grade_self_eval(text: str, case_form: dict = None) -> str:
    """F2：企业现状→建议等级+差距清单。"""
    # 从文本中抽取关键指标
    rev_match = re.search(r"营收[^\d]*(\d[\d,.]*)\s*(万|亿)?", text or "")
    rev = float(rev_match.group(1).replace(",", "")) if rev_match else None
    if rev and rev_match.group(2) == "亿":
        rev = rev * 10000
    net_match = re.search(r"联网率[^\d]*(\d+(?:\.\d+)?)%?", text or "")
    net = float(net_match.group(1)) if net_match else None
    cnc_match = re.search(r"数控化[^\d]*(\d+(?:\.\d+)?)%?", text or "")
    cnc = float(cnc_match.group(1)) if cnc_match else None
    mat_match = re.search(r"成熟度[^一二三四五]*(一|二|三|四|五)级?|(\d+(\.\d+)?)分", text or "")
    mat_txt = ""
    if mat_match:
        mat_txt = mat_match.group(1) or f"{mat_match.group(2)}级"

    # 若有案例数据则优先用
    if case_form:
        rev = rev or case_form.get("年营业收入")
        net = net or case_form.get("关键设备联网率")
        cnc = cnc or case_form.get("关键设备数控化率")
        mat_txt = mat_txt or str(case_form.get("智能制造能力成熟度评估等级", ""))

    rec, qualifies = _recommend_level(case_form or {
        "关键设备数控化率": cnc or 0, "关键设备联网率": net or 0,
        "年营业收入": rev or 0, "智能制造能力成熟度评估等级": mat_txt or "未评估",
        "生产工序自动化率": 0, "现有业务系统": "", "是否具备研发设计数字化工具": "",
    })

    lines = [f"### 🎯 等级自评结果（离线模拟）\n"]
    lines.append(f"**推荐申报等级：{rec}**\n")
    lines.append("## 一、指标达标情况\n")
    lines.append("| 指标 | 当前值 | 基础级 | 先进级 | 卓越级 | 领航级 | 达标 |")
    lines.append("|------|-------|--------|--------|--------|--------|------|")
    rows = [
        ("年营业收入(万)", rev or "未填", LEVEL_THRESHOLDS["基础级"]["revenue_min"],
         LEVEL_THRESHOLDS["先进级"]["revenue_min"], LEVEL_THRESHOLDS["卓越级"]["revenue_min"],
         LEVEL_THRESHOLDS["领航级"]["revenue_min"]),
        ("数控化率%", cnc or "未填",
         LEVEL_THRESHOLDS["基础级"]["cnc_rate"], LEVEL_THRESHOLDS["先进级"]["cnc_rate"],
         LEVEL_THRESHOLDS["卓越级"]["cnc_rate"], LEVEL_THRESHOLDS["领航级"]["cnc_rate"]),
        ("联网率%", net or "未填",
         LEVEL_THRESHOLDS["基础级"]["network_rate"], LEVEL_THRESHOLDS["先进级"]["network_rate"],
         LEVEL_THRESHOLDS["卓越级"]["network_rate"], LEVEL_THRESHOLDS["领航级"]["network_rate"]),
        ("成熟度", mat_txt or "未评估",
         "≥二级", "≥二级", "≥三级", "≥四级"),
    ]
    for r in rows:
        ok = "✅" if r[0] == "成熟度" else "—"
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[5]} | {ok} |")

    gaps = []
    if rev and rec != "基础级" and rev < LEVEL_THRESHOLDS.get(rec, {}).get("revenue_min", 99999):
        gaps.append(f"营收未达{rec}门槛")
    if cnc and cnc < LEVEL_THRESHOLDS.get(rec, {}).get("cnc_rate", 100):
        gaps.append(f"数控化率不足{rec}要求")
    if net and net < LEVEL_THRESHOLDS.get(rec, {}).get("network_rate", 100):
        gaps.append(f"联网率不足{rec}要求")

    lines.append("\n## 二、差距清单\n")
    if gaps:
        for g in gaps:
            lines.append(f"- ⚠️ {g}")
    else:
        lines.append("- ✅ 推荐等级各项指标初步达标")
    lines.append("\n## 三、整改路径\n")
    lines.append(f"- 当前建议从 **{rec}** 起步申报（逐级申报不可跳级）")
    lines.append("- 详细改造路径请到「①企业画像与等级推荐」获取六维度评分与成本估算")
    lines.append("\n> 本自评为离线规则模拟；正式评定请以大模型深度分析及协会专家审核为准。")
    return "\n".join(lines)


def _aux_policy_match(text: str, case_form: dict = None) -> str:
    """F3：政策匹配列表。"""
    industry_keywords = ["装备制造", "汽车", "电子", "化工", "医药", "新材料", "食品", "金属", "通用设备", "专用设备"]
    ind = next((i for i in industry_keywords if i in (text or "")), None)

    lines = ["### 📋 匹配政策列表（离线模拟）\n"]
    policies = [
        ("🔴 高匹配", "智能工厂梯度培育要素条件（2025版）", "所有制造业企业", "四级等级硬性门槛"),
        ("🟡 高匹配", "惠企政策30条", "大连市注册企业", "数字化车间≤50万 / 先进级≤100万 / 卓越级≤200万"),
        ("🟡 高匹配", "2026辽宁省智能工厂培育通知", "辽宁省内企业", "省级认定流程与时间窗口"),
        ("🟢 推荐", "大连市三年行动计划（2026-2028）", "大连市制造业", "市级配套支持与数字化转型方向"),
        ("🟢 参考", "GB/T 39116 成熟度国家标准", "所有企业", "CMMM 自评估方法与能力域划分"),
        ("🟢 参考", "典型场景指引2025版", "所有企业", "8大环节40场景填报模板"),
    ]

    lines.append("| 匹配度 | 政策名称 | 适用对象 | 核心内容 |")
    lines.append("|--------|---------|---------|---------|")
    for m, name, scope, content in policies:
        lines.append(f"| {m} | {name} | {scope} | {content} |")

    if ind:
        lines.append(f"\n> 检测到行业：**{ind}** — 以上政策均适用该行业。")
    lines.append("\n> 完整34份文档的知识库索引见「F8 知识问答」输入'全部政策'查看。")
    return "\n".join(lines)


def _aux_template_search(text: str) -> str:
    """F4：范本片段检索。"""
    templates = [
        ("华锐重工·卓越级", "9大章结构", "封面→基本信息→场景建设→成效→投资预算→进度→预期效益→保障措施→风险分析", "适用于大型装备制造/营收≥2亿/成熟度三级以上"),
        ("华锐重工·先进级", "7大章结构", "封面→基本信息→场景建设→成效→投资预算→进度→预期效益→保障措施", "适用于中型制造/营收5000万以上/MES已部署"),
        ("中集特种物流·先进级", "7大章结构", "封面→基本信息→场景建设→成效→投资预算→进度→预期效益→保障措施", "适用于物流/仓储行业参考"),
    ]
    lines = ["### 📚 范本检索（离线模拟）\n"]
    matched = []
    for name, struct, chapters, note in templates:
        if not text.strip() or any(k in text for k in name.split("·")[0].split()[0] if len(name.split("·")[0]) > 2):
            matched.append((name, struct, chapters, note))
    if not matched and text.strip():
        # 关键词模糊匹配
        for name, struct, chapters, note in templates:
            for kw in ["卓越级", "先进级", "基础级", "装备", "物流", "电子"]:
                if kw in text:
                    matched.append((name, struct, chapters, note))
                    break

    if matched:
        for name, struct, chapters, note in matched:
            lines.append(f"#### {name}\n")
            lines.append(f"- **章节结构**：{struct}")
            lines.append(f"- **章节明细**：{chapters}")
            lines.append(f"- **适用说明**：{note}\n")
    elif text.strip():
        lines.append("- 未检索到匹配范本。可用关键词：`华锐重工` / `中集物流` / `卓越级` / `先进级` / `装备` / `电子`\n")
    else:
        lines.append("请输入检索关键词，如：\n- `卓越级申报书结构`\n- `华锐重工范本`\n- `先进级章节目录`\n")

    lines.append("> 茌本全文在知识库 B1-B6 中；如需提取具体段落，请配置大模型接口。")
    return "\n".join(lines)


def _aux_subsidy_calc(text: str) -> str:
    """F5：补贴测算。"""
    lines = ["### 💰 补贴测算（离线模拟）\n"]

    # 提取投资额
    inv_match = re.search(r"(\d[\d,.]*)\s*万", text or "")
    inv = float(inv_match.group(1).replace(",", "")) if inv_match else None

    # 提取目标等级
    lv_text = ""
    for lv in ["领航级", "卓越级", "先进级", "基础级"]:
        if lv in (text or ""):
            lv_text = lv
            break

    lines.append("| 等级 | 补贴比例 | 市级上限 | 省级配套 | 适用条件 |")
    lines.append("|------|---------|---------|---------|---------|")
    levels_info = [
        ("基础级", "资格型", "无直接补贴", "视地方配套", "规模以上工业企业 + CMMM≥二级"),
        ("先进级", "投资×10%", "≤100万", "视省级政策", "营收≥5000万 + 联网率≥80%"),
        ("卓越级", "投资×10%", "≤200万", "视省级政策", "营收≥2亿 + 联网率≥95%"),
        ("领航级", "投资×10%", "≤200万", "视国家级政策", "营收≥5亿 + CMMM≥四级"),
    ]
    for lv, rate, cap, prov, cond in levels_info:
        amt = min(inv * 0.10, float(cap.replace("≤", "").replace("万", "")) if cap.startswith("≤") else 0) if inv else "—"
        lines.append(f"| {lv} | {rate} | {cap} | {prov} | {cond} |")

    if inv and lv_text:
        idx = {"基础级": 0, "先进级": 1, "卓越级": 2, "领航级": 3}.get(lv_text, -1)
        if idx >= 1:
            rate_val = 0.10
            cap_val = float(levels_info[idx][2].replace("≤", "").replace("万", ""))
            est = min(inv * rate_val, cap_val)
            lines.append(f"\n按您投资 **{inv:.0f} 万** 申报 **{lv_text}**：")
            lines.append(f"- 预估补贴：约 **{est:.0f} 万元**（投资×10%，封顶 {cap_val} 万）")
    elif inv and not lv_text:
        lines.append(f"\n按您投资 **{inv:.0f} 万** 的各等级预估：")
        for lv, rate, cap, _, _ in levels_info[1:]:
            cv = cap.replace("≤", "").replace("万", "")
            lines.append(f"- **{lv}**：约 **{min(inv*0.10,float(cv)):.0f} 万**（封顶 {cv} 万）")
    elif not inv:
        lines.append("\n请补充投资金额，格式如：`投资2000万元` 或 `总投资3000万`")

    lines.append("\n> 补贴金额为示意性估算，以当年财政预算与最新政策为准；《惠企政策30条》第2-3条为权威来源。")
    return "\n".join(lines)


def _aux_material_list(level: str) -> str:
    """F6：材料清单。"""
    mats = {
        "基础级": [
            ("必需", "《智能工厂申报书》（基础级模板）"),
            ("必需", "营业执照复印件"),
            ("必需", "统一社会信用代码证"),
            ("必需", "近三年财务审计报告"),
            ("必需", "CMMM 自评估报告（二级及以上）"),
            ("必需", "真实性承诺函（盖章）"),
            ("选填", "数字化车间/智能工厂相关认证证书"),
            ("选填", "专利/软著等知识产权证明"),
            ("选填", "ISO 9001/14001 等管理体系认证"),
        ],
        "先进级": [
            ("必需", "《智能工厂申报书》（先进级模板）"),
            ("必需", "推荐单位盖章的推荐表"),
            ("必需", "CMMM 自评估报告（二级及以上）"),
            ("必需", "近三年财务审计报告 + 无事故证明"),
            ("必需", "主要系统截图/部署架构图"),
            ("必需", "MES/ERP 等核心系统合同/验收单"),
            ("必需", "建设成效量化对比数据表"),
            ("必需", "真实性承诺函（盖章）"),
            ("选填", "专精特新/高新技术企业证书"),
            ("选填", "两化融合贯标证书"),
        ],
        "卓越级": [
            ("必需", "《智能工厂申报书》（卓越级9章模板）"),
            ("必需", "省工信厅推荐函"),
            ("必需", "CMMM 自评估报告（三级及以上）"),
            ("必需", "完整投资决算报告 + 第三方审计"),
            ("必需", "8大环节40场景覆盖详表 + 实例照片"),
            ("必需", "经济效益专项审计报告"),
            ("必需", "知识产权/专利清单"),
            ("必需", "安全合规评估报告"),
            ("必需", "后续实施计划（2026-2028）"),
            ("选填", "国家/省级荣誉/标杆案例证明"),
        ],
        "领航级": [
            ("必需", "《智能工厂申报书》（参照卓越级扩展）"),
            ("必需", "工信部预通知回执"),
            ("必需", "CMMM 自评估报告（四级）"),
            ("必需", "国际竞争力分析报告"),
            ("必需", "全价值链数据协同方案"),
            ("必需", "AI 应用场景 ≥60% 证明材料"),
            ("必需", "行业影响力/推广案例集"),
        ],
    }
    target = level if level in mats else "先进级"
    items = mats[target]

    lines = [f"### 📋 材料清单（{target} · 离线模拟）\n"]
    lines.append("| 类型 | 材料 |")
    lines.append("|------|------|")
    for typ, name in items:
        lines.append(f"| {'✅ 必需' if typ=='必需' else '⬜ 选填'} | {name} |")

    lines.append(f"\n> 共 **{len(items)}** 项（必需 {[t for t,n in items if t=='必需'].__len__()} 项 / 选填 {[t for t,n in items if t=='选填'].__len__()} 项）。")
    lines.append("> 正式材料清单以当年度通知附件为准；模板可参考知识库 B4/B5 文档。")
    return "\n".join(lines)


def _aux_review_sim(text: str) -> str:
    """F7：评审模拟（基于关键词信号）。"""
    if not text.strip():
        return "### 🔍 评审模拟（离线模拟）\n\n请粘贴申报书草稿或摘要，系统将基于关键词进行模拟专家提问。\n"

    signals, covered, maturity = analyze(text, "先进级")  # 默认用先进级做基准
    q_base = []
    a_base = []

    if not signals["has_mes"] and "mes" not in text.lower():
        q_base.append("贵厂是否已部署 MES 制造执行系统？如有，请描述其功能模块与车间覆盖率。")
    if not signals["has_iot"]:
        q_base.append("请说明当前设备联网方式（工业网关/PLC直连/OPCUA？），已实现实时采集的关键参数有哪些？")
    if not signals["has_digital_design"]:
        q_base.append("研发设计环节是否引入了 CAD/CAM/CAE 或 PLM 系统？仿真验证覆盖哪些工艺？")
    if not signals["has_ai"] and "ai" not in text.lower():
        q_base.append("是否有机器视觉检测、预测性维护、智能排产等 AI 场景？覆盖率约多少？")
    if len(covered) < 3:
        q_base.append("当前智能化覆盖了哪些环节？（生产作业/生产管理/运营管理/研发设计/工厂建设）")
    if maturity is None:
        q_base.append("请提供 GB/T 39116 自评估得分或等级，作为成熟度判定依据。")

    risks = []
    if len(covered) < 3:
        risks.append(("🔴 高风险", f"仅覆盖 {len(covered)}/5 个环节，先进级要求至少 3 个"))
    if maturity is None:
        risks.append(("🟡 中风险", "缺少 CMMM 自评估得分，可能被要求补交"))
    if not signals["has_datashare"]:
        risks.append(("🟡 中风险", "跨系统数据互通共享证据不足"))
    if len(text) < 300:
        risks.append(("🟡 中风险", "提交内容过短，可能无法支撑完整评审"))

    lines = ["### 🔍 评审模拟（离线模拟）\n"]
    lines.append(f"**覆盖环节**：{len(covered)}/5（{', '.join(covered) or '无'}）｜ **成熟度**：{maturity or '缺失'}\n")
    lines.append("## 模拟专家提问\n")
    if q_base:
        for i, q in enumerate(q_base, 1):
            lines.append(f"Q{i}. {q}")
    else:
        lines.append("- ✅ 基于关键词分析，未发现明显缺失项（但内容较短时可能遗漏细节）。")

    lines.append("\n## 风险点提示\n")
    if risks:
        for level, desc in risks:
            lines.append(f"- {level}：{desc}")
    else:
        lines.append("- ✅ 未识别明显风险项")

    lines.append("\n> 本模拟基于离线关键词引擎，不替代真实专家评审；复杂问题转接协会线下专家。")
    return "\n".join(lines)


def _aux_knowledge_qa(text: str, case_form: dict = None) -> str:
    """F8：通用知识问答（意图识别 → 规则回复）。"""
    t = (text or "").lower()
    intent_rules = [
        ("等级体系", ["几个等级", "几级", "等级体系", "分级"],
         "智能工厂分为 **四个等级**：基础级（市级认定）→ 先进级（省级）→ 卓越级（部级）→ 领航级（部级最高）。**逐级申报，不可跳级**。"),
        ("申报流程", ["怎么报", "流程", "步骤", "时间", "窗口"],
         "申报流程：① 企业自评 → ② 市级推荐 → ③ 省级/部级评审 → ④ 公示认定。每年 3–6 月为集中申报窗口，以当年通知为准。"),
        ("补贴标准", ["补多少钱", "补贴多少", "奖补", "资金"],
         "补贴参考（惠企政策30条）：\n- 数字化车间 ≤ **50万**\n- 先进级 ≤ **100万**\n- 卓越级/领航级 ≤ **200万**\n以投资额×比例计算，最终以财政预算为准。"),
        ("指标门槛", ["门槛", "要求", "指标", "数控化率", "联网率", "营收", "成熟度"],
         f"各等级核心门槛（要点）：\n| 指标 | 基础级 | 先进级 | 卓越级 | 领航级 |\n|---|---|---|---|---|\n"
         f"| 数控化率 | ≥50% | ≥70% | ≥90% | ≥95% |\n"
         f"| 联网率 | ≥60% | ≥80% | ≥95% | 100% |\n"
         f"| 营收(万) | 无硬性 | ≥5000 | ≥20000 | ≥50000 |\n"
         f"| 成熟度 | ≥二级 | ≥二级 | ≥三级 | ≥四级 |\n"),
        ("案例参考", ["案例", "别人", "例子", "通过", "成功"],
         "脱敏案例（知识库）：\n- **华锐重工**（装备制造）→ 先进级通过（MES+PLM+SCADA 全覆盖）\n- **精密电子**（电子制造）→ 基础级通过（SMT 产线+MES+WMS）\n"
         "- **新兴机械**（零部件）→ 先进级未通过（缺 MES/联网率低）\n"
         "更多案例可在「②政策问答」中查询。"),
    ]

    for topic, kws, answer in intent_rules:
        if any(kw in t for kw in kws):
            return f"### 💬 知识问答（离线模拟）\n\n{answer}\n\n> 来源：《要素条件2025版》《惠企政策30条》知识库摘要。如需更深入分析请配置大模型接口。"

    # 兜底
    default = (
        "我可以帮您解答以下类别（直接输入问题即可）：\n\n"
        "- **等级体系**：智能工厂分几级？能否跳级？\n"
        "- **申报流程**：怎么申报？什么时候？需要什么材料？\n"
        "- **补贴标准**：能补多少钱？计算方式是什么？\n"
        "- **指标门槛**：各级别对数控化率/联网率/营收的要求？\n"
        "- **案例参考**：有哪些通过的案例？同行业怎么做的？\n\n"
        "> 示例：「我们是装备制造，年营收1.5亿，适合报哪个等级？」"
    )
    return f"### 💬 知识问答（离线模拟）\n\n{default}"


# ============================================================
# 七、F1-F8 各功能的案例示例输入（用于自动填充）
# ============================================================
AUX_DEMO_INPUTS = {
    "F1 政策解读": "智能工厂梯度培育要素条件（2025版）规定了四级智能工厂的硬性指标门槛。",
    "F2 等级自评": "我们是一家装备制造企业，年营收约8000万元，设备联网率65%，数控化率70%，已部署ERP和CAD软件。",
    "F3 政策匹配": "装备制造行业，年营收8000万元，想了解可以申请哪些政策和补贴。",
    "F4 范本检索": "先进级申报书的章节结构和目录是什么样的？",
    "F5 补贴测算": "计划投资2000万元进行智能化改造，想申请先进级智能工厂。",
    "F6 材料清单": "先进级",
    "F7 评审模拟": "我司已完成MES和ERP部署，设备联网率达82%，生产效率提升25%，良品率提升12%，计划申报先进级。",
    "F8 知识问答": "智能工厂有几个等级？能不能直接报先进级？",
}

