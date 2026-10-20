# dsh-rea 上游监控基线报告

**生成时间**: 2026-10-19
**监控员**: 上游监控 Bot

---

## 当前锁定版本

| 依赖 | 当前版本 | npm latest | npm next/alpha | 状态 |
|------|----------|------------|----------------|------|
| `rea-agents` | 6.7.0 | 6.7.0 | — | ✅ 同步 |
| `@deepseek-ai/dsh-mcp-client` | (由 DSH 管理) | 0.0.1-rc.1 | 0.2.1-rc.2 / 0.2.1-alpha.5 | ⚠️ 关注 |

---

## rea-agents 版本历史 (最近 10 版本)

| 版本 | 发布日期 | 备注 |
|------|----------|------|
| 6.7.0 | 2026-10-18 | Client 配置编辑修复；6.6.0 未发布到 npm |
| 6.5.0 | 2026-10-14 | — |
| 6.4.0 | 2026-10-11 | — |
| 6.3.0 | 2026-10-10 | — |
| 6.2.0 | 2026-10-09 | — |
| 6.1.0 | 2026-10-09 | — |
| 6.0.0 | 2026-10-08 | Major: Node 引擎要求更新 |
| 5.0.0 | 2026-10-07 | Major |
| 4.1.0 | 2026-10-06 | — |
| 4.0.1 | 2026-10-05 | — |

**观察**: 10 月以来每日多版本，6.x 线 10 天发了 8 个版本。6.6.0 被跳过（仅打 tag 未发 npm）。

---

## 6.7.0 关键变更 (2026-10-18)

### 修复
- **Client 配置**: Setup 编辑最后一个重复 JSON/JSONC member，匹配客户端实际读取行为；拒绝会重新激活 shadowed duplicate 的移除操作

### 包含 6.6.0 变更 (未发 npm)
- 新增 Kuna 作为 caller-supplied 静态分析 provider
- 保留完成的 Evidence、取消原因、可重试清理
- Windows ARM PE、raw m68k 镜像支持
- JADX deadline 可配置

---

## dsh-mcp-client 版本情况

| Tag | 版本 | 日期 | 备注 |
|-----|------|------|------|
| latest | 0.0.1-rc.1 | 2026-08-10 | 很旧 |
| alpha | 0.2.1-alpha.5 | 2026-10-16 | 最新 alpha |
| next | 0.2.1-rc.2 | 2026-10-17 | 最新 rc |

**风险**: `latest` 标签指向 2 月前版本，实际活跃开发在 `next`/`alpha`。dsh-rea 作为 bundle 由 DSH 运行时注入 client，需确认 DSH 使用哪个版本。

---

## cordis.patch.yml 关键配置

```yaml
- insert:
    - id: rea-mcp
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: rea
        transport: stdio
        command: npx
        args: ['-y', 'rea-agents@6.7.0', 'mcp']
        env:
          NPM_CONFIG_CACHE: <动态计算>
          REA_MCP_INPUT_SCHEMA_PROFILE: 'compact'
          REA_MCP_OUTPUT_SCHEMA_PROFILE: 'off'
        toolCallTimeoutMs: 600000  # 10 分钟
        failOnStartupError: false
```

**关注点**:
- `rea-agents@6.7.0` 硬编码在 args 中
- 超时 10 分钟，首次启动可能下载包
- 启动错误不失败插件行

---

## preflight.mjs 基线

- `REA_VERSION = "6.7.0"` 硬编码
- Node 支持: 22.19+, 24.11+, 26+
- MCP 握手: initialize → tools/list
- 输出: 工具数量、catalog 大小、最大 schema top 3

---

## 待评估事项

1. **dsh-mcp-client 版本对齐**: 确认 DSH 运行时实际使用的版本，如有接口变化需评估 cordis.patch.yml 是否需调整
2. **REA 6.7.0 新工具/Schema 变化**: 需跑 preflight 对比工具数量和 catalog 大小
3. **6.6.0 合并变更**: 虽未发 npm 但 6.7.0 包含其变更，Kuna provider、JS facts 保留等可能影响工具集
4. **监控自动化**: 建立定时检查 npm 版本 + GitHub releases 的机制

---

## 建议行动

1. **立即**: 运行 `node scripts/preflight.mjs` 建立工具基线（交给 @回归测试）
2. **近期**: 确认 DSH 使用的 dsh-mcp-client 版本
3. **持续**: 每周一检查 rea-agents 新版本，有变更产出评估报告 → 提 PR