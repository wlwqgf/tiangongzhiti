"""
天工智梯 · 全局科技风主题（深蓝暗色 + 玻璃拟态 + 发光边框）

统一调用方式（每个页面在 st.set_page_config 之后调用一次）：
    from core.theme import apply_theme
    apply_theme()

仅依赖 Streamlit 原生 + 自定义 CSS，零外部依赖、离线可跑。
"""
import streamlit as st

THEME_CSS = """
<style>
:root{
  --bg-0:#060a1c;
  --bg-1:#0a1230;
  --bg-2:#0d1a40;
  --cyan:#22d3ee;
  --blue:#3b82f6;
  --violet:#8b5cf6;
  --txt:#e7f0ff;
  --muted:#9fb3d6;
  --glass:rgba(16,28,64,0.55);
  --glass-2:rgba(12,22,52,0.72);
  --border:rgba(80,170,255,0.28);
  --glow:0 0 18px rgba(34,211,238,0.22);
}

/* ---- 背景：径向光晕 + 深蓝渐变 + 科技网格 ---- */
html, body, .stApp{
  background:
    radial-gradient(1100px 560px at 10% -10%, rgba(34,211,238,0.18), transparent 60%),
    radial-gradient(950px 520px at 100% 0%, rgba(139,92,246,0.16), transparent 55%),
    linear-gradient(160deg, var(--bg-0), var(--bg-1) 55%, var(--bg-2));
  background-attachment: fixed;
  color: var(--txt);
}
.stApp::before{
  content:"";
  position:fixed; inset:0; z-index:0; pointer-events:none;
  background-image:
    linear-gradient(rgba(80,170,255,0.045) 1px, transparent 1px),
    linear-gradient(90deg, rgba(80,170,255,0.045) 1px, transparent 1px);
  background-size: 42px 42px;
  -webkit-mask-image: radial-gradient(ellipse at 50% 0%, #000 0%, transparent 78%);
          mask-image: radial-gradient(ellipse at 50% 0%, #000 0%, transparent 78%);
}
.block-container{ position:relative; z-index:1; padding-top:1.2rem; }

/* 顶部细发光条 */
.stAppHeader{ background:transparent !important; }
.stAppHeader::after{
  content:""; position:fixed; top:0; left:0; right:0; height:2px; z-index:50;
  background:linear-gradient(90deg, transparent, var(--cyan), var(--violet), transparent);
  box-shadow:0 0 14px rgba(34,211,238,0.55);
}

/* ---- 标题：青色发光 + 渐变下划线（不透明填充，避免 emoji 变透明） ---- */
h1{
  color:#7fe9ff;
  font-size:1.4rem !important; font-weight:700; letter-spacing:.4px;
  text-shadow:0 0 14px rgba(34,211,238,0.4);
  border-bottom:2px solid transparent;
  border-image:linear-gradient(90deg, var(--cyan), transparent) 1;
  padding-bottom:.25rem;
}
h2{
  color:#7fe9ff;
  font-size:1.2rem !important; font-weight:700; letter-spacing:.3px;
  text-shadow:0 0 12px rgba(34,211,238,0.35);
  border-bottom:2px solid transparent;
  border-image:linear-gradient(90deg, var(--cyan), transparent) 1;
  padding-bottom:.2rem;
}
h3{ color:var(--cyan); font-size:1.08rem !important; font-weight:600; text-shadow:0 0 10px rgba(34,211,238,0.22); }
h4{ color:var(--cyan); font-size:1rem !important; font-weight:600; }
/* 正文与列表放大，缩小与标题的差距，行高更宽松，提升可读性 */
.stMarkdown p, .stMarkdown li{ color:var(--txt); font-size:1.02rem; line-height:1.72; }
.stMarkdown p{ font-size:1.05rem; }
/* caption 微调 */
.stCaption, .stMarkdown .stCaption{ font-size:0.85rem !important; }

/* ---- 侧边栏 ---- */
section[data-testid="stSidebar"]{
  background:linear-gradient(180deg, rgba(11,19,48,0.94), rgba(6,10,28,0.97));
  border-right:1px solid var(--border);
  backdrop-filter:blur(10px);
}
section[data-testid="stSidebar"] *{ color:var(--txt) !important; }

/* 隐藏 Streamlit 原生页面导航器（"应用"下拉列表），仅隐藏该元素本身 */
[data-testid="stSidebarNav"]{ display:none !important; }
section[data-testid="stSidebar"] > [data-testid="stSidebarNav"]{ display:none !important; }

/* ---- 按钮 ---- */
.stButton > button{
  background:linear-gradient(90deg, rgba(34,211,238,0.16), rgba(59,130,246,0.16));
  color:var(--txt) !important;
  border:1px solid var(--border);
  border-radius:11px; padding:.5rem 1rem;
  font-weight:600; letter-spacing:.3px; font-size:1.02rem;
  box-shadow:var(--glow); transition:all .18s ease;
}
.stButton > button:hover{
  border-color:var(--cyan); color:#fff !important;
  box-shadow:0 0 24px rgba(34,211,238,0.5);
  transform:translateY(-1px);
}
.stButton button[data-testid="baseButton-primary"]{
  background:linear-gradient(90deg, var(--cyan), var(--blue));
  color:#04122b !important; border:none; font-weight:800;
  box-shadow:0 0 22px rgba(34,211,238,0.45);
}
.stButton button[data-testid="baseButton-primary"]:hover{
  box-shadow:0 0 30px rgba(34,211,238,0.7); color:#021026 !important;
}

/* ---- 折叠面板 ---- */
.stExpander{
  background:var(--glass) !important;
  border:1px solid var(--border) !important;
  border-radius:14px !important;
  backdrop-filter:blur(6px);
  box-shadow:0 0 14px rgba(34,211,238,0.08);
}
.stExpander > summary{ font-weight:700; color:var(--cyan); }
.stExpander .stMarkdown p{ color:var(--txt); }

/* ---- 选项卡 ---- */
.stTabs [data-baseweb="tab-list"]{ background:transparent; gap:6px; }
.stTabs [data-baseweb="tab"]{
  color:var(--muted); border-radius:10px 10px 0 0;
  border:1px solid transparent; border-bottom:none;
  transition:all .18s ease; font-weight:600;
}
.stTabs [data-baseweb="tab"]:hover{ color:var(--cyan); }
.stTabs [data-baseweb="tab"][aria-selected="true"]{
  color:#04122b !important; font-weight:800;
  background:linear-gradient(90deg, var(--cyan), var(--blue));
  border:1px solid var(--cyan); border-bottom:none;
  box-shadow:0 -2px 16px rgba(34,211,238,0.35);
}

/* ---- 表单控件统一玻璃风 ---- */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stDateInput input, .stSelectbox > div, .stMultiselect > div{
  background:var(--glass-2) !important;
  color:var(--txt) !important;
  border:1px solid var(--border) !important;
  border-radius:9px !important;
}
.stTextInput input:focus, .stNumberInput input:focus, .stTextArea textarea:focus{
  border-color:var(--cyan) !important;
  box-shadow:0 0 12px rgba(34,211,238,0.4) !important;
}
.stSelectbox [data-baseweb="select"] > div,
.stMultiselect [data-baseweb="select"] > div{ background:var(--glass-2) !important; }

/* ---- 指标块 ---- */
.stMetric{
  background:var(--glass) !important;
  border:1px solid var(--border) !important;
  border-radius:12px !important;
  padding:.4rem .8rem !important;
  box-shadow:var(--glow);
}
.stMetric label, .stMetric .metric-value{ color:var(--txt) !important; }

/* ---- 提示框 ---- */
.stAlert, .stInfo, .stSuccess, .stWarning, .stError{
  border-radius:12px !important;
  backdrop-filter:blur(6px);
}
.stInfo{ border-left:3px solid var(--cyan) !important; }
.stSuccess{ border-left:3px solid #34d399 !important; }
.stWarning{ border-left:3px solid #fbbf24 !important; }
.stError{ border-left:3px solid #f87171 !important; }

/* ---- 表格 ---- */
.stTable, table{ border-radius:10px; overflow:hidden; }
table th{ background:rgba(34,211,238,0.14) !important; color:var(--cyan) !important; }
table td{ color:var(--txt) !important; border-color:rgba(80,170,255,0.15) !important; }

/* ---- 首页模块卡片（page_link） ---- */
[data-testid="stPageLink"] a{
  display:block; text-decoration:none;
  background:var(--glass);
  border:1px solid var(--border);
  border-radius:16px; padding:18px 14px; min-height:118px;
  color:var(--txt) !important; backdrop-filter:blur(6px);
  box-shadow:var(--glow); transition:all .2s ease;
  font-size:1rem;
}
[data-testid="stPageLink"] a:hover{
  border-color:var(--cyan); color:#fff !important;
  box-shadow:0 0 26px rgba(34,211,238,0.5);
  transform:translateY(-3px);
}
[data-testid="stPageLink"] a p{ color:var(--txt) !important; font-weight:700; }
/* 放大各处 emoji 图标（首页卡片 + 侧边栏导航），文字尺寸保持不变 */
[data-testid="stPageLink"] a > div > span:first-child,
[data-testid="stPageLink"] a > span:first-child{
  font-size:1.7rem !important; line-height:1; vertical-align:middle;
}

/* 分隔线发光 */
hr{ border:none; height:1px;
  background:linear-gradient(90deg, transparent, var(--cyan), transparent); }
</style>
"""


