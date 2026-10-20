#!/usr/bin/env python3
"""
Generate promotional video for dsh-rea.
Uses OpenCV to create frames with bilingual (Chinese/English) text.
"""

import cv2
import numpy as np
import os
from pathlib import Path

# Video settings
WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION_SEC = 55  # Under 1 minute
TOTAL_FRAMES = FPS * DURATION_SEC

# Colors (BGR)
BG_COLOR = (25, 28, 35)          # Dark background
ACCENT = (0, 180, 216)           # Cyan accent
TEXT_WHITE = (240, 240, 240)
TEXT_GRAY = (160, 160, 160)
TEXT_DIM = (100, 100, 100)
HIGHLIGHT = (0, 220, 140)        # Green highlight

# Font settings
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_BOLD = cv2.FONT_HERSHEY_DUPLEX

def draw_text(img, text, pos, font_scale, color, thickness=2, font=FONT):
    """Draw text with shadow for better readability."""
    x, y = pos
    # Shadow
    cv2.putText(img, text, (x+2, y+2), font, font_scale, (0, 0, 0), thickness+1, cv2.LINE_AA)
    # Main text
    cv2.putText(img, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)

def draw_text_centered(img, text, y, font_scale, color, thickness=2, font=FONT):
    """Draw text centered horizontally."""
    (text_w, text_h), _ = cv2.getTextSize(text, font, font_scale, thickness)
    x = (WIDTH - text_w) // 2
    draw_text(img, text, (x, y), font_scale, color, thickness, font)

def make_frame_blank():
    """Create a blank frame with background."""
    return np.full((HEIGHT, WIDTH, 3), BG_COLOR, dtype=np.uint8)

def add_gradient_bg(img):
    """Add subtle gradient to background."""
    for y in range(HEIGHT):
        alpha = y / HEIGHT
        color = tuple(int(BG_COLOR[i] * (1 - alpha * 0.15) + 15 * alpha) for i in range(3))
        cv2.line(img, (0, y), (WIDTH, y), color, 1)

def ease_in_out(t):
    """Smooth easing function."""
    return t * t * (3 - 2 * t)

def slide_in_text(img, text_en, text_zh, y_en, y_zh, progress, font_scale=1.2, color=TEXT_WHITE):
    """Slide in text from left with easing."""
    eased = ease_in_out(min(progress * 2, 1.0))
    offset = int((1 - eased) * WIDTH * 0.5)
    
    # English
    (tw_en, th_en), _ = cv2.getTextSize(text_en, FONT, font_scale, 2)
    x_en = (WIDTH - tw_en) // 2 - offset
    if x_en < WIDTH:
        draw_text(img, text_en, (max(0, x_en), y_en), font_scale, color, 2)
    
    # Chinese
    (tw_zh, th_zh), _ = cv2.getTextSize(text_zh, FONT, font_scale, 2)
    x_zh = (WIDTH - tw_zh) // 2 - offset
    if x_zh < WIDTH:
        draw_text(img, text_zh, (max(0, x_zh), y_zh), font_scale, color, 2)

def fade_in_text(img, text_en, text_zh, y_en, y_zh, progress, font_scale=1.0, color=TEXT_GRAY):
    """Fade in text."""
    alpha = min(progress * 3, 1.0)
    c_en = tuple(int(color[i] * alpha) for i in range(3))
    c_zh = tuple(int(color[i] * alpha) for i in range(3))
    draw_text_centered(img, text_en, y_en, font_scale, c_en, 2)
    draw_text_centered(img, text_zh, y_zh, font_scale, c_zh, 2)

def pulse_text(img, text_en, text_zh, y_en, y_zh, frame_idx, font_scale=1.0, base_color=HIGHLIGHT):
    """Pulsing highlight text."""
    pulse = 0.7 + 0.3 * np.sin(frame_idx * 0.15)
    color = tuple(int(base_color[i] * pulse) for i in range(3))
    draw_text_centered(img, text_en, y_en, font_scale, color, 2)
    draw_text_centered(img, text_zh, y_zh, font_scale, color, 2)

