# 🔧 06 — 项目文档生成提示词（元提示词合集）

> 🎯 **目标**：掌握如何用 AI 帮你自动生成项目文档、架构图和 README。
> ⏱️ 预计时间：0.5 天

---

## 📋 这组提示词是做什么的？

这 4 个提示词是"元提示词"（Meta-Prompt）——让 AI 帮你的项目**自动写文档**，而非让你手动写。

| # | 用途 | 什么时候用 | 产出 |
|---|------|----------|------|
| 1 | **Runbook 生成器** | 每个新项目开始前 | 完整的 `WeekX_runbook.md` |
| 2 | **源码审计** | 项目完成后 | `PROJECT_AUDIT_MASTERY.md` |
| 3 | **README 生成器** | 推 GitHub 前 | 标准 `README.md` |
| 4 | **架构图生成器** | 需要可视化时 | draw.io XML 文件 |

### 使用方式

1. 复制对应的提示词
2. 替换 `{{}}` 占位符为你的实际项目信息
3. 粘贴到 Claude Code / ChatGPT / Cursor 中
4. AI 扫描项目后输出对应文档
5. 人工 Review + 修改（AI 可能遗漏或误判）

---

## 提示词 1:工程级项目 Runbook 生成提示词

```
# Role
你现在是一位全球顶尖的 AI Infra 架构师，同时也是一位开源社区的资深布道师。我正在进行“大模型应用工程师 9 周专家级实战路线”，我需要你指导我完成本周的项目，并为我输出一份可以直接存入 GitHub 的工程级 `runbook.md` 文档。

# Context & Environment
本周学习主题是：[在这里填入具体主题，例如：Week 3 Diffusers 生成式视觉工程底座]

请严格基于我的真实物理环境和技术栈约束来设计工程架构和执行命令：
- 硬件：MacBook Air M5，32GB 统一内存，macOS。
- 环境隔离：只使用 Conda 虚拟环境（环境名为 `cxllm`），Python 3.11。绝不使用 venv。
- 开源目标：这个项目最终会提交到 GitHub 作为我的个人作品集，供他人克隆学习。因此代码结构必须高度规范，防呆设计要足。
- 工具链原则：必须使用行业最新版的命令和工具（例如必须用 `hf` 替代已废弃的 `huggingface-cli`，优先使用针对 Apple Silicon 的底层优化参数）。

# Task Requirements
请为我生成一份详细的 `WeekX_runbook.md`，必须包含以下核心章节，且语气要专业、硬核，充满工程化洞察：

## 1. 工程化目录架构
- 生成一个符合现代 Python/AI 项目规范的目录树（包含 `configs/`, `scripts/`, `src/`, `tests/`, `docs/` 等）。
- 必须包含一个 `Makefile`，并在这一节用一句话解释每个目录的作用。

## 2. 依赖安装与最新工具链配置
- 给出在 `cxllm` 环境下的极速包安装命令。如果涉及到 Apple Metal 加速相关的包，请特别指出安装避坑指南。

## 3. 分终端执行与测试流程（Debug 视角）
- 按照真实的开发顺序，教我如何开多个终端分布调试（例如终端 1 跑底座服务，终端 2 跑网关，终端 3 做 Curl 或业务层压测）。
- 必须包含具体的命令、模型下载方法（需精算 32GB 统一内存的承载极限）以及预期看到的成功日志。

## 4. 终极一键运行：Makefile 集成
- 因为我要开源给小白或面试官看，必须提供一个极其优雅的 `Makefile` 源码。
- 里面需要包含 `make setup` (安装依赖)、`make run-all` (一键按顺序拉起所有服务)、`make clean` (清理缓存和模型数据) 等指令。使用 tmux 或 nohup/后台进程的技巧来实现在一个命令下管理多个服务，并在 README 中说明如何终止它们。

## 5. 常见坑点与硬件降维打击方案
- 针对 32GB M5 芯片、Conda 环境或网络代理可能遇到的报错（例如端口冲突、OOM、代理劫持），给出至少 3 个提前预判的避坑指南。

## 6. 面试深度解析
- 针对本周的主题，给出 3 道资深 AI Infra 工程师的面试题以及核心答题思路，要求包含底层硬件或数据流视角的深度思考。

# Output Style
- 输出格式必须是完整的 Markdown，方便我直接复制保存为 `runbook.md`。
- 不要废话，不要讲“你好我是AI”，直接输出硬核的 Markdown 内容。
```



