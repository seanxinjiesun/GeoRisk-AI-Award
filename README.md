# GeoRisk-AI-Award

Geo-Risk Copilot：用于矿山文件分析与贸易测算的 Streamlit 应用，可部署到 Streamlit Cloud 并通过公网链接访问。

## 1. 功能概览

- 模块1：AI 文件分析（矿业/通用自动识别）
- 模块2：贸易利润测算与报价决策
- 模块内记录查询与 Excel 导出（矿山/贸易分开）
- 指标看板页面

## 2. API 安全设计

- API Key 与 BASE_URL 通过 `st.secrets`（或环境变量兜底）在后端读取。
- 前端页面不展示 `ANTHROPIC_API_KEY`、`BASE_URL`。
- 所有 AI 调用都在后端模块执行（`modules/claude_client.py`）。

## 3. 本地运行

### 3.1 安装依赖

```bash
pip install -r requirements.txt
```

### 3.2 配置 secrets（推荐）

在项目根目录创建 `.streamlit/secrets.toml`：

```toml
ANTHROPIC_API_KEY = "your_api_key"
BASE_URL = "https://your-base-url" # 可选
```

### 3.3 启动应用

```bash
python -m streamlit run app.py
```

## 4. Streamlit Cloud 部署（公网可分享）

1. 将项目推送到 GitHub 仓库。
2. 打开 Streamlit Cloud，创建 New app。
3. 选择仓库、分支，入口文件设为 `app.py`。
4. 在应用设置 **Secrets** 中配置：

```toml
ANTHROPIC_API_KEY = "your_api_key"
BASE_URL = "https://your-base-url" # 可选
```

5. 点击 Deploy，获取公网链接。
6. 将公网链接分享给评委（可微信打开使用）。

## 5. 云端稳定性建议

- 部署后先用真实样例跑通矿山分析与贸易测算。
- 若出现 AI 调用失败，优先检查：
  - `ANTHROPIC_API_KEY` 是否正确；
  - `BASE_URL` 是否可用（若配置了代理）；
  - Streamlit Cloud 网络访问是否正常。
- 评审前建议准备一份 PDF/PPT 结果备份，防止临场网络波动影响展示。