def draw_icon_area(img, center_x, center_y, radius, progress):
    """Draw animated icon placeholder."""
    eased = ease_in_out(progress)
    r = int(radius * eased)
    # Outer ring
    cv2.circle(img, (center_x, center_y), r, ACCENT, 3, cv2.LINE_AA)
    # Inner dot
    if r > 10:
        cv2.circle(img, (center_x, center_y), max(5, r // 4), ACCENT, -1, cv2.LINE_AA)

def draw_progress_bar(img, y, progress, width_ratio=0.6):
    """Draw a progress bar."""
    w = int(WIDTH * width_ratio)
    x = (WIDTH - w) // 2
    h = 6
    # Background
    cv2.rectangle(img, (x, y), (x + w, y + h), (60, 60, 60), -1, cv2.LINE_AA)
    # Fill
    fill_w = int(w * progress)
    cv2.rectangle(img, (x, y), (x + fill_w, y + h), ACCENT, -1, cv2.LINE_AA)
    # Border
    cv2.rectangle(img, (x, y), (x + w, y + h), (100, 100, 100), 1, cv2.LINE_AA)

# ==================== SCENES ====================

def scene_title(writer, start_frame, end_frame):
    """Scene 1: Title - dsh-rea"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        # Animated icon
        draw_icon_area(img, WIDTH // 2, HEIGHT // 2 - 60, 80, progress)
        
        # Title
        slide_in_text(img, "dsh-rea", "dsh-rea", 
                      HEIGHT // 2 + 40, HEIGHT // 2 + 100, progress, 1.8, TEXT_WHITE)
        
        # Subtitle
        if progress > 0.5:
            sub_prog = (progress - 0.5) * 2
            fade_in_text(img, "REA MCP Integration for DeepSeek Harness", 
                         "DeepSeek Harness 的 REA MCP 集成插件",
                         HEIGHT // 2 + 150, HEIGHT // 2 + 190, sub_prog, 0.8, TEXT_GRAY)
        
        writer.write(img)

def scene_unofficial(writer, start_frame, end_frame):
    """Scene 2: Unofficial / Packaging Layer disclaimer"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        # Badge
        badge_text_en = "UNOFFICIAL"
        badge_text_zh = "非官方项目"
        (bw, bh), _ = cv2.getTextSize(badge_text_en, FONT_BOLD, 1.5, 3)
        bx = (WIDTH - bw) // 2
        by = HEIGHT // 2 - 80
        
        # Pulsing badge background
        pulse = 0.8 + 0.2 * np.sin(i * 0.2)
        badge_color = (0, int(180 * pulse), int(216 * pulse))
        cv2.rectangle(img, (bx - 20, by - bh - 10), (bx + bw + 20, by + 10), badge_color, -1, cv2.LINE_AA)
        draw_text(img, badge_text_en, (bx, by), 1.5, (255, 255, 255), 3, FONT_BOLD)
        
        fade_in_text(img, "Packaging Layer Only", "仅做打包与接入层",
                     HEIGHT // 2 + 20, HEIGHT // 2 + 70, progress, 1.0, TEXT_WHITE)
        
        if progress > 0.4:
            sub_prog = (progress - 0.4) / 0.6
            fade_in_text(img, "No REA source code included", "不包含 REA 源码",
                         HEIGHT // 2 + 120, HEIGHT // 2 + 160, sub_prog, 0.8, TEXT_GRAY)
            fade_in_text(img, "Official rea-agents fetched from npm at runtime", "运行时从 npm 拉取官方 rea-agents",
                         HEIGHT // 2 + 200, HEIGHT // 2 + 240, sub_prog, 0.8, TEXT_GRAY)
        
        writer.write(img)

def scene_config_only(writer, start_frame, end_frame):
    """Scene 3: Configuration-only bundle"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        slide_in_text(img, "Configuration-Only Bundle", "纯配置插件",
                      HEIGHT // 2 - 80, HEIGHT // 2 - 20, progress, 1.3, TEXT_WHITE)
        
        if progress > 0.3:
            sub_prog = (progress - 0.3) / 0.7
            # YAML snippet visualization
            yaml_lines_en = [
                "- insert:",
                "    - id: rea-mcp",
                "      name: '@deepseek-ai/dsh-mcp-client'",
                "      config:",
                "        command: npx",
                "        args: ['-y', 'rea-agents@6.7.0', 'mcp']"
            ]
            yaml_lines_zh = [
                "插入一行配置：",
                "  id: rea-mcp",
                "  使用官方 MCP Client",
                "  运行时拉取 rea-agents",
                "  通过 npx 启动 MCP 服务器"
            ]
            
            start_y = HEIGHT // 2 + 30
            for idx, (en, zh) in enumerate(zip(yaml_lines_en, yaml_lines_zh)):
                line_prog = max(0, min(1, (sub_prog - idx * 0.1) * 3))
                if line_prog > 0:
                    alpha = line_prog
                    color_en = tuple(int(c * alpha) for c in (180, 200, 220))
                    color_zh = tuple(int(c * alpha) for c in TEXT_GRAY)
                    draw_text(img, en, (80, start_y + idx * 35), 0.55, color_en, 1)
                    draw_text(img, zh, (80, start_y + idx * 35 + 20), 0.5, color_zh, 1)
        
        writer.write(img)

def scene_npm_runtime(writer, start_frame, end_frame):
    """Scene 4: npm runtime fetch"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        slide_in_text(img, "npm Runtime Fetch", "npm 运行时拉取",
                      HEIGHT // 2 - 100, HEIGHT // 2 - 40, progress, 1.3, TEXT_WHITE)
        
        if progress > 0.2:
            sub_prog = (progress - 0.2) / 0.8
            
            # Animated download arrow
            cx, cy = WIDTH // 2, HEIGHT // 2 + 50
            arrow_progress = min(progress * 2, 1.0)
            arrow_y = cy + int((1 - arrow_progress) * 60)
            
            # Down arrow
            cv2.arrowedLine(img, (cx, arrow_y - 40), (cx, arrow_y + 20), ACCENT, 4, cv2.LINE_AA, tipLength=0.3)
            
            fade_in_text(img, "npx -y rea-agents@6.7.0 mcp", "首次启动自动下载官方包",
                         HEIGHT // 2 + 120, HEIGHT // 2 + 160, sub_prog, 0.8, TEXT_GRAY)
            fade_in_text(img, "Zero vendoring \u00b7 Zero forking \u00b7 Zero rebuilding", "零复制 \u00b7 零分叉 \u00b7 零重构",
                         HEIGHT // 2 + 210, HEIGHT // 2 + 250, max(0, sub_prog - 0.2) * 1.25, 0.7, HIGHLIGHT)
        
        writer.write(img)

def scene_207_tools(writer, start_frame, end_frame):
    """Scene 5: 207 REA tools connected"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        # Big number
        num = "207"
        (nw, nh), _ = cv2.getTextSize(num, FONT_BOLD, 6, 6)
        nx = (WIDTH - nw) // 2
        ny = HEIGHT // 2 - 20
        
        # Pulse the number
        pulse = 0.5 + 0.5 * ease_in_out(progress)
        num_color = tuple(int(ACCENT[i] * pulse) for i in range(3))
        draw_text(img, num, (nx, ny), 6, num_color, 6, FONT_BOLD)
        
        slide_in_text(img, "REA Tools Connected", "REA 工具接入 DSH",
                      HEIGHT // 2 + 80, HEIGHT // 2 + 140, progress, 1.2, TEXT_WHITE)
        
        if progress > 0.4:
            sub_prog = (progress - 0.4) / 0.6
            fade_in_text(img, "mcp__rea__* namespace", "mcp__rea__* 命名空间",
                         HEIGHT // 2 + 190, HEIGHT // 2 + 230, sub_prog, 0.8, TEXT_GRAY)
            fade_in_text(img, "Binary \u00b7 App \u00b7 JS/Electron \u00b7 Managed \u00b7 Web \u00b7 Firmware", 
                         "二进制 \u00b7 应用包 \u00b7 JS/Electron \u00b7 托管程序 \u00b7 网页 \u00b7 固件",
                         HEIGHT // 2 + 260, HEIGHT // 2 + 300, max(0, sub_prog - 0.2) * 1.25, 0.7, TEXT_GRAY)
        
        writer.write(img)

def scene_tool_categories(writer, start_frame, end_frame):
    """Scene 6: Tool categories quick flash"""
    frames = end_frame - start_frame
    categories = [
        ("inspect_*", "\u68c0\u67e5\u5de5\u5177"),
        ("analyze_*", "\u5206\u6790\u5de5\u5177"),
        ("trace_*", "\u8ffd\u8e2a\u5de5\u5177"),
        ("compare_*", "\u5bf9\u6bd4\u5de5\u5177"),
        ("capture_*", "\u6355\u83b7\u5de5\u5177"),
        ("observe_*", "\u89c2\u5bdf\u5de5\u5177"),
        ("project_*", "\u6295\u5f71\u5de5\u5177"),
        ("verify_*", "\u9a8c\u8bc1\u5de5\u5177"),
    ]
    
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        cat_idx = int(progress * len(categories)) % len(categories)
        cat_en, cat_zh = categories[cat_idx]
        
        # Category name pulsing
        pulse_text(img, cat_en, cat_zh, HEIGHT // 2 - 30, HEIGHT // 2 + 30, i, 1.5, HIGHLIGHT)
        
        # Subtitle
        fade_in_text(img, "207 tools across 8 categories", "8 大类 207 个工具",
                     HEIGHT // 2 + 120, HEIGHT // 2 + 160, 1.0, 0.8, TEXT_GRAY)
        
        writer.write(img)

def scene_verified(writer, start_frame, end_frame):
    """Scene 7: Verified on macOS, Linux untested Windows"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        slide_in_text(img, "Verified on macOS", "\u5df2\u5728 macOS \u9a8c\u8bc1",
                      HEIGHT // 2 - 100, HEIGHT // 2 - 40, progress, 1.2, TEXT_WHITE)
        
        if progress > 0.3:
            sub_prog = (progress - 0.3) / 0.7
            
            # Platform badges
            platforms = [
                ("\u2713 macOS", "\u2713 macOS", ACCENT),
                ("\u2713 Linux (expected)", "\u2713 Linux (\u9884\u671f\u76f8\u540c)", TEXT_GRAY),
                ("? Windows (untested)", "? Windows (\u672a\u9a8c\u8bc1)", TEXT_DIM),
            ]
            
            for idx, (en, zh, color) in enumerate(platforms):
                line_prog = max(0, min(1, (sub_prog - idx * 0.2) * 2))
                if line_prog > 0:
                    alpha = line_prog
                    c = tuple(int(color[j] * alpha) for j in range(3))
                    y_pos = HEIGHT // 2 + 30 + idx * 60
                    draw_text_centered(img, en, y_pos, 0.9, c, 2)
                    draw_text_centered(img, zh, y_pos + 30, 0.8, c, 2)
        
        writer.write(img)

def scene_install(writer, start_frame, end_frame):
    """Scene 8: Install command"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        slide_in_text(img, "Install", "\u5b89\u88c5",
                      HEIGHT // 2 - 120, HEIGHT // 2 - 60, progress, 1.5, TEXT_WHITE)
        
        if progress > 0.3:
            sub_prog = (progress - 0.3) / 0.7
            
            # Command box
            box_x, box_y = 150, HEIGHT // 2 - 10
            box_w, box_h = WIDTH - 300, 140
            cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (40, 45, 55), -1, cv2.LINE_AA)
            cv2.rectangle(img, (box_x, box_y), (box_x + box_w, box_y + box_h), (80, 80, 80), 2, cv2.LINE_AA)
            
            cmds = [
                ("git clone https://github.com/sqhc/dsh-rea", "\u5147\u4e32\u4ed3\u5e93"),
                ("# In Harness: plugin_manager install_bundle /path/to/dsh-rea", "# \u5728 Harness \u4e2d\u5b89\u88c5\u63d2\u4ef6"),
                ("node scripts/preflight.mjs  # Optional preflight", "node scripts/preflight.mjs  # \u53ef\u9009\u81ea\u68c0"),
            ]
            
            for idx, (en, zh) in enumerate(cmds):
                line_prog = max(0, min(1, (sub_prog - idx * 0.25) * 2.5))
                if line_prog > 0:
                    alpha = line_prog
                    c_en = (int(180 * alpha), int(210 * alpha), int(180 * alpha))
                    c_zh = tuple(int(TEXT_GRAY[j] * alpha) for j in range(3))
                    draw_text(img, "$ " + en, (box_x + 20, box_y + 35 + idx * 40), 0.55, c_en, 1)
                    draw_text(img, "  # " + zh, (box_x + 20, box_y + 55 + idx * 40), 0.45, c_zh, 1)
        
        writer.write(img)

def scene_verify(writer, start_frame, end_frame):
    """Scene 9: Verify with binary_session"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        slide_in_text(img, "Verify", "\u9a8c\u8bc1",
                      HEIGHT // 2 - 100, HEIGHT // 2 - 40, progress, 1.5, TEXT_WHITE)
        
        if progress > 0.3:
            sub_prog = (progress - 0.3) / 0.7
            
            fade_in_text(img, "Ask agent: mcp__rea__binary_session()", "\u8ba9\u667a\u80fd\u4f53\u8c03\u7528: mcp__rea__binary_session()",
                         HEIGHT // 2 + 20, HEIGHT // 2 + 60, sub_prog, 0.8, TEXT_GRAY)
            
            # Expected output
            box_y = HEIGHT // 2 + 120
            box_h = 100
            cv2.rectangle(img, (150, box_y), (WIDTH - 150, box_y + box_h), (30, 35, 45), -1, cv2.LINE_AA)
            cv2.rectangle(img, (150, box_y), (WIDTH - 150, box_y + box_h), (70, 70, 70), 1, cv2.LINE_AA)
            
            out_lines = [
                ("{ server: 'rea', version: '6.7.0', ... }", "{ server: 'rea', version: '6.7.0', ... }")
            ]
            for idx, (en, zh) in enumerate(out_lines):
                line_prog = max(0, min(1, (sub_prog - 0.3) * 2))
                if line_prog > 0:
                    alpha = line_prog
                    c = tuple(int(HIGHLIGHT[j] * alpha) for j in range(3))
                    draw_text(img, "> " + en, (170, box_y + 35 + idx * 30), 0.5, c, 1)
                    draw_text(img, "  # " + zh, (170, box_y + 55 + idx * 30), 0.45, tuple(int(TEXT_GRAY[j] * alpha) for j in range(3)), 1)
        
        writer.write(img)

def scene_outro(writer, start_frame, end_frame):
    """Scene 10: Outro with repo link"""
    frames = end_frame - start_frame
    for i in range(frames):
        img = make_frame_blank()
        add_gradient_bg(img)
        
        progress = i / frames
        
        # Icon
        draw_icon_area(img, WIDTH // 2, HEIGHT // 2 - 120, 60, progress)
        
        # Repo
        slide_in_text(img, "github.com/sqhc/dsh-rea", "github.com/sqhc/dsh-rea",
                      HEIGHT // 2, HEIGHT // 2 + 50, progress, 1.0, ACCENT)
        
        if progress > 0.5:
            sub_prog = (progress - 0.5) * 2
            fade_in_text(img, "MIT Licensed \u00b7 Unofficial Integration", "MIT \u8bb8\u53ef \u00b7 \u975e\u5b98\u65b9\u96c6\u6210",
                         HEIGHT // 2 + 120, HEIGHT // 2 + 160, sub_prog, 0.7, TEXT_DIM)
        
        writer.write(img)

# ==================== MAIN ====================

def main():
    output_path = str(Path(__file__).resolve().parent / "promo.mp4")
    
    # Try H264 first, fallback to MP4V
    fourcc = cv2.VideoWriter_fourcc(*'avc1')
    writer = cv2.VideoWriter(output_path, fourcc, FPS, (WIDTH, HEIGHT))
    
    if not writer.isOpened():
        print("H264 not available, trying MP4V...")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(output_path, fourcc, FPS, (WIDTH, HEIGHT))
    
    if not writer.isOpened():
        print("ERROR: Could not open video writer")
        return
    
    print(f"Generating video: {WIDTH}x{HEIGHT} @ {FPS}fps, {DURATION_SEC}s")
    print(f"Total frames: {TOTAL_FRAMES}")
    
    # Scene timings (in frames)
    scenes = [
        (scene_title, 0, 120),           # 4s
        (scene_unofficial, 120, 210),    # 3s
        (scene_config_only, 210, 330),   # 4s
        (scene_npm_runtime, 330, 450),   # 4s
        (scene_207_tools, 450, 570),     # 4s
        (scene_tool_categories, 570, 690), # 4s
        (scene_verified, 690, 810),      # 4s
        (scene_install, 810, 960),       # 5s
        (scene_verify, 960, 1080),       # 4s
        (scene_outro, 1080, 1200),       # 4s
    ]
    
    # Verify total frames
    total = sum(end - start for _, start, end in scenes)
    print(f"Scene frames total: {total} (target: {TOTAL_FRAMES})")
    
    frame_count = 0
    for scene_func, start_f, end_f in scenes:
        print(f"  Rendering {scene_func.__name__}: frames {start_f}-{end_f} ({end_f-start_f} frames)")
        scene_func(writer, start_f, end_f)
        frame_count += end_f - start_f
    
    writer.release()
    print(f"Done! Written {frame_count} frames to {output_path}")
    
    # Get file size
    size = os.path.getsize(output_path)
    print(f"File size: {size / 1024:.1f} KB")

if __name__ == "__main__":
    main()