# GeoRisk-AI-Award

Geo-Risk Copilot：用于矿山文件分析与贸易测算的 Streamlit 应用，支持**在线AI模式**与**演示模式**。

## 1. 功能概览

- 模块1：AI 文件分析（矿业/通用自动识别）
- 模块2：贸易利润测算与报价决策
- 模块内记录查询与 Excel 导出（矿山/贸易分开）
- 指标看板页面

## 2. 模式说明

应用支持两种模式：

- **在线AI模式**：启用真实 Claude API。
- **演示模式**：不依赖外部 API，返回本地演示数据，保证可演示可运行。

触发演示模式的情况：

1. 侧边栏关闭“是否启用AI”；
2. 未配置有效 `ANTHROPIC_API_KEY`；
3. API 调用失败（自动回退）。

当进入演示模式时，页面会提示：**“当前为演示数据”**。

## 3. API 安全设计

- API Key 与 BASE_URL 通过 `st.secrets`（或环境变量兜底）在后端读取。
- 前端页面不展示 `ANTHROPIC_API_KEY`、`BASE_URL`。
- 所有 AI 调用都在后端模块执行（`modules/claude_client.py`）。

## 4. 本地运行

### 4.1 安装依赖

```bash
pip install -r requirements.txt
```

### 4.2 配置 secrets（推荐）

在项目根目录创建 `.streamlit/secrets.toml`：

```toml
ANTHROPIC_API_KEY = "your_api_key"
BASE_URL = "https://your-base-url" # 可选
```

### 4.3 启动应用

```bash
python -m streamlit run app.py
```

## 5. Streamlit Cloud 部署（公网可分享）

1. 将项目推送到 GitHub 仓库。
2. 打开 Streamlit Cloud，创建 New app。
3. 选择仓库、分支，入口文件设为 `app.py`。
4. 在应用设置 **Secrets** 中配置：

```toml
ANTHROPIC_API_KEY = "your_api_key"
BASE_URL = "https://your-base-url" # 可选
```

5. 点击 Deploy，获取公网链接。
6. 将公网链接直接分享给他人（可微信打开使用）。

## 6. 比赛演示建议

- 现场网络不稳定时，关闭“是否启用AI”，切换到演示模式，确保 100% 可运行。
- 若在线模式异常，系统会自动回退演示模式并给出提示。
- 可优先演示：模块结果 + 记录查询 + Excel 导出 + 指标看板。
