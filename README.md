# Web3 SpotOps Agent

面向 Web3 现货运营场景的 USDC 资金流监控与 AI 分析看板。项目集成链上实时拉取、规则异常检测、LLM 运营报告生成与下载。

## 功能

- 实时模式：按区块范围拉取 USDC Transfer 日志并展示概览、事件流、时间序列、地址分析。
- 示例模式：离线读取 `data/sample_usdc_transfers.csv`，无需 RPC 即可演示完整流程。
- AI Agent 分析：自动构建 metrics、检测异常、生成中文运营报告。
- 报告导出：支持在页面下载 Markdown 报告，并查看 Agent 输入 JSON 调试信息。

## 目录

- `dashboard.py`：Streamlit 主应用。
- `realtime/`：实时数据拉取与解析。
- `analyzer.py`：聚合分析与地址统计。
- `agent/`：指标构建、异常检测、提示词、LLM 调用、报告编排。
- `data/sample_usdc_transfers.csv`：示例数据。
- `tests/`：单元测试。

## 快速开始

1. 安装依赖：

   ```bash
   pip install -r requirements.txt
   ```

2. 配置环境变量：

   ```bash
   copy .env.example .env
   ```

3. 启动看板：

   ```bash
   streamlit run dashboard.py
   ```

## LLM 配置

- `LLM_API_KEY`：必填。
- `LLM_BASE_URL`：OpenAI-compatible 网关地址（默认 `https://api.deepseek.com/v1`）。
- `LLM_MODEL`：默认模型名称，可在侧边栏覆盖。

DeepSeek 示例：

```env
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_deepseek_api_key_here
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-v4-flash
```

## 实时链路配置

实时模式依赖 Alchemy 以太坊 RPC，请在 `.env` 中配置：

```env
ALCHEMY_API_KEY=your_alchemy_api_key_here
```

如果你只想演示功能，不依赖链上网络，可在侧边栏切换到“示例数据”模式。

## API 联通测试

已内置测试脚本：

```bash
python tools/check_glm_api.py
```

判定标准：
- `GET /models` 返回 200：说明 Key 与网关可用。
- `POST /chat/completions` 返回 200：说明模型调用成功。

## 常见问题

- `429 code=1113`：余额不足或无可用资源包，需要在模型平台充值/开通资源。
- `405/404`：网关地址或路径错误，检查 `LLM_BASE_URL`。
- `zstd decode` 报错：项目已在 `realtime/fetcher.py` 内做兼容处理，重启进程后重试。

## 测试

```bash
pytest tests -q
```
