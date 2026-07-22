# 天工智梯 · 部署指南（Streamlit Community Cloud）

本指南用于将项目部署到 **Streamlit Community Cloud**（免费、公网可访问、自动从 GitHub 拉取更新）。

---

## 前置条件

- 已注册 GitHub 账号，且**当前网络能访问 github.com**（如需请挂代理）
- 已生成 GitHub Personal Access Token（PAT，具备 `repo` 权限）——仅用于首次 push，可部署后删除

---

## 步骤 1：在 GitHub 新建空仓库

1. 打开 https://github.com → 右上角 **New repository**（或 https://github.com/new）
2. Repository name：`tiangongzhiti`（可自定义）
3. **不要**勾选 `Add a README file` / `Add .gitignore` / `Choose a license`（项目里已包含）
4. 点 **Create repository**

建好后，记下仓库地址格式：`https://github.com/<你的用户名>/<仓库名>.git`

---

## 步骤 2：把代码推送到 GitHub

在 **VS Code 终端**（即本沙箱）执行（把 `<用户名>` / `<仓库名>` 替换成你的）：

```bash
cd /workspace/天工智梯
git remote add origin https://github.com/<用户名>/<仓库名>.git
git branch -M main
git push -u origin main
```

> **关于密码**：`git push` 弹出用户名/密码时——
> - 用户名：填你的 GitHub 用户名
> - 密码：**填 GitHub Personal Access Token**（不是账号登录密码）
>
> Token 生成路径：GitHub → 右上角头像 → **Settings** → **Developer settings** →
> **Personal access tokens** → **Tokens (classic)** → **Generate new token (classic)**
> → Note 随意、Expiration 随意、勾选 `repo` → **Generate** → 复制那串 `ghp_...`

推成功后，刷新 GitHub 仓库页面应能看到 `app.py`、`pages/`、`core/` 等文件。

---

## 步骤 3：在 Streamlit Community Cloud 一键部署

1. 打开 https://share.streamlit.io
2. 点 **Sign in with GitHub**（用刚才能访问的账号授权）
3. 点 **New app**
4. 选择刚推送的仓库 → Branch 选 **`main`** → Main file path 填 **`app.py`**
5. 点 **Deploy**
6. 等待 1–2 分钟，页面会给出公网地址，形如：
   `https://<仓库名>-<随机>.streamlit.app`

把这个地址发给企业/专家即可访问。

---

## 步骤 4：（可选）配置大模型接口

若要让"政策标准问答 / 专家评定"等模块真正调用大模型，需在 Streamlit Cloud 配置 Secrets：

1. 进入 App → 右上角 **⋯** → **Settings** → **Secrets**
2. 填入（与项目 `.env.example` 对应）：

```toml
OPENAI_API_KEY = "sk-你的密钥"
OPENAI_BASE_URL = "https://你的兼容端点/v1"
MODEL_NAME = "glm-4.5-air"
```

3. Save 后应用会自动重启生效。

> 若不配置，应用仍可正常运行与浏览，仅 LLM 问答类功能会提示未配置接口。

---

## 日常更新

代码改动后，在终端提交并推送即可，Streamlit Cloud 会自动重新部署：

```bash
git add -A
git commit -m "更新说明"
git push
```

---

## 备选方案（无法使用 GitHub 时）

若长期无法访问 GitHub，改用 **阿里云轻量服务器 / 协会自有服务器**：

- 项目已自带 `requirements.txt` 与 `run.sh`
- 在服务器安装 Python 3.11 + 依赖后：`bash run.sh`
- 建议用 `docker` + `nginx` 反代 + SSL，避免裸跑 8501 端口
- 这种方式不需要 GitHub，但需要你有一台可 SSH 的服务器
