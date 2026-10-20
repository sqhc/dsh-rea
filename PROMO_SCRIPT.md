# dsh-rea 推广视频脚本 / 分镜

## 核心要求
- 时长 ≤ 60 秒
- 中英双版本（可同一视频双语字幕/旁白，或分别制作）
- 格式：适合 README 嵌入（GIF / MP4 / WebM / 外链视频平台）
- 定位：**Unofficial / packaging layer**，严禁暗示官方背书
- 关键信息点（必须覆盖）：
  1. 配置层打包插件
  2. 无 REA 源码
  3. npm 运行时拉取官方包
  4. 207 个 REA 工具接入 DSH（`mcp__rea__<tool>`）
- 本机 ffmpeg 8.1 无 drawtext/subtitles → 字幕需用其他方案

---

## 视频结构设计（60 秒）

| 时间段 | 画面内容 | 中文旁白/字幕 | 英文旁白/字幕 | 备注 |
|--------|----------|---------------|---------------|------|
| 0-3s | Logo 淡入 + 标题 | dsh-rea | dsh-rea | icon.svg 放大淡入 |
| 3-8s | 核心定位一句话 | **非官方 / 纯配置层** | **Unofficial / packaging layer only** | 加粗显示，醒目 |
| 8-18s | 展示安装流程 | 克隆仓库 → `plugin_manager install` | Clone repo → `plugin_manager install` | 终端录屏或动画 |
| 18-28s | 核心原理图解 | **无源码** · npm 运行时拉取 `rea-agents@6.7.0` | **No source** · npm pulls `rea-agents@6.7.0` at runtime | 箭头图：npm → npx → REA MCP |
| 28-42s | 工具目录演示 | **207 个 REA 工具** → `mcp__rea__*` | **207 REA tools** → `mcp__rea__*` | 实测：preflight 输出工具数 |
| 42-52s | 实际调用演示 | 调用 `mcp__rea__binary_session` 验证 | Call `mcp__rea__binary_session` to verify | 终端/DSH 界面录屏 |
| 52-57s | 兼容性/配置提示 | `cordis.patch.yml` 可改版本 · Node 22/24/26 | Edit `cordis.patch.yml` for version · Node 22/24/26 | 快速闪过配置表 |
| 57-60s | 结尾 + 链接 | GitHub: sqhc/dsh-rea · MIT | GitHub: sqhc/dsh-rea · MIT | 仓库链接 + 许可证 |

---

## 双语制作方案对比

| 方案 | 优点 | 缺点 | 推荐度 |
|------|------|------|--------|
| **方案 A：同一视频 + 双语字幕文件（SRT/VTT）** | 维护单一视频源；README 嵌入 `<video>` 支持 `track` | ffmpeg 无 drawtext → 需外部工具烧录字幕或用播放器加载外挂字幕 | ⭐⭐⭐⭐ |
| **方案 B：分别制作中英两版视频** | 无字幕技术债；各版本节奏可微调 | 工作量 ×2；README 需放两个视频或用语言切换 JS | ⭐⭐⭐ |
| **方案 C：纯视觉 + 关键词标注（无旁白），配双语说明文案** | 无音频/字幕技术问题；GIF/WebM 体积小 | 信息密度依赖文字，需配合 README 文案 | ⭐⭐⭐⭐⭐ |
| **方案 D：浏览器录屏 + 后期合成（用 canvas/remotion 或 screen studio）** | 完全可控，支持任意字幕/动画 | 需额外工具链 | ⭐⭐⭐ |

---

## 推荐方案：方案 C + 方案 A 混合（最务实）

