# 天工智梯 · 本地运行与验收指南（QUICKSTART）

适用：大连市智能制造产业协会 · 智能工厂梯度培育申报 AI 专家顾问系统
环境：Python ≥ 3.11，Windows / macOS / Linux 均可

## 一、安装依赖

```bash
cd tiangongzhiti_assembled
pip install -r requirements.txt
```

> 依赖仅三项：`streamlit>=1.30`、`openai>=1.30`、`python-dotenv>=1.0`

## 二、启动（浏览器自动打开）

```bash
streamlit run app.py
```

启动后终端输出 `Local URL: http://localhost:8501`，浏览器自动弹出该地址。
若未弹出，手动访问 `http://localhost:8501`。

自定义端口（端口被占用时）：
```bash
streamlit run app.py --server.port 8502
```

## 三、要不要配 API Key？

- **不配 Key 也能跑**：`call_llm` 内置离线兜底，页面可正常进入、点击、走完流程；
  大模型生成部分返回模板式兜底文案（非真实模型输出）。
- **配 Key 才真实生成**：在项目根目录建 `.env`：
  ```
  OPENAI_API_KEY=你的key
  OPENAI_BASE_URL=你的兼容端点   # 可选，默认官方
  ```
  参考已附的 `.env.example`。

> 合规护栏在 `call_llm` 入口、拦截发生在调模型之前——**不配 Key 也能验证改动3**。

## 四、浏览器必测验收点（4 项）

| # | 操作 | 期望结果 |
|---|------|---------|
| 1 | 左侧栏 `🛡️ 智能体模式` 切到 **企业端**，点 🏢 企业端进入 | 正常进入企业端各页 |
| 2 | 企业端任意对话框输入「评分权重怎么定」或「帮我刷分」 | ⛔ 弹拒答，导引去专家端 |
| 3 | 左侧栏切到 **专家端**，进专家评定页，同样问「评分权重」 | ✅ 正常返回权重/打分细则 |
| 4 | 企业端问正常问题（如「先进级要几个场景」） | ✅ 正常回答，不误拦 |

附：改动1（字段库）/ 改动2（政策包）可在企业端对应页面（政策包推荐页、字段库查询）点测。

## 五、常见排查

- 端口被占：`--server.port 8502` 换端口。
- `pip` 不是 3.11+：`python -m pip install -r requirements.txt`。
- 页面报错：看终端红字；如为 `import` 缺失，先确认依赖装全。
- 白屏/样式异常：清缓存 `streamlit cache clear` 后重开。

## 六、目录要点

- `app.py`：双入口落地页 + 侧边栏智能体模式开关。
- `core/llm.py`：大模型调用入口，含集中式合规护栏（改动3）。
- `core/field_lib.py`：结构化字段库（改动1）。
- `core/policy_pack.py`：政策包推荐与资金测算（改动2）。
- `core/agent_mode.py`：双端角色路由与合规拦截逻辑。
- `pages/7_政策包推荐.py`、`pages/8_双端分离与合规.py`：改动2/3 演示页。
- `knowledge/declaration_field_lib.json`：字段库标注样本（当前 7 条脱敏样例）。
