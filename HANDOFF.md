# 天工智梯 · 开发交接文档（HANDOFF）

> 本文档面向**接手本项目的后续任务/开发者**，补充 `README.md` 未覆盖的 UI/交互改造、必须遵守的工程约定，以及可继续完善的方向。
> 项目根目录：`/workspace/天工智梯/`，代码与配置均持久化在此，**新会话可直接读取**。

---

## 一、当前成品状态（截至本交接）

### 1. 双端分流架构（首页）
- `app.py` 落地页改为**两栏大卡片入口**：`🏢 企业端` 与 `🧑‍⚖️ 专家端`。
- 点「企业端」→ 进入 `pages/1_企业画像与等级推荐.py`（企业端①），侧边栏提供 ①②③④ 四个模块的 `page_link` 导航。
- 点「专家端」→ 进入 `pages/5_专家评定反馈.py`（专家端⑤），**无导航目录**（专家端只有一个页面），侧边栏直接是功能操作区。
- 模块顺序已对齐业务语义：**①~④ 属企业端，⑤ 属专家端**。

### 2. 已统一的交互范式（五个模块一致）
- **选案例前全空**：表单/问卷/文本框初始值均为空（表单控件用 `session_state` 键 + 空默认值绑定）。
- **选案例自动填入**：侧边栏案例按钮只回填数据，不自动出报告。
- **点生成才出报告**：必须点「生成…」按钮才调用引擎（未配置接口走离线规则引擎 `core/demo.py`，配置了走大模型）。
- **点击才出现内容**：每个页面用 `st.tabs` 切功能 + `st.expander` 收内容，进入页面不信息过载。

### 3. 科技风主题
- `core/theme.py`：深蓝暗色 + 玻璃拟态卡片 + 发光边框 + 科技网格背景 + 渐变下划线标题；纯 CSS，零外部依赖。
- `.streamlit/config.toml`：`base="dark"` 主题 + `showErrorDetails=false`（**防代码/堆栈泄露到页面**）+ 关闭遥测。
- 每个页面在 `st.set_page_config` 之后调用 `apply_theme()`。

### 4. 三个案例工厂（离线演示全用这三个）
- `core/demo.py` 的 `CASES`：`华锐重工`（先进级）、`新兴机械`（基础级）、`精密电子`（基础级）。
- 数据贯穿 ①~④ 的回填、② 的政策咨询、③ 的问卷与 F1-F8、④ 的研判正文；⑤ 用 `expert_pack/` 下的三个样例申报书。

### 5. 在线 Demo
- 预览服务由 supervisord 托管（`/usr/local/share/supervisor/preview-8501.conf`），`autorestart=true`。
- 端口 `8501`。改代码后**必须杀掉真实 streamlit 进程**（从 `ss -ltnp | grep :8501` 取 PID 再 `kill -9`）才能重载；supervisord 会自动重启。
- ⚠️ 注意：`pkill -f "streamlit run app.py"` 会误杀执行命令自身的 shell（命令里含该字符串），**不要用 pkill**，改用端口查 PID 方式。

---

## 二、必须遵守的工程约定（违反会破坏现有功能）

| 约定 | 说明 | 违反后果 |
|------|------|---------|
| **零 Key 离线可跑** | 未配置接口时，①~④ 的"生成报告"、② 全功能、⑤ 全功能必须能跑（走 `core/demo.py` 等离线引擎）。新增功能须同时提供"大模型版"和"离线版"两条路径。 | 演示环境无 Key 时白屏/报错 |
| **选案例前空白** | 所有输入控件初始为空默认值，不能预填示例。 | 用户要求"选前全空"被破坏 |
| **点生成才出报告** | 报告/诊断/大纲只在点击生成按钮后出现，不能一进页面就显示。 | 交互范式不一致 |
| **防代码泄露** | `.streamlit/config.toml` 的 `showErrorDetails=false` 必须保留；页面**禁止** `st.json()` 暴露内部字典（模块⑤ 已修复）。报错用户只见友好提示。 | 源码路径/内部字段名泄露到页面 |
| **隐藏原生侧边栏导航** | `core/theme.py` 中 `[data-testid="stSidebarNav"]{display:none}` 隐藏了 Streamlit 原生页面列表，改用自建 `page_link` 导航。改动 CSS 时不要删这条。 | 侧边栏又出现平铺的 5 页面列表 |
| **双端分流** | 首页双卡片入口 + 企业端 4 页共用 `render_enterprise_sidebar()`、专家端用 `render_expert_sidebar()`（无目录）。新增模块需明确归属企业端/专家端。 | 分流结构被破坏 |
| **标题不用透明渐变字** | 标题用 `color + text-shadow + 渐变下划线`，**不能用 `background-clip:text`+透明填充**（会让 emoji 变透明不可见）。 | 🏭📊 等图标消失 |

