"""
core/checklist.py — 模块① 企业自评材料清单

依据 GB/T 39116-2020《智能制造能力成熟度模型》与
GB/T 39117-2020《智能制造能力成熟度评估方法》设计。
对应 c3mep.cn（中国电子技术标准化研究院·智能制造能力成熟度评估平台）
官方自评所需材料清单。

5 大能力域 = 4 个一级维度 + 1 个基础信息域
- 基础与资质
- 人员能力（组织战略 + 人员技能）
- 技术能力（数据 + 集成 + 信息安全）
- 资源能力（装备 + 网络）
- 制造能力（设计 + 生产 + 物流 + 销售 + 服务）

自评等级（一级→五级）：规划 → 规范 → 集成 → 优化 → 引领
"""
from __future__ import annotations

# ============================================================
# 材料清单 (5 组 / 共 25 项)
# 每项 = 企业完成 c3mep 自评需要提前准备的素材
# ============================================================
CHECKLIST = [
    {
        "key": "basic",
        "title": "📋 基础与资质信息",
        "sub_title": "对应 c3mep 自评表头与基本信息表（封面信息）",
        "items": [
            {"id": "company_basic", "name": "企业基本信息",
             "desc": "企业名称、统一社会信用代码、注册地址、邮编、联系人、电话、邮箱",
             "evidence": "营业执照 / 公司官网"},
            {"id": "industry_class", "name": "行业类别与代码",
             "desc": "按 GB/T 4754 国民经济行业分类填写 (如 C35 专用设备、C39 电气机械)",
             "evidence": "工商登记 / 行业代码表"},
            {"id": "biz_overview", "name": "经营概况",
             "desc": "近 3 年营业收入、员工总数、主营业务范围、主导产品/服务清单",
             "evidence": "审计报告 / 公司年报"},
            {"id": "certifications", "name": "现有资质与认定",
             "desc": "高新技术企业、专精特新(创新型/省级/小巨人)、ISO 9001/14001/45001、"
                     "数字化车间、智能工厂、绿色工厂等",
             "evidence": "证书扫描件 / 认定文件"},
            {"id": "eval_history", "name": "过往自评 / 贯标记录",
             "desc": "是否做过 c3mep 自评或两化融合贯标, 等级/分数/有效期",
             "evidence": "历史报告 / 贯标证书"},
        ],
    },
    {
        "key": "people",
        "title": "👥 人员能力（组织战略 + 人员技能）",
        "sub_title": "GB/T 39116 5.1 — 数字化战略与人才队伍",
        "items": [
            {"id": "org_structure", "name": "信息化/数字化部门设置",
             "desc": "是否设立独立部门、职责范围、人员规模、汇报关系（建议向 CIO/CDO 汇报）",
             "evidence": "组织架构图 / 部门职责文件"},
            {"id": "digital_strategy", "name": "数字化战略规划文件",
             "desc": "3-5 年规划、年度目标、预算安排、董事会决议",
             "evidence": "战略文档 / 决议文件 / 年度预算"},
            {"id": "talent_pool", "name": "数字化人才清单",
             "desc": "IT/OT/数字化岗位人数、学历、职称、专业资质（建造师/软考等）",
             "evidence": "花名册 / 简历 / 资质证书"},
            {"id": "training_kpi", "name": "培训计划与考核",
             "desc": "年度培训计划、培训记录、数字化能力考核 KPI（人均学时/认证数）",
             "evidence": "培训记录表 / 绩效文件"},
        ],
    },
    {
        "key": "technology",
        "title": "💻 技术能力（数据 + 集成 + 信息安全）",
        "sub_title": "GB/T 39116 5.2 — 数据资产、系统集成、网络安全",
        "items": [
            {"id": "data_assets", "name": "数据采集与存储",
             "desc": "关键工序/设备的数据采集范围、频度、存储方式、数据治理制度",
             "evidence": "数据字典 / 管理制度"},
            {"id": "system_list", "name": "现有信息系统清单",
             "desc": "ERP / MES / PLM / SCM / CRM / QMS / WMS / TMS / EMS / OA 等系统部署情况",
             "evidence": "系统台账 / 资产清单"},
            {"id": "integration_arch", "name": "系统集成架构图",
             "desc": "系统间接口数量、集成方式(接口/ESB/中台)、数据打通率",
             "evidence": "架构图 / 接口清单"},
            {"id": "info_security", "name": "信息安全等级保护",
             "desc": "等保定级(等保二级/三级)、备案号、数据/网络安全制度",
             "evidence": "等保备案证 / 安全管理制度"},
        ],
    },
    {
        "key": "resource",
        "title": "🛠 资源能力（装备 + 网络）",
        "sub_title": "GB/T 39116 5.3 — 工业装备、工业网络",
        "items": [
            {"id": "equipment_list", "name": "关键设备清单与状态",
             "desc": "关键设备总数、数控化率、联网率、设备台账（按工位/工序统计）",
             "evidence": "设备台账 / OEE 报表"},
            {"id": "auto_collection", "name": "自动化与数据采集覆盖",
             "desc": "已实现自动化工序数、数据采集工序数、覆盖率",
             "evidence": "工序清单 / 采集点表"},
            {"id": "network_topo", "name": "工业控制网络拓扑",
             "desc": "现场总线、工业以太网、5G / OPC-UA / MQTT 应用情况",
             "evidence": "网络拓扑图"},
        ],
    },
    {
        "key": "manufacturing",
        "title": "🏭 制造能力（设计 + 生产 + 物流 + 销售 + 服务）",
        "sub_title": "GB/T 39116 5.4 — 全制造过程数字化",
        "items": [
            {"id": "design_digital", "name": "研发设计数字化",
             "desc": "PLM / CAD / CAE / CAPP 应用、数字化仿真覆盖率",
             "evidence": "设计工具清单 / 项目案例"},
            {"id": "procurement_sys", "name": "采购管理数字化",
             "desc": "SRM / 供应商门户、ERP 集成、订单自动化",
             "evidence": "系统截图 / 流程文件"},
            {"id": "aps_mes", "name": "计划与排程 (APS/MES)",
             "desc": "是否部署 APS、高级排产算法、与 ERP 集成情况",
             "evidence": "系统截图 / 排产规则"},
            {"id": "production_auto", "name": "生产作业自动化",
             "desc": "关键工序自动化、产线数据采集、看板可视化",
             "evidence": "现场照片 / 看板截图"},
            {"id": "equipment_mgmt", "name": "设备管理 (EAM/OEE)",
             "desc": "设备点检、故障预测、OEE 统计、预测性维护",
             "evidence": "EAM 报表 / 维护工单"},
            {"id": "safety_env_sys", "name": "安全环保系统",
             "desc": "EHS 数字化、能耗监测、碳排放台账",
             "evidence": "EHS 系统截图"},
            {"id": "warehouse_logistics", "name": "仓储与物流 (WMS/TMS)",
             "desc": "WMS 应用、TMS 配送调度、自动化立库 / AGV",
             "evidence": "WMS / TMS 截图"},
            {"id": "crm_sales", "name": "销售与客户管理 (CRM)",
             "desc": "CRM 应用、客户画像、订单全流程可视化",
             "evidence": "CRM 截图"},
            {"id": "service_digital", "name": "客户服务与远程运维",
             "desc": "客户档案、在线监测、远程运维、预测性服务",
             "evidence": "服务系统截图"},
        ],
    },
]