## 提示词 2：生成项目源码级心智模型介绍

```text
# Role
你是一位顶级 AI 全栈架构师、源码审计专家与技术文档专家。你的任务是通过逆向阅读代码库，帮我建立对当前项目的源码级心智模型，而不是泛泛写项目介绍。

# Task
请完整扫描当前工作区的源码、配置、依赖、脚本、文档和测试文件。不要预设技术栈，先自动识别项目使用的前端、后端、数据库、AI/算法框架、部署方式、测试体系和工具链。最终生成《项目架构与源码掌控白皮书》：PROJECT_AUDIT_MASTERY.md。

# Core Rules
1. 零预设：先扫描 package.json、requirements.txt、pyproject.toml、pom.xml、go.mod、Dockerfile、docker-compose.yml、.env、README、src、server、backend、frontend、tests 等文件，再判断技术栈。
2. 证据绑定：任何架构结论、数据流、接口、数据库、模型机制、启动方式、风险判断，都必须附源码证据，格式为：[文件路径 -> 类名/函数名/变量名/配置项]。
3. 禁止脑补：鉴权、日志、测试、事务、OOM 防御、Token 截断、限流、配置管理、CI/CD、Docker、持久化等能力，未在代码中发现就明确写“❌ 未发现实现”。
4. 区分现状与建议：严格区分“当前代码已实现”和“未来优化建议”。

# Output Structure

## 1. 项目总览
说明项目目标、核心场景、技术栈、最小运行闭环、当前最大风险，并列出核心入口文件。

## 2. 目录与依赖图谱
给出核心目录树，解释每个目录职责；列出前端、后端、数据库、AI/算法、部署、测试相关依赖及版本。

## 3. 启动与环境边界
总结依赖安装、前端启动、后端启动、数据库/模型初始化、自测命令；扫描环境变量和硬编码端口、路径、URL、密钥、模型路径。

## 4. 数据流与接口契约
枚举核心 API/HTTP/SSE/WebSocket/RPC 接口，列出请求体、响应体、调用方和实现位置；追踪 1-2 条最重要业务流，从 UI 事件 -> 请求发送 -> 后端路由 -> 核心逻辑 -> 数据库/模型 -> 响应返回 -> 前端状态更新。

## 5. 数据库与持久化
列出核心实体、表结构、字段、关系、CRUD 触发时机、事务处理和一致性风险；若无数据库，标“❌ 未发现持久化机制”。

## 6. 核心业务与 AI 引擎
定位项目处理大脑：业务 service、RAG、Agent、模型推理或算法模块。说明模型/资源如何加载、是否常驻内存、Prompt 如何构造、Token 如何管理、流式输出如何实现；无相关模块则标未发现。

## 7. 防御、日志与测试
审计异常处理、fallback、输入校验、安全边界、CORS、限流、OOM 风险、日志框架、print/console.log、测试目录和测试覆盖；未发现必须直说。

## 8. 部署、故障与技术债
判断是否纯本地运行或具备 Docker/CI/CD；列出高频故障排查表：端口冲突、依赖缺失、接口地址错、数据库路径错、模型加载失败等。最后列出 P0/P1/P2 技术债和 10 倍并发/企业级部署的重构建议。

## 9. 开发者掌握清单
列出我必须能讲清楚的 20 个问题、必须能独立完成的 10 个操作，以及达到 L4/L5 掌握等级还需要补齐的知识。

# Formatting
全文使用标准 Markdown、表格和必要的 Mermaid 图。语言专业、直接、客观。所有关键判断必须有源码证据；不得编造；未发现就明确标注；不要把优化建议写成当前事实。
```

---

## 提示词 3：生成 GitHub 仓库 README.md

