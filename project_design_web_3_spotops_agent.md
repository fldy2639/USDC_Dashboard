# Web3 SpotOps Agent 项目设计文档

## 1. 项目名称

**Web3 SpotOps Agent：USDC 鲸鱼资金流监控与 Agent 分析助手**

## 2. 项目定位

本项目面向 Web3 现货平台运营场景，基于以太坊 USDC Transfer 链上数据，构建一个轻量级 Agent 分析工具。

系统将链上原始日志转换为运营可读的资金流指标、异常信号、地址行为分析和中文运营建议，帮助运营同学更快完成数据观察、异常发现和日报撰写。

一句话介绍：

> 一个面向 Web3 现货运营场景的链上资金流 Agent，看板负责呈现事实数据，Agent 负责解释数据、识别异常并生成运营行动建议。

## 3. 项目目标

### 3.1 面试目标

本项目用于展示以下能力：

1. 使用真实链上数据完成数据获取、解析和清洗。
2. 使用 pandas 完成基础分析和指标聚合。
3. 使用 Streamlit 搭建可交互的数据看板。
4. 接入真实 LLM API，让 AI 参与数据解释、异常归因和运营建议生成。
5. 将 AI 能力嵌入具体运营工作流，而不是停留在聊天式使用。

### 3.2 业务目标

模拟 Web3 现货平台运营同学的日常工作流：

1. 观察近期 USDC 资金流变化。
2. 识别大额转账、地址集中度、目标地址净流入/净流出等异常。
3. 快速理解异常背后的可能运营含义。
4. 自动生成一份可复制的运营日报或分析摘要。
5. 给出下一步运营动作建议。

## 4. 当前项目基础

现有项目已经具备以下能力：

1. 实时拉取 USDC Transfer 日志。
2. 解析日志中的交易哈希、区块号、from、to、value、timestamp 等字段。
3. 使用 pandas 进行时间规范化、日度聚合和地址维度分析。
4. 使用 Streamlit 展示概览、事件流、时间序列和地址分析四个 Tab。
5. 支持目标地址输入、覆盖区块数、分块查询大小和结束区块等查询参数。

因此，后续改造重点不是重写底层数据链路，而是在现有 Dashboard 之上新增 Agent 分析层。

## 5. 用户角色与使用场景

### 5.1 目标用户

**Web3 现货平台运营实习生 / 运营分析同学**

用户特点：

- 不一定熟悉链上技术细节。
- 需要快速观察资金流变化。
- 需要把数据转化为日报、周报或运营反馈。
- 关注异常是否需要人工复核或内容响应。

### 5.2 典型场景

#### 场景 A：日常巡检

运营同学每天打开看板，选择最近 N 个区块或固定时间窗口，查看 USDC 转账活跃度、总转账量和活跃地址数。

Agent 输出：

- 当前资金流是否平稳。
- 是否存在明显大额转账。
- 是否存在地址集中度异常。
- 今日运营观察摘要。

#### 场景 B：鲸鱼地址观察

用户输入某个目标地址，系统统计该地址在样本窗口内的接收金额、发送金额、净流入和交易次数。

Agent 输出：

- 该地址当前更偏向资金流入还是流出。
- 该地址是否可能为交易所、机构钱包或普通钱包。
- 是否建议持续观察。

#### 场景 C：面试 Demo

面试时打开 Streamlit 页面，先展示实时数据看板，再点击“运行 Agent 分析”。

Agent 输出：

- 数据概览。
- 异常发现。
- 可能原因。
- 运营建议。
- 可复制日报。

## 6. 需求范围

### 6.1 P0：三天内必须完成

1. 新增 `AI Agent 分析` Tab。
2. 新增规则型异常检测模块。
3. 接入真实 LLM API。
4. 将结构化指标传入 LLM，生成中文运营分析报告。
5. 支持报告复制或 Markdown 下载。
6. 在 README 中突出项目的 Agent 分析能力。

### 6.2 P1：面试前尽量完成

1. 增加 sample data / live data 切换。
2. 增加大额转账阈值设置。
3. 增加 Top 地址集中度分析。
4. 增加目标地址行为解释。
5. 增加 Agent 输出 JSON 调试视图，展示 Agent 输入了哪些指标。

### 6.3 P2：后续优化

1. 支持多 token，例如 USDT、WETH。
2. 支持多链，例如 Ethereum、Base、Arbitrum。
3. 接入地址标签数据，识别交易所地址、合约地址、疑似机构地址。
4. 加入历史基线，对比当前窗口与历史均值。
5. 将日报推送到飞书、企业微信或邮件。

## 7. 非目标范围

三天内不做以下内容：