---

## 三、关键文件职责速查

```
app.py                      # 首页：双端入口卡片 + 简化侧边栏
core/theme.py               # 科技风 CSS + apply_theme() + render_enterprise_sidebar()/render_expert_sidebar()
core/llm.py                 # call_llm / is_configured / DISCLAIMER（OpenAI 兼容）
core/knowledge.py           # 政策知识库：LEVEL_THRESHOLDS（四级阈值）/ POLICIES / CASES / SUBSIDY / 40场景
core/demo.py                # 三个案例数据 + 离线生成器（画像/改造路径/大纲/研判/F1-F8）
core/a_prompts.py / c_prompts.py / e_prompts.py  # 各模块提示词
pages/1_*.py ~ 5_*.py       # 五大模块页面（①~④ 企业端，⑤ 专家端）
.streamlit/config.toml      # 暗色主题 + 防泄露 + 关遥测
```

---

## 四、可继续完善的方向（供后续任务参考）

1. **首页双端卡片**：当前是图标+文字，可加 hover 发光、进入动画、各端模块数量角标。
2. **企业端首页内导航页**：可考虑在 ① 之前加一个"企业端总览"页，列出 4 模块卡片（类似首页双端，但只列企业端 4 个），让用户在企业端内也有"地图"。
3. **专家端**：专家端目前仅一个页面（⑤ 内含三模块选项卡）。若后续专家端要扩成多页面，需复用 `render_expert_sidebar()` 并为专家端各页加 `🧑‍⚖️` 导航。
4. **移动端适配**：当前 `layout="wide"`，窄屏下侧边栏导航与卡片可优化。
5. **案例扩展**：`core/demo.py` 的 `CASES` 目前 3 个，可按行业补充更多行业样例。
6. **报告导出**：各模块生成的 Markdown 报告可加"下载为 .md/.pdf"按钮（目前仅页面展示）。
7. **大模型深度报告**：配置了接口后，①③ ④ 走 `call_llm`；可统一加"重新生成""复制""导出"等操作条。
8. **统一页脚**：各页面底部 `st.info(DISCLAIMER)` 可抽成 `core/theme.py` 的 `render_footer()` 保持格式一致。

---

## 五、新任务接手建议（给后续开发者的开场白）

> "请读取 `/workspace/天工智梯/HANDOFF.md` 与 `README.md`，并浏览 `app.py`、`core/theme.py`、`pages/*.py` 的当前代码，
>  在遵守『零 Key 离线可跑 / 选案例前全空 / 点生成才出报告 / 防代码泄露 / 双端分流』等约定的前提下，继续完善网站。
>  先不要改动已稳定的架构，重点做 [具体需求]。"

---

## 六、验证清单（每次改动后必跑）
- `cd /workspace/天工智梯 && .venv/bin/python -m py_compile app.py core/*.py pages/*.py` 语法全过。
- 自建 mock 渲染测试（见历史会话的 `/tmp/mock_pages.py`）可捕捉页面级运行时错误。
- 杀真实 streamlit 进程重载后，`curl -s -o /dev/null -w "%{http_code}" http://localhost:8501/` 应返回 200，且 `/tmp/preview-8501.log` 无 Traceback。
