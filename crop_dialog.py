# -*- coding: utf-8 -*-
"""
图片裁剪弹窗 — 用户选择头像后弹出，拖拽选取正方形区域，不压缩原图比例。
"""

import os

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk, ImageDraw


class CropDialog(tk.Toplevel):
    """正方形裁剪弹窗。用户拖拽选择区域，确认后返回裁剪后的 PIL Image。"""

    PREVIEW_SIZE = 400  # 预览区域大小

    def __init__(self, parent, image_path, title="裁剪头像", callback=None):
        super().__init__(parent)
        self.title(title)
        self.transient(parent)
        self.grab_set()
        self.callback = callback

        self._image = Image.open(image_path).convert("RGBA")
        self._photo = None
        self._drag_start = None
        self._rect = None  # canvas rect id
        self._crop_rect = None  # (x0, y0, x1, y1) in original image coords

        # 计算缩放比例
        ow, oh = self._image.size
        scale = min(self.PREVIEW_SIZE / ow, self.PREVIEW_SIZE / ow)
        self._disp_w = int(ow * scale)
        self._disp_h = int(oh * scale)
        self._scale = scale
        self._disp_img = self._image.resize(
            (self._disp_w, self._disp_h), Image.LANCZOS)

        # 居中窗口
        self.geometry(f"{self._disp_w + 40}x{self._disp_h + 100}")
        parent.update_idletasks()
        px = parent.winfo_x() + (parent.winfo_width() - self._disp_w - 40) // 2
        py = parent.winfo_y() + (parent.winfo_height() - self._disp_h - 100) // 2
        self.geometry(f"+{max(0, px)}+{max(0, py)}")
        self.resizable(False, False)

        self._build_ui()

    def _build_ui(self):
        # 顶部提示
        top = ttk.Frame(self)
        top.pack(fill="x", padx=10, pady=(8, 4))
        ttk.Label(top, text="拖拽选择正方形裁剪区域",
                  font=("Microsoft YaHei UI", 9)).pack()

        # 画布
        self.canvas = tk.Canvas(self, width=self._disp_w, height=self._disp_h,
                                highlightthickness=1,
                                highlightbackground="#d3d8e2",
                                bg="#1a1a2e")
        self.canvas.pack(padx=10, pady=4)
        self._photo = ImageTk.PhotoImage(self._disp_img)
        self.canvas.create_image(0, 0, anchor="nw", image=self._photo,
                                  tags="img")
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

        # 底部按钮
        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(4, 10))
        ttk.Button(bottom, text="取消", command=self._on_cancel).pack(
            side="right", padx=(4, 0))
        ttk.Button(bottom, text="确认裁剪", command=self._on_confirm).pack(
            side="right")

    def _on_press(self, e):
        self._drag_start = (e.x, e.y)
        if self._rect:
            self.canvas.delete(self._rect)

    def _on_drag(self, e):
        if not self._drag_start:
            return
        sx, sy = self._drag_start
        # 正方形：以较短边为准
        dx = e.x - sx
        dy = e.y - sy
        side = max(abs(dx), abs(dy))
        # 确定方向
        x0 = sx if dx >= 0 else sx - side
        y0 = sy if dy >= 0 else sy - side
        x1 = x0 + side
        y1 = y0 + side
        # 限制在画布内
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self._disp_w, x1)
        y1 = min(self._disp_h, y1)
        # 调整为正方形
        side = min(x1 - x0, y1 - y0)
        x1 = x0 + side
        y1 = y0 + side

        if self._rect:
            self.canvas.delete(self._rect)
        # 绘制裁剪框（半透明遮罩效果）
        self._rect = self.canvas.create_rectangle(
            x0, y0, x1, y1, outline="#ff375f", width=2)
        # 存储原始图像坐标
        self._crop_rect = (
            int(x0 / self._scale),
            int(y0 / self._scale),
            int(x1 / self._scale),
            int(y1 / self._scale),
        )

    def _on_release(self, _e):
        pass

    def _on_confirm(self):
        if self._crop_rect is None:
            # 默认居中正方形裁剪
            ow, oh = self._image.size
            side = min(ow, oh)
            x0 = (ow - side) // 2
            y0 = (oh - side) // 2
            self._crop_rect = (x0, y0, x0 + side, y0 + side)

        cropped = self._image.crop(self._crop_rect)
        # 缩放到标准头像尺寸
        cropped = cropped.resize((256, 256), Image.LANCZOS)
        if self.callback:
            self.callback(cropped)
        self.destroy()

    def _on_cancel(self):
        self.destroy()