1. 不做交易策略或买卖建议。
2. 不做复杂后端服务。
3. 不做多 Agent 框架重构。
4. 不做钱包实名识别。
5. 不做复杂机器学习模型。
6. 不做链上风控结论，只做运营观察和异常提示。

## 8. 系统架构设计

### 8.1 总体流程

```text
USDC Transfer Logs
        ↓
Fetcher：拉取链上原始日志
        ↓
Parser：解析 Transfer 事件
        ↓
Analyzer：计算运营指标
        ↓
Anomaly Detector：识别异常信号
        ↓
Agent Context Builder：组织给 LLM 的结构化上下文
        ↓
LLM Agent：生成运营分析、异常解释、行动建议
        ↓
Streamlit Dashboard：展示看板与 Agent 报告
```

### 8.2 模块结构建议

```text
Blockchain_learning/
├── dashboard.py
├── analyzer.py
├── realtime/
│   ├── fetcher.py
│   ├── parser.py
│   └── config.py
├── agent/
│   ├── __init__.py
│   ├── llm_client.py
│   ├── metrics_builder.py
│   ├── anomaly_detector.py
│   ├── prompt_builder.py
│   └── report_agent.py
├── data/
│   ├── sample_usdc_transfers.csv
│   └── reports/
└── docs/
    ├── project_design.md
    ├── agent_workflow.md
    └── demo_script.md
```

## 9. 现有模块与新增模块关系

| 模块 | 当前职责 | 是否保留 | 改造方向 |
|---|---|---:|---|
| `realtime/fetcher.py` | 连接节点，分块拉取 USDC Transfer logs | 保留 | 作为 Data Fetcher Tool |
| `realtime/parser.py` | 解析 raw logs 为标准 DataFrame | 保留 | 作为 Data Parser Tool |
| `analyzer.py` | 时间规范化、日度聚合、地址分析 | 保留 | 补充 metrics summary 函数 |
| `dashboard.py` | Streamlit 多 Tab 可视化 | 保留 | 新增 Agent 分析 Tab |
| `agent/anomaly_detector.py` | 暂无 | 新增 | 规则型异常检测 |
| `agent/llm_client.py` | 暂无 | 新增 | 封装真实 LLM API 调用 |
| `agent/report_agent.py` | 暂无 | 新增 | 调度指标、异常和 LLM，生成报告 |

## 10. Agent 分析层设计

### 10.1 Agent 的定义

本项目中的 Agent 不强调复杂框架，而强调“能完成一个运营分析任务的工作流”。

Agent 输入：

- 当前链上数据窗口。
- 目标地址，可为空。
- 用户设置的阈值，例如大额转账阈值。
- Dashboard 已计算出的核心指标。
- 异常检测模块输出的 signals。

Agent 输出：

- 数据概览。
- 异常发现。
- 目标地址分析。
- 可能原因。
- 运营建议。
- 后续待办。
- 风险提示。

### 10.2 Agent 工作流

```text
Step 1：读取 Dashboard 当前 DataFrame
Step 2：生成 Metrics Summary
Step 3：运行规则型 Anomaly Detector
Step 4：构造 LLM Prompt
Step 5：调用真实 LLM API
Step 6：解析并展示 Agent Report
Step 7：支持复制或下载报告
```

### 10.3 Agent 工具函数设计

#### 10.3.1 Metrics Builder

建议函数：

```python
def build_metrics_summary(df, target_address=None) -> dict:
    """将当前 DataFrame 汇总为 LLM 可理解的结构化指标。"""
```

输出示例：

```json
{
  "window": {
    "start_time": "2026-04-24 05:20:00 UTC",
    "end_time": "2026-04-24 05:35:00 UTC",
    "block_count": 200
  },
  "market_activity": {
    "transfer_count": 10386,
    "total_volume_usdc": 411552673.73,
    "active_address_count": 5500,
    "avg_transfer_usdc": 39622.5,
    "max_transfer_usdc": 81200000.0
  },
  "target_address": {
    "address": "0x...",
    "received_usdc": 860.89,
    "sent_usdc": 860.89,
    "net_flow_usdc": 0.0,
    "tx_count_total": 2
  }
}
```

#### 10.3.2 Anomaly Detector

建议函数：

```python
def detect_anomalies(df, metrics, whale_threshold=1_000_000) -> list[dict]:
    """基于规则识别运营异常信号。"""
```

异常规则：