1. **主视频**：制作 **无声、纯视觉演示** 的 MP4/WebM（≤60s），关键节点用**画面内关键词标注**（如 "Unofficial"、"207 tools"、"npm pull"、"mcp__rea__"），不依赖字幕轨。
2. **双语覆盖**：README 顶层放视频，**视频下方紧跟中英双语要点列表**（已基本在 README 有，微调即可）。
3. **字幕回退**：若必须要字幕，用 **Remotion (React 合成视频)** 或 **ScreenToGif/kap 录屏后用 Aegisub 手工加字幕再导出**，不依赖 ffmpeg drawtext。
4. **格式**：输出 **WebM (VP9) + MP4 (H.264)** 双格式，`<video>` 标签双 source；同时生成 **GIF 预览**（首帧+关键帧）供不支持视频的场景。

---

## 制作工具链（避开 ffmpeg drawtext 限制）

| 环节 | 推荐工具 | 说明 |
|------|----------|------|
| 终端录屏 | `asciinema` + `agg` → GIF/MP4，或 `vhs` (charmbracelet) | 纯文本终端演示最清晰 |
| GUI 录屏 | macOS 自带 `截图工具` (Cmd+Shift+5) / `kap` / `ScreenToGif` | 录 DSH 界面调用工具 |
| 动画合成 | **Remotion** (npm, React 合成视频，完美支持字幕/动画) | `npx remotion studio` 可视化调节，输出 MP4/WebM |
| 字幕烧录（备选） | **Aegisub** 手工做字幕 → `ffmpeg -vf "ass=sub.ass"` (ass 滤镜通常可用) | 验证本机 ffmpeg 是否支持 `libass` |
| 格式转换 | `ffmpeg -i in.mp4 -c:v libvpx-vp9 -b:v 1M out.webm` | 双格式输出 |

---

## 素材准备清单

- [ ] `icon.svg` 放大动画（0-3s）
- [ ] 终端演示：`git clone` → `plugin_manager install`（可用 asciinema 录制）
- [ ] 架构图解：npm → npx → REA MCP → DSH（可用 Mermaid/Excalidraw 画一张静态图，再做简单推拉动画）
- [ ] `node scripts/preflight.mjs` 实测输出（工具数 207、catalog 大小）
- [ ] DSH 界面调用 `mcp__rea__binary_session` 返回版本 6.7.0
- [ ] `cordis.patch.yml` 关键配置项特写

---

## README 嵌入代码模板

```markdown
<p align="center">
  <video width="100%" max-width="720" controls preload="metadata" poster="promo-poster.png">
    <source src="promo.webm" type="video/webm">
    <source src="promo.mp4" type="video/mp4">
    <track kind="subtitles" src="promo.zh.vtt" srclang="zh" label="中文" default>
    <track kind="subtitles" src="promo.en.vtt" srclang="en" label="English">
    Your browser does not support the video tag.
  </video>
  <br>
  <sub>🇨🇳 <a href="#中文版">中文版</a> | 🇺🇸 <a href="#english">English</a></sub>
</p>
```

> 若 GitHub README 不支持 `<video>`，改用 **GIF** + "点击观看完整视频" 链接到外部托管（YouTube/B站/自建）。

---

## 下一步行动项

1. **确认方案**：团队确认上述方案 C（纯视觉+关键词标注）+ 双语要点列表，还是要真字幕？
2. **录制素材**：跑一次 `node scripts/preflight.mjs` 录屏；DSH 里调用 `mcp__rea__binary_session` 录屏。
3. **制作视频**：用 Remotion 或 kap + 后期合成，输出 MP4/WebM/GIF。
4. **嵌入 README**：在两个 README 顶部（icon 下方）插入视频/GIF。
5. **验证**：GitHub README 渲染正常，视频 ≤1 分钟，体积可接受（目标 <5MB）。

---

## 备注：ffmpeg 字幕可用性自测

```bash
ffmpeg -filters | grep -i ass   # 若有 ass 滤镜，可用 ASS 字幕烧录
ffmpeg -filters | grep -i drawtext  # 确认无 drawtext
```

若 `ass` 可用，方案 A 完全可行；否则坚持方案 C。