# -*- coding: utf-8 -*-
"""
core/field_lib.py —— 结构化字段库（改动1：核心竞争力 / 壁垒最厚）

把每份"优秀申报书"拆成结构化字段：
    industry 行业 | level 等级 | link 环节 | scenarios 场景
    key_metrics 关键指标数据 | scoring_paragraph 得分点段落 | source/result 溯源

能力：能回答"同行业的先进级企业，在'生产作业'环节通常写几个场景？"——这才是真本事。
离线可跑；团队标注的 JSON 入库后优先加载，缺失时回退内置示例。

落库方式（今天）：LLM 抽取 pdf/docx -> 人工校验 -> 写入 knowledge/declaration_field_lib.json
"""
import os
import json
from collections import Counter

# ---------------------------------------------------------------------------
# 内置示例（团队标注入库后由 JSON 覆盖；此处保证离线 demo 永远能跑）
# ---------------------------------------------------------------------------
_EMBEDDED = [
    {"id": "DEC-001", "industry": "装备制造", "level": "先进级", "link": "生产作业",
     "scenarios": ["产线柔性配置", "工艺动态优化", "人机协同作业", "质量在线检测"],
     "key_metrics": {"设备联网率": "92%", "关键工序数控化率": "95%", "生产数据采集点": "1800+", "自动化率": "88%"},
     "scoring_paragraph": "通过MES与SCADA集成实现关键工序100%数据采集，建立质量在线检测模型，一次合格率由96.1%提升至99.3%，形成可复制的柔性产线范式。",
     "source": "华锐重工（脱敏）", "result": "通过"},
    {"id": "DEC-002", "industry": "装备制造", "level": "先进级", "link": "生产作业",
     "scenarios": ["产线柔性配置", "质量在线检测", "设备智能运维", "精准作业派工"],
     "key_metrics": {"设备联网率": "90%", "关键工序数控化率": "93%", "生产数据采集点": "1500+", "自动化率": "85%"},
     "scoring_paragraph": "部署设备智能运维系统，基于振动与温度特征预测性维护使非计划停机下降42%，单位产能能耗降低11%。",
     "source": "中集特种物流（脱敏）", "result": "通过"},
    {"id": "DEC-003", "industry": "装备制造", "level": "卓越级", "link": "生产作业",
     "scenarios": ["产线柔性配置", "工艺动态优化", "人机协同作业", "质量在线检测", "能源动态管控"],
     "key_metrics": {"设备联网率": "98%", "关键工序数控化率": "100%", "AI场景占比": "28%", "自动化率": "94%"},
     "scoring_paragraph": "构建数字孪生产线，工艺参数自寻优使换型时间缩短60%；AI质检覆盖全部关键尺寸，漏检率<0.1%。",
     "source": "某标杆装备企业（脱敏）", "result": "通过"},
    {"id": "DEC-004", "industry": "石化化工", "level": "先进级", "link": "生产作业",
     "scenarios": ["工艺动态优化", "设备智能运维", "安全一体化管控", "精准作业派工"],
     "key_metrics": {"设备联网率": "88%", "自动化率": "90%", "DCS覆盖率": "100%", "APC投用率": "76%"},
     "scoring_paragraph": "先进过程控制(APC)投用率76%，关键装置平稳率提升5.8个百分点，年增效约3200万元。",
     "source": "某石化企业（脱敏）", "result": "通过"},
    {"id": "DEC-005", "industry": "汽车及零部件", "level": "先进级", "link": "生产作业",
     "scenarios": ["产线柔性配置", "质量在线检测", "物流智能配送", "人机协同作业"],
     "key_metrics": {"设备联网率": "91%", "关键工序数控化率": "96%", "自动化率": "87%", "生产数据采集点": "2200+"},
     "scoring_paragraph": "总装线多车型混流生产，AGV智能配送齐套率99.5%，整车一次下线合格率98.7%。",
     "source": "某汽车零部件企业（脱敏）", "result": "通过"},
    {"id": "DEC-006", "industry": "电子信息", "level": "基础级", "link": "生产作业",
     "scenarios": ["质量在线检测", "精准作业派工"],
     "key_metrics": {"设备联网率": "70%", "关键工序数控化率": "80%", "自动化率": "65%"},
     "scoring_paragraph": "关键工序部署机器视觉检测，缺陷识别准确率97%，初步实现生产数据实时采集。",
     "source": "某电子企业（脱敏）", "result": "通过（基础级）"},
    {"id": "DEC-007", "industry": "装备制造", "level": "基础级", "link": "生产作业",
     "scenarios": ["质量在线检测", "产线柔性配置"],
     "key_metrics": {"设备联网率": "68%", "关键工序数控化率": "78%", "自动化率": "62%"},
     "scoring_paragraph": "完成核心设备联网与数据采集，建立基础级质量追溯体系。",
     "source": "某中小企业（脱敏）", "result": "通过（基础级）"},
]


def _lib_path() -> str:
    return os.path.join(os.path.dirname(__file__), "..", "knowledge", "declaration_field_lib.json")


def load_field_lib():
    """优先加载团队标注的 JSON；缺失/为空时回退内置示例，保证离线可演示。"""
    p = _lib_path()
    if os.path.exists(p):
        try:
            with open(p, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
        except Exception:
            pass
    return _EMBEDDED


def query_production_scenarios(industry: str, level: str, link: str = "生产作业", lib=None) -> dict:
    """核心能力：同行业 + 同等级 + 同环节，统计'通常写几个场景'并聚合得分点段落。"""
    lib = lib or load_field_lib()
    matched = [r for r in lib
               if r.get("industry") == industry and r.get("level") == level and r.get("link") == link]
    if not matched:
        return {"matched": 0, "count_typical": 0,
                "message": f"字段库中暂无「{industry}/{level}/{link}」样本，建议补充标杆案例入库。"}
    n = len(matched)
    typical = round(sum(len(r.get("scenarios", [])) for r in matched) / n, 1)  # 平均场景数 = 通常写几个
    freq = Counter()
    for r in matched:
        for s in r.get("scenarios", []):
            freq[s] += 1
    return {
        "matched": n,
        "count_typical": typical,
        "top_scenarios": [s for s, _ in freq.most_common(6)],
        "scoring_paragraphs": [r.get("scoring_paragraph", "") for r in matched],
        "sources": [r.get("source", "") for r in matched],
        "key_metrics_samples": [r.get("key_metrics", {}) for r in matched],
    }


# 兼容原 MVP 命名
def benchmark_query(industry: str, level: str, link: str = "生产作业"):
    return query_production_scenarios(industry, level, link)


if __name__ == "__main__":
    q = query_production_scenarios("装备制造", "先进级", "生产作业")
    print("通常写场景数:", q["count_typical"], "| 高频:", q["top_scenarios"])