| 异常类型 | 判断逻辑 | 运营含义 |
|---|---|---|
| 大额转账 | 单笔转账金额 ≥ whale_threshold | 可能存在机构调仓、交易所归集或大户资金移动 |
| 地址集中度高 | Top1 接收地址金额占比 ≥ 30% | 资金流向集中，需关注是否为交易所或机构地址 |
| 目标地址大额净流入 | 目标地址净流入 ≥ threshold | 可能有充值、归集或资金准备动作 |
| 目标地址大额净流出 | 目标地址净流出 ≤ -threshold | 可能有提现、资金迁移或风险事件 |
| 交易活跃度高 | 当前日志条数显著高于手动设定阈值 | 市场活跃度升高，可作为内容或运营观察点 |

#### 10.3.3 Prompt Builder

Prompt 设计原则：

1. 明确 Agent 角色：Web3 现货平台运营分析助手。
2. 明确输出对象：运营同学，而不是工程师。
3. 明确边界：只做观察和建议，不给投资建议。
4. 明确格式：结构化输出，便于复制到日报。
5. 明确数据来源：当前 Dashboard 窗口内的 USDC Transfer 数据。

Prompt 模板：

```text
你是一个 Web3 现货平台运营分析 Agent。

你的任务是基于 USDC 链上转账数据，帮助运营同学理解当前资金流情况。

请严格基于输入数据生成分析，不要编造不存在的信息。
不要给出投资建议、价格预测或交易建议。

请输出以下结构：
1. 数据概览
2. 主要发现
3. 异常信号
4. 目标地址分析
5. 可能原因
6. 运营建议
7. 今日待办
8. 风险提示

输入指标：
{metrics_json}

异常信号：
{anomalies_json}

Top 地址：
{top_addresses_json}
```

#### 10.3.4 LLM Client

建议封装为：

```python
class LLMClient:
    def __init__(self, provider: str, api_key: str, model: str):
        ...

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        ...
```

环境变量建议：

```text
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.xxx.com/v1
LLM_MODEL=your-model-name
```

三天内建议优先做 OpenAI-compatible 风格封装，方便后续切换不同模型服务商。

### 10.4 Agent 输出格式

建议第一版直接输出 Markdown：

```markdown
## Web3 现货运营观察日报

### 1. 数据概览
...

### 2. 主要发现
...

### 3. 异常信号
...

### 4. 运营建议
...

### 5. 今日待办
- [ ] 复核 Top1 接收地址
- [ ] 观察目标地址后续净流向
- [ ] 若大额转账持续出现，准备市场异动相关内容
```

后续可以升级为 JSON + Markdown 双输出。

## 11. 数据指标设计

### 11.1 全局指标

| 指标 | 字段名 | 说明 |
|---|---|---|
| 样本日志条数 | `transfer_count` | 当前窗口内 USDC Transfer 日志数量 |
| 总转账量 | `total_volume_usdc` | 当前窗口 USDC 转账金额求和 |
| 活跃地址数 | `active_address_count` | from/to 地址去重数 |
| 平均转账金额 | `avg_transfer_usdc` | 总金额 / 日志条数 |
| 最大单笔转账 | `max_transfer_usdc` | 当前窗口最大一笔 USDC 转账 |
| 大额转账笔数 | `whale_transfer_count` | 超过阈值的转账数量 |

### 11.2 地址指标

| 指标 | 字段名 | 说明 |
|---|---|---|
| 接收金额 | `total_received_usdc` | 目标地址作为 to 的金额求和 |
| 发送金额 | `total_sent_usdc` | 目标地址作为 from 的金额求和 |
| 净流入 | `net_flow_usdc` | 接收金额 - 发送金额 |
| 收款次数 | `tx_count_in` | 目标地址作为 to 的日志数 |
| 转出次数 | `tx_count_out` | 目标地址作为 from 的日志数 |
| 首次出现 | `first_seen` | 目标地址在窗口中的首次出现时间 |
| 最近出现 | `last_seen` | 目标地址在窗口中的最近出现时间 |

### 11.3 Top 地址指标

| 指标 | 说明 |
|---|---|
| Top10 接收地址 | 按接收 USDC 金额排序 |
| Top10 发送地址 | 按发送 USDC 金额排序 |
| Top1 接收占比 | Top1 接收金额 / 总转账量 |
| Top10 接收占比 | Top10 接收金额 / 总转账量 |

## 12. Dashboard 页面改造设计

### 12.1 页面标题

由：

```text
Week4 USDC Whale Dashboard（实时）
```

改为：

```text
Web3 SpotOps Agent：USDC 鲸鱼资金流监控与 AI 分析助手
```

### 12.2 侧边栏

新增配置：

```text
数据模式：实时数据 / 示例数据
目标地址：可选
覆盖区块数
分块查询大小
结束区块
大额转账阈值
LLM 模型名称
运行 Agent 分析按钮
```

### 12.3 Tab 设计

```text
概览
事件流
时间序列
地址分析
AI Agent 分析
```