def apply_theme():
    """在每个页面 st.set_page_config 之后调用一次，注入科技风 CSS。"""
    try:
        st.markdown(THEME_CSS, unsafe_allow_html=True)
    except Exception:
        pass


def tech_pill(text: str) -> str:
    """返回一个发光小标签的 HTML（用于状态/标签展示）。"""
    return (
        f'<span style="display:inline-block;padding:2px 10px;border-radius:999px;'
        f'background:rgba(34,211,238,0.14);border:1px solid var(--border);'
        f'color:#22d3ee;font-size:.82rem;font-weight:700;margin-right:6px;">{text}</span>'
    )


# ============================================================
# 侧边栏构建器（统一格式，排版工整）
# ============================================================
ENTERPRISE_NAV = [
    ("pages/1_自评材料清单.py", "📊", "① 自评材料清单"),
    ("pages/2_政策标准问答.py",     "💬", "② 政策标准互动问答"),
    ("pages/3_申报书大纲生成.py",   "📝", "③ 申报书大纲智能生成"),
    ("pages/4_申报书研判优化.py",   "🔍", "④ 申报书研判与优化"),
    ("pages/7_政策包推荐.py",       "💰", "⑤ 政策包推荐与资金测算"),
    ("pages/6_线下服务对接.py",     "📞", "⑥ 线下服务对接"),
]

EXPERT_NAV = [
    ("pages/5_专家评定反馈.py", "🧑‍⚖️", "⑤ 专家侧评定与反馈"),
]


def render_enterprise_sidebar():
    """企业端侧边栏：返回首页 + 5 模块整齐导航 + 分隔线。在 with st.sidebar 中调用。"""
    st.page_link("app.py", label="🏠 返回首页", icon="🏠")
    st.markdown("#### 🏢 企业端")
    for page, icon, label in ENTERPRISE_NAV:
        st.page_link(page, label=label, icon=icon)
    st.divider()


def render_expert_sidebar():
    """专家端侧边栏：返回首页 + 标题（专家端只有一个页面，不需要导航目录）。"""
    st.page_link("app.py", label="🏠 返回首页", icon="🏠")
    st.markdown("#### 🧑‍⚖️ 专家端")
    st.caption("初筛 → 增强标注 → 评分建议")
    st.divider()