```text
# Role
你是一位顶级全栈架构师、AI Infra 工程顾问与开源项目 Technical Writer，擅长把真实工程项目整理成专业、可信、适合 GitHub 展示与学习复现的 README.md。

# Task
请完整阅读当前项目的 README、docs、源码、目录结构、依赖文件、配置文件、脚本、Docker 文件、测试文件和我提供的项目说明。在不预设技术栈的前提下，自动识别项目类型、核心功能、技术栈、运行方式、学习价值和工程亮点，然后重写或生成一份完整的 GitHub README.md。

该项目属于“大模型应用工程师 / AI Infra 工程师学习路线”的实战项目之一，README 不仅要展示项目，还要帮助学弟学妹理解、复现和学习工程实践。

# Core Rules
1. 不得预设框架或架构。必须先扫描 package.json、requirements.txt、pyproject.toml、Dockerfile、docker-compose.yml、.env.example、src/、frontend/、backend/、server/、gateway/、scripts/、docs/、tests/ 等真实文件后再判断技术栈。
2. 所有功能描述必须来自真实代码、配置、文档或我提供的项目说明；不确定内容标注“待确认”，不得编造。
3. 必须明确区分：已实现、部分实现、计划中、可选增强。
4. README 要兼顾 GitHub 展示、学习记录、复现友好和企业级工程实践感。
5. 如果项目没有前端、后端、数据库、AI、Docker、测试、监控等模块，不要硬写，省略或标注“当前未涉及”。
6. 如果涉及模型、数据集或权重，必须说明来源、下载方式、存放位置、license 待确认项，以及大文件不应提交 Git。

# README Structure
请生成完整 README.md，必须包含以下部分：

## 1. 项目标题与徽章
生成专业项目名；根据真实技术栈添加 Shields.io 徽章，如 Python、FastAPI、Vue、TypeScript、Docker、llama.cpp、License 等。未发现 License 时写 License: TBD，不要伪造。

## 2. 项目简介
用 100-200 字说明项目解决什么问题、适合什么场景、核心价值是什么，以及它在大模型学习路线中的位置。

## 3. 学习目标
说明完成本项目后，学习者能掌握哪些工程概念，如本地推理、模型服务化、流式响应、Docker、压测、可观测性、前后端联调等。

## 4. 功能亮点
用 4-8 条列出核心能力，并使用：
- ✅ 已实现
- 🟡 部分实现
- 🚧 计划中
不得把规划写成已完成。

## 5. 技术栈
按真实内容分类展示：前端、后端、AI/推理、部署、监控、测试、工具链。未发现的分类不要硬写。

## 6. 系统架构
使用 Mermaid 或文本图展示整体数据流，并简要解释核心模块职责。例如：Frontend → Gateway → Model Server → Model / Metrics。

## 7. 项目目录结构
给出核心目录树，每个关键目录后写一句职责说明。不要展开缓存、构建产物或大模型文件。

## 8. 快速开始
必须包含：
- 环境要求
- 克隆项目
- 依赖安装
- 环境变量配置
- 模型或资源下载
- 启动服务
- 最小自测命令，如 curl / health check / 浏览器地址
如果存在多种运行方式，请区分推荐路线、Docker 路线和 fallback 路线，并说明适合谁。

## 9. 核心使用方式
说明主要功能如何使用，可包含 API 示例、CLI 命令、前端流程、Docker 命令、压测命令、metrics 查看方式等。

## 10. 关键实现说明
解释 3-5 个最能体现技术深度的实现点，包括设计动机、实现方式、工程价值和当前限制。不要写成源码审计报告。

## 11. 复现与排错指南
面向初学者列出常见问题、原因和解决方式。例如：依赖安装失败、端口占用、模型文件不存在、Docker 很慢、环境变量错误、.venv/conda 混用等。

## 12. 学习路线中的位置
说明本项目属于学习路线的哪个阶段，前置知识是什么，后续可以衔接哪些项目。

## 13. Roadmap
分短期优化、中期增强、长期演进。只写合理规划，不要写成已实现。

## 14. License / Author / Acknowledgements
若未发现 License，写待确认。列出真实使用的开源项目和依赖，不要编造。

# Formatting
使用标准 Markdown；标题层级清晰；适当使用 Emoji；代码块标注语言；表格整洁；命令必须可复制；语言专业、简洁、有吸引力。

# Output Mode
请直接修改或生成 README.md，并在完成后列出识别到的技术栈、修改文件、待确认内容和建议补充项。
```

## 提示词4:生成项目模型架构图