### 12.4 AI Agent 分析 Tab

页面内容：

1. 当前分析窗口说明。
2. Agent 输入指标 JSON。
3. 异常信号列表。
4. “生成 AI 分析报告”按钮。
5. Markdown 报告展示。
6. 下载 Markdown 按钮。

## 13. 三天实现计划

### Day 1：Agent 数据准备层

目标：让 Agent 有稳定的结构化输入。

任务：

1. 新增 `agent/metrics_builder.py`。
2. 新增 `agent/anomaly_detector.py`。
3. 从现有 DataFrame 生成 metrics JSON。
4. 基于规则输出 anomalies JSON。
5. 在 Streamlit 中增加 `AI Agent 分析` Tab 的静态展示。

验收标准：

- 页面能展示 metrics JSON。
- 页面能展示 anomalies JSON。
- 不调用 LLM 也能看到规则型异常结果。

### Day 2：接入真实 LLM API

目标：让 Agent 能基于真实数据生成运营分析。

任务：

1. 新增 `agent/llm_client.py`。
2. 新增 `agent/prompt_builder.py`。
3. 新增 `agent/report_agent.py`。
4. 配置 `.env.example` 中的 LLM 环境变量。
5. 在 Dashboard 中加入“生成 AI 分析报告”按钮。
6. 加入 LLM 调用失败时的兜底模板报告。

验收标准：

- 点击按钮后能调用真实 LLM API。
- 报告内容基于当前 metrics 和 anomalies。
- API 失败时不会导致 Dashboard 崩溃。

### Day 3：文档、演示和面试包装

目标：让 GitHub 项目具备面试展示能力。

任务：

1. 重写 README 项目简介和功能说明。
2. 增加 `docs/project_design.md`。
3. 增加 `docs/agent_workflow.md`。
4. 增加 `docs/demo_script.md`。
5. 添加 Demo 截图。
6. 本地完整演示三遍。

验收标准：

- GitHub 首页能体现“Agent 分析”而不只是 Dashboard。
- 面试中 3 分钟能讲清楚项目背景、技术实现和业务价值。
- Demo 可使用 sample data 稳定展示。

## 14. 面试讲解重点

### 14.1 30 秒版本

这是一个面向 Web3 现货运营场景的链上资金流 Agent。它会实时拉取 USDC Transfer 数据，经过解析和 pandas 聚合后，在 Streamlit 上展示资金流看板。同时，我新增了 Agent 分析层：先用规则识别大额转账、地址集中度和目标地址净流入异常，再调用 LLM API，把结构化指标转成运营同学可直接使用的日报、异常解释和行动建议。

### 14.2 重点表达

1. 我不是单纯做一个图表看板，而是把运营分析流程拆成了数据获取、数据解析、指标计算、异常识别、Agent 分析和报告生成。
2. Agent 的输入不是随意文本，而是当前 Dashboard 的结构化指标和异常信号。
3. 规则检测保证稳定性，LLM 负责解释和表达优化。
4. 这个项目对应 JD 中的数据整理、内容优化、基础分析、看板搭建和 AI 工具提效。

## 15. 风险与兜底方案

| 风险 | 影响 | 兜底方案 |
|---|---|---|
| Alchemy API 临时失败 | 无法实时拉数据 | 使用 sample CSV 演示 |
| LLM API 失败 | 无法生成 AI 报告 | 使用模板报告兜底 |
| 主网 USDC 日志量过大 | 查询慢或失败 | 缩小 block_span / chunk_size |
| 面试现场网络不稳定 | Demo 卡顿 | 提前录屏和截图 |
| Agent 输出幻觉 | 报告不可信 | Prompt 中要求严格基于输入数据，且展示 Agent 输入 JSON |

## 16. 项目最终交付物

1. 可运行的 Streamlit Dashboard。
2. 真实链上数据获取与解析模块。
3. pandas 指标分析模块。
4. Agent 分析模块。
5. 真实 LLM API 接入。
6. AI 运营分析报告生成。
7. README。
8. `docs/project_design.md`。
9. Demo 截图。
10. 面试演示稿。

## 17. 后续版本路线

### v0.1：当前版本

- USDC 实时数据看板。
- 概览、事件流、时间序列、地址分析。

### v0.2：面试版本

- Agent 分析 Tab。
- 异常检测。
- 真实 LLM API。
- AI 运营日报。

### v0.3：增强版本

- sample/live 数据切换。
- Markdown 报告下载。
- README 和演示文档完善。

### v1.0：可产品化版本

- 多 token。
- 多链。
- 地址标签。
- 历史基线。
- 定时任务。
- 飞书/邮件推送。

