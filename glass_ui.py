# -*- coding: utf-8 -*-
"""
glass_ui — iOS 风格毛玻璃 tkinter 窗口基类。

提供：无边框圆角窗口、透明色键、玻璃覆盖层预渲染、
canvas 自绘圆角按钮（6 种样式）、自定义标题栏（拖动/最大化/最小化/关闭）、
ttk clam 主题配色、背景图渲染（静态图片 + 动态视频）。

所有控件用 canvas + PIL ImageDraw 自绘，不依赖 ttk 原生渲染。
"""

import ctypes
import os
import sys
import queue
import threading
import subprocess

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk, ImageDraw, ImageChops


# ---------------------------------------------------------------- 视频背景播放器

class VideoBackgroundPlayer:
    """用 ffmpeg 子进程从视频文件读取 RGBA 帧，线程安全队列供主线程消费。"""

    def __init__(self, video_path, width, height, fps=30, ffmpeg_exe="ffmpeg"):
        self.path = video_path
        self.w = max(2, width)
        self.h = max(2, height)
        self.fps = fps
        self.ffmpeg = ffmpeg_exe
        self._proc = None
        self._thread = None
        self._queue = queue.Queue(maxsize=3)
        self._stop = threading.Event()

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._proc:
            try:
                self._proc.kill()
            except Exception:
                pass
            self._proc = None
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass

    def get_frame(self):
        """非阻塞取一帧 PIL.Image，无可用帧返回 None。"""
        try:
            return self._queue.get_nowait()
        except queue.Empty:
            return None

    def _read_loop(self):
        vf = (f"scale={self.w}:{self.h}:force_original_aspect_ratio=increase,"
              f"crop={self.w}:{self.h}")
        while not self._stop.is_set():
            try:
                self._proc = subprocess.Popen(
                    [self.ffmpeg, "-i", self.path,
                     "-vf", vf, "-pix_fmt", "rgba",
                     "-r", str(self.fps), "-f", "rawvideo", "-"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    creationflags=0x08000000)  # CREATE_NO_WINDOW
            except Exception:
                return
            frame_size = self.w * self.h * 4
            while not self._stop.is_set():
                raw = self._proc.stdout.read(frame_size)
                if len(raw) < frame_size:
                    break  # 视频结束，外层循环重新启动实现循环播放
                if self._stop.is_set():
                    break
                img = Image.frombytes("RGBA", (self.w, self.h), raw)
                try:
                    self._queue.put(img, timeout=0.5)
                except queue.Full:
                    try:
                        self._queue.get_nowait()
                    except queue.Empty:
                        pass
                    try:
                        self._queue.put(img, timeout=0.5)
                    except queue.Full:
                        pass
            if self._proc:
                try:
                    self._proc.kill()
                except Exception:
                    pass
                self._proc = None


def find_ffmpeg_dir():
    """依次在打包资源、程序目录、bin 子目录里寻找 ffmpeg.exe。"""
    candidates = [
        bundle_dir(),
        app_dir(),
        os.path.join(app_dir(), "bin"),
        os.path.join(bundle_dir(), "bin"),
    ]
    for d in candidates:
        if d and os.path.isfile(os.path.join(d, "ffmpeg.exe")):
            return d
    return None


def app_dir():
    """程序所在目录（打包后是 exe 所在目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir():
    """PyInstaller onefile 解包目录。"""
    return getattr(sys, "_MEIPASS", app_dir())


# ---------------------------------------------------------------- 玻璃窗口基类

class GlassWindow(tk.Tk):
    """iOS 玻璃风无边框窗口基类。子类实现 _build_ui()。"""

    # ---- 布局常量 ----
    TITLE_H = 48
    WIN_RADIUS = 24
    PADDING = 12
    LEFT_W = 156
    PANEL_RADIUS = 26

    # ---- 透明色键 ----
    TRANS_KEY = "#ff00fe"

    # ---- iOS 玻璃配色 ----
    GLASS_FILL = (255, 255, 255, 148)
    GLASS_EDGE = (255, 255, 255, 120)
    TEXT_DARK = "#1d2230"
    TEXT_GREY = "#5c6478"
    FIELD_BG = "#ffffff"
    FIELD_BD = "#d3d8e2"
    GLASS_BG = "#eef1f7"
    IOS_BLUE = "#0a84ff"
    IOS_PINK = "#ff375f"

    # ---- 按钮配色 ----
    BTN_STYLES = {
        "blue":   ((10, 132, 255, 255),  "#ffffff", None),
        "gray":   ((228, 231, 237, 235), TEXT_DARK, None),
        "glass":  ((255, 255, 255, 150), TEXT_DARK, (255, 255, 255, 200)),
        "ghost":  ((255, 255, 255, 60),  TEXT_DARK, (255, 255, 255, 160)),
        "dark":   ((18, 20, 28, 150),    "#ffffff", (255, 255, 255, 70)),
        "pink":   ((255, 55, 95, 235),   "#ffffff", None),
    }

    def __init__(self):
        super().__init__()
        self._btn_imgs = {}
        self._bg_photo = None
        self._glass_photo = None
        self._glass_overlay = None
        self._glass_rgb = None
        self._glass_alpha = None
        self._corner_mask = None
        self._maximized = False
        self._saved_geom = None
        self._win_mode = None
        self._drag_start = None
        self.widgets = {}

        # 视频背景
        self._video_player = None
        self._video_after = None
        self._video_mode = False
        self.ffmpeg_dir = find_ffmpeg_dir()

        self.configure(bg=self.TRANS_KEY)
        self.bg_canvas = tk.Canvas(self, highlightthickness=0,
                                   bd=0, bg=self.TRANS_KEY)
        self.bg_canvas.pack(fill="both", expand=True)
        self.bg_canvas.bind("<Configure>", self._on_canvas_configure)
        self.bg_canvas.bind("<ButtonPress-1>", self._win_press)
        self.bg_canvas.bind("<B1-Motion>", self._win_drag)
        self.bg_canvas.bind("<ButtonRelease-1>", self._win_release)
        self.bg_canvas.bind("<Double-Button-1>", self._win_double)
        self.bg_canvas.bind("<Motion>", self._win_hover)

        self._setup_theme()
        self.after(60, self._enable_frameless)

    # ---------------------------------------------------------------- 主题

    def _setup_theme(self):
        s = ttk.Style(self)
        try:
            s.theme_use("clam")
        except tk.TclError:
            pass
        fg = self.TEXT_DARK
        field = self.FIELD_BG
        border = self.FIELD_BD
        s.configure(".", background=self.GLASS_BG, foreground=fg,
                    font=("Microsoft YaHei UI", 10))
        s.configure("TFrame", background=self.GLASS_BG)
        s.configure("TLabel", background=self.GLASS_BG, foreground=fg)
        s.configure("TEntry", fieldbackground=field, foreground=fg,
                    insertcolor=fg, bordercolor=border,
                    lightcolor=border, darkcolor=border, padding=5)
        s.configure("TCombobox", fieldbackground=field, foreground=fg,
                    background=field, bordercolor=border,
                    lightcolor=border, darkcolor=border,
                    arrowcolor="#5c6478", padding=3)
        s.map("TCombobox",
              fieldbackground=[("readonly", field)],
              foreground=[("readonly", fg)],
              bordercolor=[("focus", self.IOS_BLUE)])
        self.option_add("*TCombobox*Listbox.background", field)
        self.option_add("*TCombobox*Listbox.foreground", fg)
        self.option_add("*TCombobox*Listbox.selectBackground", self.IOS_BLUE)
        self.option_add("*TCombobox*Listbox.selectForeground", "white")

    # ---------------------------------------------------------------- 无边框

    def _enable_frameless(self):
        try:
            self.overrideredirect(True)
            self.attributes("-transparentcolor", self.TRANS_KEY)
        except tk.TclError:
            return
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            cur = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            ctypes.windll.user32.SetWindowLongW(
                hwnd, GWL_EXSTYLE, cur | WS_EX_APPWINDOW)
            class _MARGINS(ctypes.Structure):
                _fields_ = [("cxLeftWidth", ctypes.c_int),
                            ("cxRightWidth", ctypes.c_int),
                            ("cyTopHeight", ctypes.c_int),
                            ("cyBottomHeight", ctypes.c_int)]
            m = _MARGINS(1, 1, 1, 1)
            try:
                ctypes.windll.dwmapi.DwmExtendFrameIntoClientArea(
                    hwnd, ctypes.byref(m))
            except Exception:
                pass
        except Exception:
            pass

    # ---------------------------------------------------------------- 背景

    def _on_canvas_configure(self, event):
        W, H = event.width, event.height
        if W < 2 or H < 2:
            return
        self._render_background(W, H)
        self._build_layout(W, H)

    def _render_background(self, W, H):
        """渲染背景：视频模式用两层 canvas，静态模式用单张合成图。"""
        p = self.PADDING
        lx, ly = p, self.TITLE_H + p
        lw, lh = self.LEFT_W, H - self.TITLE_H - 2 * p
        rw = W - self.LEFT_W - 3 * p
        rx, ry = self.LEFT_W + 2 * p, ly
        rh = lh

        # 玻璃覆盖层（视频和静态共用）
        self._glass_overlay = self._render_glass_overlay(
            W, H, lx, ly, lw, lh, rx, ry, rw, rh)

        from skin import current_skin_path, cover_image, is_video_path
        skin = current_skin_path()
        self._video_mode = skin is not None and is_video_path(skin)

        if self._video_mode and self.ffmpeg_dir:
            # 视频背景
            self._stop_video_bg()
            self._start_video_bg(skin, W, H)
        else:
            # 静态图片背景
            self._stop_video_bg()
            if skin and not is_video_path(skin):
                try:
                    img = cover_image(skin, W, H).convert("RGBA")
                except Exception:
                    img = self._make_default_bg(W, H)
            else:
                img = self._make_default_bg(W, H)
            img = Image.alpha_composite(img, self._glass_overlay)
            # 窗口圆角遮罩
            corner_mask = Image.new("L", (W, H), 0)
            ImageDraw.Draw(corner_mask).rounded_rectangle(
                [0, 0, W - 1, H - 1], radius=self.WIN_RADIUS, fill=255)
            img.putalpha(ImageChops.multiply(img.split()[3], corner_mask))
            self._bg_photo = ImageTk.PhotoImage(img)
            self.bg_canvas.delete("bg")
            self.bg_canvas.delete("bg_video")
            self.bg_canvas.delete("bg_overlay")
            self.bg_canvas.create_image(0, 0, anchor="nw",
                                        image=self._bg_photo, tags="bg")
            self.bg_canvas.tag_lower("bg")

    def _make_default_bg(self, W, H):
        """无皮肤时生成渐变背景。"""
        img = Image.new("RGB", (W, H))
        draw = ImageDraw.Draw(img)
        for y in range(H):
            t = y / max(1, H)
            r = int(30 + t * 35)
            g = int(35 + t * 25)
            b = int(55 + t * 50)
            draw.line([(0, y), (W, y)], fill=(r, g, b))
        return img.convert("RGBA")

    def _render_glass_overlay(self, W, H, lx, ly, lw, lh, rx, ry, rw, rh):
        """生成含玻璃面板 + 圆角遮罩的 RGBA 覆盖层。"""
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        radius = self.PANEL_RADIUS
        panels = [(lx, ly, lx + lw, ly + lh), (rx, ry, rx + rw, ry + rh)]
        for box in panels:
            od.rounded_rectangle(box, radius=radius, fill=self.GLASS_FILL)
            od.arc([box[0], box[1], box[0] + 2 * radius, box[1] + 2 * radius],
                   start=180, end=270, fill=self.GLASS_EDGE, width=2)
            od.line([box[0] + radius, box[1], box[2] - radius, box[1]],
                    fill=self.GLASS_EDGE, width=2)
            od.arc([box[2] - 2 * radius, box[1], box[2], box[1] + 2 * radius],
                   start=270, end=360, fill=self.GLASS_EDGE, width=2)
        # 圆角遮罩
        wr = min(self.WIN_RADIUS, W // 2, H // 2)
        mask = Image.new("L", (W, H), 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            [0, 0, W - 1, H - 1], radius=wr, fill=255)
        overlay.putalpha(ImageChops.multiply(overlay.split()[3], mask))
        # 预计算供视频帧使用
        self._glass_rgb = overlay.convert("RGB")
        self._glass_alpha = overlay.split()[3]
        self._corner_mask = mask
        return overlay

    # ---- 视频背景 ----

    def _start_video_bg(self, path, W, H):
        ffmpeg_exe = "ffmpeg"
        if self.ffmpeg_dir:
            ffmpeg_exe = os.path.join(self.ffmpeg_dir, "ffmpeg.exe")
        self._video_player = VideoBackgroundPlayer(path, W, H, fps=30,
                                                   ffmpeg_exe=ffmpeg_exe)
        self._video_player.start()
        self._update_video_frame()

    def _stop_video_bg(self):
        if self._video_after:
            self.after_cancel(self._video_after)
            self._video_after = None
        if self._video_player:
            self._video_player.stop()
            self._video_player = None
        self._bg_photo = None
        self._glass_photo = None
        self.bg_canvas.delete("bg_video")
        self.bg_canvas.delete("bg_overlay")

    def _update_video_frame(self):
        """从视频播放器取帧，加圆角 alpha 后更新画布底层。
        玻璃覆盖层作为独立 canvas image 叠在上方，由 Tk 原生做 alpha 混合。"""
        if not self._video_player or not self._corner_mask:
            return
        frame = self._video_player.get_frame()
        if frame is not None:
            frame.putalpha(self._corner_mask)
            if self._bg_photo is None:
                self._bg_photo = ImageTk.PhotoImage(frame)
                self.bg_canvas.create_image(
                    0, 0, anchor="nw", image=self._bg_photo, tags="bg_video")
                self._glass_photo = ImageTk.PhotoImage(self._glass_overlay)
                self.bg_canvas.create_image(
                    0, 0, anchor="nw", image=self._glass_photo, tags="bg_overlay")
                self.bg_canvas.tag_lower("bg_video")
                self.bg_canvas.tag_lower("bg_overlay")
            else:
                self._bg_photo.paste(frame)
        self._video_after = self.after(20, self._update_video_frame)

    # ---- 子类重写 ----

    def _build_layout(self, W, H):
        pass

    # ---------------------------------------------------------------- 自绘按钮

    def _rounded_img(self, w, h, radius, fill, outline=None, ow=1):
        scale = 2
        im = Image.new("RGBA", (w * scale, h * scale), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        box = [ow * scale, ow * scale,
               w * scale - ow * scale - 1, h * scale - ow * scale - 1]
        d.rounded_rectangle(box, radius=radius * scale, fill=fill,
                            outline=outline, width=ow * scale)
        return im.resize((w, h), Image.LANCZOS)

    def _draw_button(self, tag, x, y, w, h, text, kind="glass",
                     command=None, enabled=True, font_size=10, **kwargs):
        if not enabled:
            fill = (209, 214, 224, 200)
            text_color = "#9aa2b2"
            outline = None
        else:
            style = self.BTN_STYLES.get(kind, self.BTN_STYLES["glass"])
            fill, text_color, outline = style

        radius = min(h // 2, 16)
        img = self._rounded_img(w, h, radius, fill, outline, ow=1 if outline else 0)
        photo = ImageTk.PhotoImage(img)
        self._btn_imgs[tag] = photo

        self.bg_canvas.delete(tag + "_img")
        self.bg_canvas.delete(tag + "_txt")

        self.bg_canvas.create_image(x, y, anchor="nw", image=photo,
                                    tags=(tag, tag + "_img"))
        self.bg_canvas.create_text(x + w // 2, y + h // 2, text=text,
                                   fill=text_color,
                                   font=("Microsoft YaHei UI", font_size),
                                   tags=(tag, tag + "_txt"))

        if command and enabled:
            self.bg_canvas.tag_bind(tag, "<Button-1>", command)
            self.bg_canvas.tag_bind(tag, "<Enter>",
                                    lambda e: self._btn_hover(tag, True, text_color))
            self.bg_canvas.tag_bind(tag, "<Leave>",
                                    lambda e: self._btn_hover(tag, False, text_color))

    def _btn_hover(self, tag, entering, orig_color=None):
        txt_tag = tag + "_txt"
        if entering:
            self.bg_canvas.itemconfig(txt_tag, fill=self.IOS_BLUE)
        else:
            self.bg_canvas.itemconfig(txt_tag, fill=orig_color or self.TEXT_DARK)

    # ---------------------------------------------------------------- 标题栏

    def _draw_titlebar(self, W):
        self.bg_canvas.delete("titlebar")
        self.bg_canvas.create_text(
            20 + 20 + 8, self.TITLE_H // 2, anchor="w",
            text="OmniCalc", fill=self.TEXT_DARK,
            font=("Microsoft YaHei UI", 11, "bold"),
            tags="titlebar")
        self._draw_button("b_min", W - 104, 10, 44, 28, "—",
                          "dark", self._win_minimize)
        self._draw_button("b_close", W - 52, 10, 40, 28, "✕",
                          "dark", self._win_close)
        # 标题栏按钮加入 titlebar tag 以便统一清除
        for t in ("b_min", "b_close"):
            for suffix in ("_img", "_txt"):
                self.bg_canvas.itemconfig(t + suffix, tags=(t, t + suffix, "titlebar"))

    # ---------------------------------------------------------------- 窗口操作

    def _win_press(self, e):
        W, H = self.winfo_width(), self.winfo_height()
        if e.x >= W - 14 and e.y >= H - 14:
            self._win_mode = "resize"
            self._drag_start = (e.x_root, e.y_root, W, H)
            return
        if e.y <= self.TITLE_H and e.x < W - 116 and not self._maximized:
            self._win_mode = "move"
            self._drag_start = (e.x_root - self.winfo_x(),
                                 e.y_root - self.winfo_y())

    def _win_drag(self, e):
        if not self._win_mode or not self._drag_start:
            return
        if self._win_mode == "move":
            dx, dy = self._drag_start
            self.geometry(f"+{e.x_root - dx}+{e.y_root - dy}")
        elif self._win_mode == "resize":
            sx, sy, sw, sh = self._drag_start
            nw = max(460, sw + e.x_root - sx)
            nh = max(500, sh + e.y_root - sy)
            self.geometry(f"{nw}x{nh}")

    def _win_release(self, _e):
        self._win_mode = None
        self._drag_start = None

    def _win_hover(self, e):
        W, H = self.winfo_width(), self.winfo_height()
        if e.x >= W - 14 and e.y >= H - 14:
            self.bg_canvas.configure(cursor="size_nw_se")
        else:
            self.bg_canvas.configure(cursor="")

    def _win_double(self, e):
        if e.y <= self.TITLE_H and e.x < self.winfo_width() - 116:
            self._toggle_maximize()

    def _toggle_maximize(self):
        if not self._maximized:
            self._saved_geom = (self.winfo_x(), self.winfo_y(),
                                self.winfo_width(), self.winfo_height())
            screen_w = self.winfo_screenwidth()
            screen_h = self.winfo_screenheight()
            self.geometry(f"0+0+{screen_w}x{screen_h}")
            self._maximized = True
        else:
            if self._saved_geom:
                x, y, w, h = self._saved_geom
                self.geometry(f"{w}x{h}+{x}+{y}")
            self._maximized = False

    def _win_minimize(self, _e=None):
        try:
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
            ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
        except Exception:
            pass

    def _win_close(self, _e=None):
        self.destroy()

    def destroy(self):
        """重写 destroy，确保视频播放器停止。"""
        self._stop_video_bg()
        super().destroy()