`````
# Role

你是一位资深 AI Infra 首席架构师与技术制图专家。请完整阅读当前项目的所有关键源码、配置、依赖、脚本和文档，生成一份可以导入 draw.io / diagrams.net 的架构全景图 XML。

# Phase 1: 项目理解

请先扫描以下文件并给出架构识别摘要：

- README.md、Makefile、package.json、requirements.txt、pyproject.toml
- 后端入口文件（app.py / main.py / server.js 等）
- 路由文件（routes/、controllers/ 等）
- 核心业务模块（engine、service、pipeline、agent 等）
- AI/模型推理模块（llm.py、model.py、inference.py 等）
- 前端入口（App.vue、main.ts、index.html 等）
- 配置与脚本（.env.example、scripts/、Dockerfile 等）
- 测试目录（tests/）

输出：

1. **架构识别摘要**：项目类型、技术栈、核心入口、主数据流
2. **核心模块清单表**：层级 | 文件 | 核心类/函数 | 职责

# Phase 2: 生成 draw.io XML

基于 Phase 1 的分析，生成一份 draw.io XML 架构图，严格遵循以下规范。

## 2.1 文本精简规则

- **绝对禁止**出现具体数值：端口号、文件大小、延迟毫秒数、HTTP 状态码列表、量化参数等全部移除
- **禁止枚举**：如 "① Timing ② RequestId ③ RateLimit ④ ApiKey ⑤ CORS" 应合并为 "全局中间件链"
- 每个节点最多 **2 行文本**：第一行中文业务语义（大字加粗），第二行英文文件名（小字浅色斜体）

## 2.2 中文优先规范

节点文本格式（HTML）：
```xml
<font style="font-size:24px;"><b>🌐 中文功能描述</b></font><br>
<font style="font-size:16px;" color="#8899aa"><i>英文文件名 · 补充说明</i></font>
```

- 第一行：中文业务语义 + Emoji 图标，`font-size:24px`，`<b>` 加粗
- 第二行：英文文件名 + 技术关键词，`font-size:16px`，`color="#8899aa"`，`<i>` 斜体

## 2.3 字体字号规范

| 元素 | 字号 |
|------|------|
| 主标题 | `fontSize=28` |
| 层标签（tag） | `fontSize=22` |
| 技术标签（FastAPI/MLX 等） | `fontSize=18` |
| 节点主文字（中文） | `font-size:24px` |
| 节点副文字（英文） | `font-size:16px` |
| 层间箭头标签 | `fontSize=16` |
| 图例/脚注 | `fontSize=15-16` |

## 2.4 五层架构布局（从上到下）

| 层级 | 背景色 | 边框色 | Tag 色 | 标题示例 |
|------|--------|--------|--------|----------|
| 用户入口层 | `#eef4ff` | `#b0c4de` | `#dae8fc` / `#6c8ebf` | 用户入口层 |
| API 服务层 | `#eeffee` | `#a0c8a0` | `#d5e8d4` / `#82b366` | API 网关层 / API 服务层 |
| AI 推理引擎层 | `#f6f0fa` | `#b8a0c8` | `#e1d5e7` / `#9673a6` | AI 推理引擎层 |
| 数据与存储层 | `#f4f4f4` | `#b0b0b0` | `#e0e0e0` / `#999999` | 数据与存储层 |
| DevOps 工具层 | `#fff8f0` | `#d0b080` | `#ffe6cc` / `#d79b00` | DevOps 与质量保障 |

**重要**：根据实际项目调整层数和命名。如果项目没有独立的 API Gateway 层（如 MLX 项目只有 Server），则将 "API 网关层" 改为 "API 服务层"。不要强行套用不存在的层级。

## 2.5 画布与布局参数

```
pageWidth="1400" pageHeight="1100"
每层背景: x="50" width="1300" height="145"（L1-L3）/ height="130"（L4-L5）
层间距: 45px（L1底部→L2顶部）
每层 3 个白底节点: width="340"/"340"/"290", 间距 48px
节点高度: 108px（L1-L3）/ 100px（L4-L5）
节点样式: rounded=1; fillColor=#FFFFFF; strokeColor=<同层边框色>; spacingTop=14; spacingBottom=10
```

## 2.6 层间箭头规范

- 每个层间一个垂直箭头 + 右侧标签
- 实线 = 主数据流，虚线 = 观测/工具
- 箭头: `strokeWidth=2.5; endArrow=block; endFill=1`
- 标签: 白色背景圆角小框，`fontSize=16; fontStyle=1`