# ============================================================
# 扁平化索引 / 进度统计
# ============================================================
def flat_items():
    """把所有组的 items 摊平成单层 list, 每项附带 group 信息。"""
    out = []
    for grp in CHECKLIST:
        for it in grp["items"]:
            out.append({**it, "group": grp["key"], "group_title": grp["title"]})
    return out


def total_count() -> int:
    return sum(len(g["items"]) for g in CHECKLIST)


def progress(session_state) -> tuple:
    """返回 (已完成数, 总数, 百分比)。"""
    done = 0
    for it in flat_items():
        if session_state.get(f"chk_{it['id']}", False):
            done += 1
    total = total_count()
    pct = round(done / total * 100) if total else 0
    return done, total, pct


def group_progress(session_state, group_key: str) -> tuple:
    """返回某组的 (已完成数, 组总项数)。"""
    grp = next((g for g in CHECKLIST if g["key"] == group_key), None)
    if not grp:
        return 0, 0
    done = sum(
        1 for it in grp["items"] if session_state.get(f"chk_{it['id']}", False)
    )
    return done, len(grp["items"])


# ============================================================
# 案例预设: 大连融科储能 (三级/集成级) — 全材料就绪态
# ============================================================
CASE_PRESET_NAME = "案例预设：大连融科储能（三级 / 集成级）"
CASE_PRESET_DESC = (
    "储能用钒电池技术国际领先，营业收入约 **3.71 亿元**，已通过 c3mep 官方自评获得 **三级（集成级）**。"
    "点下方按钮可一次性预勾选全部材料为「已就绪」，便于评委演示与功能体验。"
    "**仅修改前端会话状态，不会连接任何外部服务。**"
)


def apply_preset(session_state, on: bool = True) -> None:
    """一次性勾选/取消全部清单。"""
    for it in flat_items():
        session_state[f"chk_{it['id']}"] = on


def reset_all(session_state) -> None:
    """全部取消勾选。"""
    apply_preset(session_state, on=False)


# ============================================================
# 自检
# ============================================================
if __name__ == "__main__":
    items = flat_items()
    total = total_count()
    print(f"=== 自评材料清单 v1 ===")
    print(f"组数: {len(CHECKLIST)}")
    print(f"总项数: {total}")
    print(f"示例 item: {items[0]}")
    # 模拟 100% 完成
    fake_state = {f"chk_{it['id']}": True for it in items}
    d, t, p = progress(fake_state)
    print(f"模拟完成: {d}/{t} ({p}%)")
    # 模拟 0%
    empty_state = {}
    d, t, p = progress(empty_state)
    print(f"模拟空: {d}/{t} ({p}%)")
    # 各组进度
    for g in CHECKLIST:
        gd, gt = group_progress(fake_state, g["key"])
        print(f"  {g['title']}: {gd}/{gt}")