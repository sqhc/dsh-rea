# rea-agents 6.7.0 → 6.8.0 升级评估报告

**生成时间**: 2026-10-27
**评估员**: 上游监控
**监控报告**: `.monitor/monitoring-2026-10-27.md`

---

## 版本变更概览

| 项目 | 当前 | 目标 | 变更类型 |
|------|------|------|----------|
| rea-agents | 6.7.0 | 6.8.0 | **Minor (含 Breaking Changes)** |
| dsh-mcp-client | DSH 管理 | 无变化 | — |
| Node.js 引擎要求 | ^22.19.0 \|\| ^24.11.0 \|\| >=26.0.0 | ^22.23.4 \|\| ^24.22.1 \|\| >=26.12.1 | **升级要求** |

**发布日期**: 2026-10-25
**提交数**: 1740 commits, 497 merged PRs

---

## ⚠️ 破坏性变更风险评估 (HIGH)

以下变更**直接影响 dsh-rea 用户**：

| 变更 | 影响 | 缓解措施 |
|------|------|----------|
| **Node.js 引擎要求升级** | 要求 Node 22.23.4+ / 24.22.1+ / 26.12.1+；Node 23/25 明确不支持 | 更新 `preflight.mjs` 的版本检查逻辑；确认 DSH 运行时满足要求 |
| **`analyze_function` 默认返回 summary** | MCP 调用者若期望完整 dossier 需显式传 `detail: "complete"` | 我们的 preflight 不直接调用该工具，**低风险** |
| **Accessibility node.value 接受 number/boolean** | 消费端假设 text-only 会报错 | 不直接暴露给用户，**低风险** |
| **JSON Lines 输出格式变更** | CLI `--format jsonl` 增加 control record | 我们不使用 CLI jsonl，**无影响** |
| **Interface Builder keyed-archive UID 变更** | 持久化图查找需迁移 | 仅影响特定工具，**低风险** |
| **Frida instrument-with-frida 返回结构变更** | 需读 `normalized_result.cleanup_error` | 仅影响 Frida 用户，**低风险** |
| **MCP input schema 默认 compact** | 已是我们的配置 (`REA_MCP_INPUT_SCHEMA_PROFILE=compact`)，**无影响** | ✅ 已兼容 |
| **Browser storage 历史哈希不可比较** | 需重新捕获 | 仅影响浏览器捕获对比，**低风险** |
| **Mach-O import name 可能为 null** | 需用 `raw_name`/`name_status` 区分 | 仅影响 Mach-O 分析，**低风险** |

**结论**: 核心风险在 **Node.js 版本要求升级**；MCP 工具接口变更对我们透明（通过 dsh-mcp-client 桥接）。

---

## ✨ 新功能亮点 (对 dsh-rea 用户可见)

| 功能 | 说明 | 用户价值 |
|------|------|----------|
| **Agent Environments** | 从网络捕获/浏览器场景/提示词构建环境，支持 replay 对比 | 🔥 高：新工作流 |
| **新格式支持** | GPU 代码对象、BEAM、Python bytecode、Unity IL2CPP、Godot PCK、PyInstaller、Node.js SEA、devicetree、PE/ELF 新表 | 🔥 高：覆盖面大幅扩展 |
| **Retained Summaries / Selected Facts** | 大型调查保留摘要、可查询选定事实、可配置恢复限制 | ✅ 高：性能/Token 优化 |
| **Binary Layout: ELF32 i386/ARM/MIPS** | Linux x64 上通过 pwntools 分析更多架构 | ✅ 中 |
| **PE/ELF 深度检查** | 导出表、导入/延迟加载、Authenticode、TLS 回调、ELF notes、内核模块元数据、Zstd section | ✅ 高 |
| **Android APK 签名/清单组件** | 结构化清单、静态 final DEX 字段值 | ✅ 中 |
| **Bytecode: CPython pyc / BEAM / devicetree / MMIO** | 新检查维度 | ✅ 中 |
| **JavaScript: 静态路由 inventory、赋值链接写入** | 更完整的 JS 分析 | ✅ 高 |
| **Data: protobuf/gRPC、GGUF/safetensors、byte-entropy** | ML/数据格式支持 | ✅ 中 |
| **MCP: Streamable HTTP / FreeBuff 注册** | 新传输/注册选项 | 🔍 观察：FreeBuff 首次出现，未验证 |

---

## 配置文件需更新项

### 1. `cordis.patch.yml`
```yaml
args: ['-y', 'rea-agents@6.8.0', 'mcp']  # 版本号更新
```

### 2. `scripts/preflight.mjs`
```javascript
const REA_VERSION = "6.8.0";
// Node 支持检查需更新：
const nodeSupported =
  (major === 22 && minor >= 23) ||  // 22.23.4+
  (major === 24 && minor >= 22) ||  // 24.22.1+
  major >= 26;                      // 26.12.1+ (注意：23/25 不支持)
```

---

## 基线预期变化

升级后 preflight 可能产生不同 baseline（需实测）：
- **工具数**: 可能增加（新格式/工具）
- **Catalog 大小**: 可能增加（新 schema）
- **REA 版本**: 6.8.0

---

## 推荐策略：跟随升级 ✅

**理由**：
1. 6.8.0 是 minor 版本但含大量功能增强，非纯补丁
2. 破坏性变更主要在 CLI/内部接口，MCP 层对我们影响可控
3. Node.js 要求升级符合 DSH 运行时演进方向（v24.21.0 已满足 24.22.1+ 预期）
4. REA 迭代极快，跳过可能积累更大迁移成本

**执行步骤**：
1. 创建 PR 更新版本号 + preflight Node 检查
2. Chief 审批合并
3. 回归测试跑 preflight 确认新 baseline
4. 文档社区更新兼容性表 + Release Notes
5. 推广担当更新视频版本号/工具数

---

## 风险提示

- **首次启动下载时间**: 6.8.0 包体积 49MB (6.7.0 28MB)，首次 npx 耗时可能增加
- **Windows**: 记录为已知风险，回归测试仅 macOS/Linux
- **FreeBuff**: 首次集成，未验证，不影响核心流程
- **如果 DSH 运行时 Node < 24.22.1**: 需协调升级运行时

---

## 后续行动清单

- [ ] 创建评估 PR (更新 cordis.patch.yml + preflight.mjs)
- [ ] Chief 审批合并
- [ ] 回归测试跑 preflight 确认新 baseline
- [ ] 文档社区更新兼容性表 + Release Notes
- [ ] 推广担当更新视频素材