## 2.7 图例规范

- 底部一个灰色细边框条，包含：
  - 实线箭头 + "主数据流"
  - 虚线箭头 + "观测 / 验证"（或"工具 / 编排"）
  - "白底节点 = 模块实例"
  - "浅色背景 = 架构分层"
- 图例右方放一行脚注：硬件 / 环境 / 关键约束

## 2.8 节点形状

- 普通模块：`rounded=1` 矩形
- 模型/数据库存储：`shape=cylinder3`
- 这二者之外**不使用**六边形、菱形、圆形等复杂形状，保持简洁统一

# Output Specification

直接输出 `<mxfile><diagram><mxGraphModel>...` 完整 XML，不要输出任何解释文字。
````

---

## 参考 XML 模板（可直接嵌入提示词中作为示例）

以下是一张完整架构图的 XML 模板，包含 5 层 × 3 节点 = 15 个核心模块 + 4 条层间箭头 + 图例。AI 可参照此结构生成新图。

```xml
<mxfile host="app.diagrams.net" modified="2026-06-06T00:00:00.000Z" agent="Claude" version="21.0.0">
  <diagram name="项目架构全景图" id="arch-main">
    <mxGraphModel dx="1400" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1400" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />

        <!-- 主标题 -->
        <mxCell id="title" value="[项目名称] 架构全景图" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=28;fontStyle=1;fontColor=#1a1a2e;" vertex="1" parent="1">
          <mxGeometry x="350" y="15" width="700" height="48" as="geometry" />
        </mxCell>

        <!-- 副标题 -->
        <mxCell id="subtitle" value="[技术栈简述]" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontColor=#8b949e;" vertex="1" parent="1">
          <mxGeometry x="250" y="63" width="900" height="24" as="geometry" />
        </mxCell>

        <!-- ====== L1: 用户入口层 ====== -->
        <mxCell id="L1-bg" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#eef4ff;strokeColor=#b0c4de;strokeWidth=1.5;" vertex="1" parent="1">
          <mxGeometry x="50" y="108" width="1300" height="145" as="geometry" />
        </mxCell>
        <mxCell id="L1-tag" value="用户入口层" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf;fontStyle=1;fontSize=22;" vertex="1" parent="1">
          <mxGeometry x="80" y="118" width="140" height="38" as="geometry" />
        </mxCell>

        <!-- L1 节点 1 -->
        <mxCell id="n1-1" value="&lt;font style=&quot;font-size:24px;&quot;&gt;&lt;b&gt;[emoji] [中文名]&lt;/b&gt;&lt;/font&gt;&lt;br&gt;&lt;font style=&quot;font-size:16px;&quot; color=&quot;#8899aa&quot;&gt;&lt;i&gt;[英文组件名]&lt;/i&gt;&lt;/font&gt;" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#b0c4de;fontSize=16;align=center;spacingTop=14;spacingBottom=10;" vertex="1" parent="1">
          <mxGeometry x="260" y="128" width="340" height="108" as="geometry" />
        </mxCell>

        <!-- L1 节点 2 (x=648) -->
        <!-- L1 节点 3 (x=1036, w=290) -->

        <!-- ====== L2-L5 类似 ====== -->
        <!-- 每层背景色不同，见配色表 -->
        <!-- 层间箭头: sourcePoint x=700, 箭头标签 x=745 -->

        <!-- 图例 -->
        <mxCell id="legend-bg" value="" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fafafa;strokeColor=#e0e0e0;strokeWidth=1;" vertex="1" parent="1">
          <mxGeometry x="50" y="1005" width="760" height="44" as="geometry" />
        </mxCell>
        <!-- 图例内容：实线+主数据流 | 虚线+观测验证 | 白底节点=模块 | 浅色背景=分层 -->

        <!-- 脚注 -->
        <mxCell id="footer" value="[硬件/环境/约束]" style="text;html=1;strokeColor=none;fillColor=none;align=right;verticalAlign=middle;whiteSpace=wrap;fontSize=15;fontColor=#bbb;" vertex="1" parent="1">
          <mxGeometry x="870" y="1015" width="480" height="26" as="geometry" />
        </mxCell>

      </root>
    </mxGraphModel>
  </diagram>
</mxfile>
```

---
`````

