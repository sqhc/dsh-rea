#!/usr/bin/env python3
"""
Create dsh-rea promotional video using OpenCV for text rendering
(avoids ffmpeg drawtext limitation)
Outputs: promo.mp4, promo.webm, promo.gif
"""

import cv2
import numpy as np
import subprocess
import os
from pathlib import Path

# Video settings
WIDTH = 1280
HEIGHT = 720
FPS = 30
DURATION = 60  # seconds
TOTAL_FRAMES = FPS * DURATION

# Colors (BGR)
BG_DARK = (18, 18, 24)
BG_CARD = (30, 30, 40)
ACCENT_BLUE = (100, 200, 255)
ACCENT_GREEN = (80, 255, 120)
ACCENT_ORANGE = (40, 180, 255)
TEXT_WHITE = (240, 240, 240)
TEXT_GRAY = (160, 160, 170)
TEXT_DIM = (100, 100, 110)

# Fonts
FONT = cv2.FONT_HERSHEY_SIMPLEX
FONT_MONO = cv2.FONT_HERSHEY_DUPLEX

def put_text(img, text, pos, font_scale, color, thickness=1, font=FONT, center=False):
    """Draw text with optional centering"""
    (tw, th), _ = cv2.getTextSize(text, font, font_scale, thickness)
    x, y = pos
    if center:
        x = x - tw // 2
    cv2.putText(img, text, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
    return tw, th

def put_text_multiline(img, lines, start_pos, font_scale, color, line_spacing=1.4, thickness=1, font=FONT, center_x=False):
    """Draw multiple lines of text"""
    x, y = start_pos
    for line in lines:
        (tw, th), _ = cv2.getTextSize(line, font, font_scale, thickness)
        if center_x:
            x = (WIDTH - tw) // 2
        cv2.putText(img, line, (x, y), font, font_scale, color, thickness, cv2.LINE_AA)
        y += int(th * line_spacing)
    return y

def draw_card(img, rect, color, radius=12):
    """Draw rounded rectangle card"""
    x, y, w, h = rect
    overlay = img.copy()
    cv2.rectangle(overlay, (x, y), (x + w, y + h), color, -1)
    # Simple rounded corners via mask
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.rectangle(mask, (radius, 0), (w - radius, h), 255, -1)
    cv2.rectangle(mask, (0, radius), (w, h - radius), 255, -1)
    cv2.circle(mask, (radius, radius), radius, 255, -1)
    cv2.circle(mask, (w - radius, radius), radius, 255, -1)
    cv2.circle(mask, (radius, h - radius), radius, 255, -1)
    cv2.circle(mask, (w - radius, h - radius), radius, 255, -1)
    for c in range(3):
        img[y:y+h, x:x+w, c] = np.where(mask == 255, color[c], img[y:y+h, x:x+w, c])

def ease_in_out(t):
    """Smooth easing"""
    return t * t * (3 - 2 * t)

def ease_out(t):
    return 1 - (1 - t) ** 3

def render_frame(frame_idx):
    """Render a single frame based on timeline"""
    t = frame_idx / FPS
    progress = frame_idx / TOTAL_FRAMES
    
    img = np.full((HEIGHT, WIDTH, 3), BG_DARK, dtype=np.uint8)
    
    # ===== SECTION 1: Logo + Title (0-3s) =====
    if t < 3:
        p = ease_out(t / 3)
        # Icon placeholder (animated scale)
        icon_size = max(10, int(120 * p))
        cx, cy = WIDTH // 2, HEIGHT // 2 - 60
        cv2.circle(img, (cx, cy), icon_size, ACCENT_BLUE, -1)
        if icon_size > 10:
            cv2.circle(img, (cx, cy), icon_size - 8, BG_DARK, -1)
        # "REA" in center
        put_text(img, "REA", (cx - 35, cy + 15), 1.5, ACCENT_BLUE, 3, center=True)
        
        # Title fade in
        if t > 1:
            title_p = ease_out((t - 1) / 2)
            alpha = title_p
            title_y = HEIGHT // 2 + 80
            # dsh-rea
            put_text(img, "dsh-rea", (WIDTH // 2, title_y), 2.0, TEXT_WHITE, 3, center=True)
    
    # ===== SECTION 2: Core positioning (3-8s) =====
    elif t < 8:
        p = ease_in_out((t - 3) / 5)
        
        # "Unofficial / packaging layer only" - BIG
        y_start = HEIGHT // 2 - 60
        put_text(img, "Unofficial", (WIDTH // 2, y_start), 1.8, ACCENT_ORANGE, 3, center=True)
        put_text(img, "packaging layer only", (WIDTH // 2, y_start + 70), 1.3, TEXT_WHITE, 2, center=True)
        
        # Subtitle
        put_text(img, "No REA source code · npm pulls official package at runtime",
                 (WIDTH // 2, y_start + 140), 0.8, TEXT_GRAY, 1, center=True)
    
    # ===== SECTION 3: Install flow (8-18s) =====
    elif t < 18:
        p = (t - 8) / 10
        
        # Terminal-like animation
        put_text(img, "Installation", (80, 60), 1.2, ACCENT_BLUE, 2)
        
        commands = [
            "$ git clone https://github.com/sqhc/dsh-rea",
            "$ cd dsh-rea",
            "$ # In DSH agent:",
            "> plugin_manager install_bundle /path/to/dsh-rea",
        ]
        
        # Animate lines appearing
        lines_to_show = int(p * len(commands)) + 1
        for i, cmd in enumerate(commands[:lines_to_show]):
            color = ACCENT_GREEN if cmd.startswith("$") or cmd.startswith(">") else TEXT_WHITE
            y = 140 + i * 55
            # Prompt indicator
            if cmd.startswith("$"):
                put_text(img, "▶", (80, y), 0.9, ACCENT_GREEN, 2)
                put_text(img, cmd[2:], (110, y), 0.7, color, 1, FONT_MONO)
            elif cmd.startswith(">"):
                put_text(img, "▶", (80, y), 0.9, ACCENT_BLUE, 2)
                put_text(img, cmd[2:], (110, y), 0.7, color, 1, FONT_MONO)
            else:
                put_text(img, cmd, (80, y), 0.7, color, 1, FONT_MONO)
        
        # Success indicator
        if p > 0.8:
            put_text(img, "✓ Bundle installed & persisted across restarts",
                     (80, 140 + len(commands) * 55 + 30), 0.7, ACCENT_GREEN, 1)
    
    # ===== SECTION 4: Architecture - npm pulls REA (18-28s) =====
    elif t < 28:
        p = (t - 18) / 10
        
        put_text(img, "How it works", (80, 60), 1.2, ACCENT_BLUE, 2)
        
        # Flow diagram: npm → npx → REA MCP → DSH
        boxes = [
            ("npm", "rea-agents@6.7.0", ACCENT_BLUE),
            ("npx", "runs as stdio MCP server", ACCENT_GREEN),
            ("REA MCP", "207 tools exposed", ACCENT_ORANGE),
            ("DSH", "mcp__rea__<tool>", (255, 150, 100)),
        ]
        
        box_w = 260
        box_h = 100
        spacing = 40
        total_w = len(boxes) * box_w + (len(boxes) - 1) * spacing
        start_x = (WIDTH - total_w) // 2
        y = HEIGHT // 2 - 40
        
        for i, (title, desc, color) in enumerate(boxes):
            # Animate appearance
            box_p = max(0, min(1, (p - i * 0.2) / 0.3))
            if box_p <= 0:
                continue
            
            x = start_x + i * (box_w + spacing)
            alpha = box_p
            
            # Card
            card_color = tuple(int(c * 0.3 + BG_CARD[j] * 0.7) for j, c in enumerate(color))
            draw_card(img, (x, y, box_w, box_h), card_color)
            
            # Border
            cv2.rectangle(img, (x, y), (x + box_w, y + box_h), color, 2)
            
            # Title
            put_text(img, title, (x + box_w // 2, y + 35), 0.9, color, 2, center=True)
            # Description
            put_text(img, desc, (x + box_w // 2, y + 70), 0.55, TEXT_WHITE, 1, center=True)
            
            # Arrow to next
            if i < len(boxes) - 1 and box_p > 0.5:
                arrow_x = x + box_w + spacing // 2
                arrow_y = y + box_h // 2
                cv2.arrowedLine(img, (x + box_w, arrow_y), (x + box_w + spacing, arrow_y), 
                               TEXT_GRAY, 2, tipLength=0.3)
        
        # Key point at bottom
        if p > 0.6:
            put_text(img, "Zero REA source code in this repo · Official package fetched at runtime",
                     (WIDTH // 2, HEIGHT - 80), 0.7, ACCENT_GREEN, 1, center=True)
    
    # ===== SECTION 5: 207 tools demo (28-42s) =====
    elif t < 42:
        p = (t - 28) / 14
        
        put_text(img, "207 REA Tools → mcp__rea__*", (80, 60), 1.2, ACCENT_ORANGE, 2)
        
        # Preflight output simulation
        preflight_lines = [
            "node 24.21.0: supported",
            "npm cache /tmp/dsh-rea-npm-cache: writable",
            "REA 6.7.0: handshake ok",
            "  tools: 207",
            "  catalog: 214.1 KiB (~55k tokens)",
            "  largest: inspect_analysis_view (7.4 KB)",
            "OK",
        ]
        
        # Terminal background
        term_x, term_y = 80, 110
        term_w, term_h = 1120, 450
        draw_card(img, (term_x, term_y, term_w, term_h), BG_CARD)
        cv2.rectangle(img, (term_x, term_y), (term_x + term_w, term_y + term_h), (60, 60, 80), 1)
        
        # Animate lines
        lines_to_show = min(len(preflight_lines), int(p * len(preflight_lines) * 1.5) + 1)
        for i, line in enumerate(preflight_lines[:lines_to_show]):
            y = term_y + 35 + i * 40
            color = ACCENT_GREEN if "OK" in line or "supported" in line or "writable" in line else TEXT_WHITE
            if "tools:" in line:
                color = ACCENT_ORANGE
            put_text(img, line, (term_x + 20, y), 0.65, color, 1, FONT_MONO)
        
        # Tool examples scrolling
        if p > 0.5:
            tool_examples = [
                "mcp__rea__binary_session",
                "mcp__rea__analyze_function",
                "mcp__rea__inspect_artifact",
                "mcp__rea__inspect_web_page",
                "mcp__rea__capture_browser_scenario",
                "mcp__rea__trace_call_path",
                "mcp__rea__inspect_managed_members",
                "mcp__rea__inspect_wasm_artifact",
                "mcp__rea__trace_native_values",
                "... and 197 more",
            ]
            ex_y = term_y + term_h + 20
            put_text(img, "Example tools:", (term_x, ex_y), 0.7, TEXT_GRAY, 1)
            for i, tool in enumerate(tool_examples):
                tx = term_x + 20 + (i % 3) * 380
                ty = ex_y + 30 + (i // 3) * 28
                put_text(img, tool, (tx, ty), 0.55, ACCENT_BLUE, 1, FONT_MONO)
    
    # ===== SECTION 6: Live verification (42-52s) =====
    elif t < 52:
        p = (t - 42) / 10
        
        put_text(img, "Verify: mcp__rea__binary_session", (80, 60), 1.2, ACCENT_BLUE, 2)
        
        # Simulated DSH tool call result
        result_json = """{
  "serverVersion": "6.7.0",
  "provider": "ghidra",
  "capabilities": ["tools", "resources"],
  "toolsCount": 207
}"""
        
        # Terminal
        term_x, term_y = 80, 110
        term_w, term_h = 1120, 400
        draw_card(img, (term_x, term_y, term_w, term_h), BG_CARD)
        cv2.rectangle(img, (term_x, term_y), (term_x + term_w, term_y + term_h), (60, 60, 80), 1)
        
        # Command
        put_text(img, "> mcp__rea__binary_session {}", (term_x + 20, term_y + 40), 0.65, ACCENT_GREEN, 1, FONT_MONO)
        
        # Result (animated)
        if p > 0.3:
            lines = result_json.strip().split('\n')
            lines_to_show = min(len(lines), int((p - 0.3) / 0.7 * len(lines)) + 1)
            for i, line in enumerate(lines[:lines_to_show]):
                y = term_y + 90 + i * 35
                put_text(img, line, (term_x + 20, y), 0.6, TEXT_WHITE, 1, FONT_MONO)
        
        # Checkmark
        if p > 0.8:
            put_text(img, "✓ REA 6.7.0 connected · 207 tools ready", 
                     (term_x + 20, term_y + term_h + 40), 0.7, ACCENT_GREEN, 1)
    
    # ===== SECTION 7: Config & compatibility (52-57s) =====
    elif t < 57:
        p = (t - 52) / 5
        
        put_text(img, "Configure via cordis.patch.yml", (80, 60), 1.1, ACCENT_BLUE, 2)
        
        config_items = [
            ("Version pin", "rea-agents@6.7.0", "Change to upgrade"),
            ("Node.js", "22.x / 24.x / 26+", "REA official support"),
            ("Schema profile", "compact (214 KiB)", "full = 3.4 MB"),
            ("Timeout", "600s", "Native analysis needs time"),
        ]
        
        for i, (key, val, note) in enumerate(config_items):
            y = 130 + i * 70
            row_p = max(0, min(1, (p - i * 0.15) / 0.3))
            if row_p <= 0:
                continue
            
            # Key
            put_text(img, key, (100, y), 0.7, TEXT_GRAY, 1)
            # Value
            put_text(img, val, (320, y), 0.7, TEXT_WHITE, 1, FONT_MONO)
            # Note
            put_text(img, note, (650, y), 0.55, TEXT_DIM, 1)
        
        if p > 0.8:
            put_text(img, "Edit cordis.patch.yml → reinstall bundle → run preflight",
                     (WIDTH // 2, HEIGHT - 80), 0.7, ACCENT_GREEN, 1, center=True)
    
    # ===== SECTION 8: Outro (57-60s) =====
    else:
        p = (t - 57) / 3
        
        # GitHub link
        put_text(img, "github.com/sqhc/dsh-rea", (WIDTH // 2, HEIGHT // 2 - 40), 1.2, ACCENT_BLUE, 2, center=True)
        put_text(img, "MIT Licensed · Unofficial integration", (WIDTH // 2, HEIGHT // 2 + 30), 0.8, TEXT_GRAY, 1, center=True)
        
        # Fade out
        if p > 0.7:
            fade = 1 - (p - 0.7) / 0.3
            overlay = np.full((HEIGHT, WIDTH, 3), BG_DARK, dtype=np.uint8)
            img = cv2.addWeighted(img, fade, overlay, 1 - fade, 0)
    
    return img

def create_video():
    """Generate video frames and encode"""
    output_dir = Path("/Users/shenqing/Desktop/Deepseek Harness/dsh-rea")
    mp4_path = output_dir / "promo.mp4"
    webm_path = output_dir / "promo.webm"
    gif_path = output_dir / "promo.gif"
    
    print(f"Generating {TOTAL_FRAMES} frames at {FPS}fps...")
    
    # Use OpenCV to write MP4 first
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(str(mp4_path), fourcc, FPS, (WIDTH, HEIGHT))
    
    for i in range(TOTAL_FRAMES):
        frame = render_frame(i)
        writer.write(frame)
        if i % 300 == 0:
            print(f"  Frame {i}/{TOTAL_FRAMES} ({i/FPS:.1f}s)")
    
    writer.release()
    print(f"MP4 written: {mp4_path}")
    
    # Convert to WebM using ffmpeg
    print("Converting to WebM...")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(mp4_path),
        "-c:v", "libvpx-vp9", "-b:v", "1.5M",
        "-deadline", "good", "-cpu-used", "2",
        str(webm_path)
    ], check=True)
    print(f"WebM written: {webm_path}")
    
    # Create GIF (downsampled, 10fps)
    print("Creating GIF...")
    gif_frames = []
    for i in range(0, TOTAL_FRAMES, 3):  # 10fps
        frame = render_frame(i)
        # Resize to 640x360 for GIF
        small = cv2.resize(frame, (640, 360))
        gif_frames.append(small)
    
    # Save as GIF using OpenCV (limited) or PIL
    try:
        from PIL import Image
        pil_frames = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in gif_frames]
        pil_frames[0].save(
            str(gif_path),
            save_all=True,
            append_images=pil_frames[1:],
            duration=100,  # 10fps = 100ms per frame
            loop=0,
            optimize=True
        )
        print(f"GIF written: {gif_path} ({len(pil_frames)} frames)")
    except Exception as e:
        print(f"GIF creation failed: {e}")
    
    # Poster frame (first frame)
    poster_path = output_dir / "promo-poster.png"
    first_frame = render_frame(0)
    cv2.imwrite(str(poster_path), first_frame)
    print(f"Poster written: {poster_path}")
    
    # File sizes
    for p in [mp4_path, webm_path, gif_path, poster_path]:
        if p.exists():
            size = p.stat().st_size
            print(f"  {p.name}: {size/1024:.1f} KB")

if __name__ == "__main__":
    create_video()