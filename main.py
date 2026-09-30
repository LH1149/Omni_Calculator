# -*- coding: utf-8 -*-
"""OmniCalc 通用运算器 — 主程序入口"""

import os
import sys
import ctypes

import tkinter as tk
from tkinter import ttk, filedialog

from PIL import Image, ImageTk, ImageDraw

from glass_ui import GlassWindow
from modes import ModeManager
from modes.exchange import ExchangeMode
from modes.calculator import CalculatorMode
import skin


class UniCalcApp(GlassWindow):

    def __init__(self):
        super().__init__()
        self.title("OmniCalc 通用运算器")
        self.geometry("560x620")
        self.minsize(460, 500)
        self._avatar_photo = None

        self.mode_manager = ModeManager(self)
        self.mode_manager.register("汇率换算", ExchangeMode)
        self.mode_manager.register("数学计算器", CalculatorMode)
        self._mode_var = tk.StringVar(value="汇率换算")
        self._first_layout_done = False

    # ---- 布局 ----

    def _build_layout(self, W, H):
        self._render_background(W, H)
        self._draw_titlebar(W)
        if not self._first_layout_done:
            self._first_layout_done = True
            self._build_left_sidebar(W, H)
            self.after(100, lambda: self.mode_manager.switch_to("汇率换算"))

    def _build_left_sidebar(self, W, H):
        canvas = self.bg_canvas
        p = self.PADDING
        sx = p + 8
        bw = self.LEFT_W - 16

        # 头像
        avatar_size = 72
        avatar_x = p + (self.LEFT_W - avatar_size) // 2
        avatar_y = self.TITLE_H + p + 16
        av_path = skin.avatar_path()
        if av_path:
            try:
                av_img = Image.open(av_path).convert("RGBA").resize(
                    (avatar_size, avatar_size), Image.LANCZOS)
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse(
                    [0, 0, avatar_size - 1, avatar_size - 1], fill=255)
                av_img.putalpha(mask)
            except Exception:
                av_img = self._make_default_avatar(avatar_size)
        else:
            av_img = self._make_default_avatar(avatar_size)
        self._avatar_photo = ImageTk.PhotoImage(av_img)
        canvas.create_image(avatar_x, avatar_y, anchor="nw",
                            image=self._avatar_photo, tags="avatar")

        # 按钮
        by = avatar_y + avatar_size + 16
        self._draw_button("b_avatar", sx, by, bw, 32, "更换头像",
                          "glass", self._choose_avatar, font_size=9)
        by += 44
        self._draw_button("b_skin", sx, by, bw, 32, "更换皮肤",
                          "glass", self._choose_skin, font_size=9)
        by += 44
        self._draw_button("b_reset", sx, by, bw, 32, "恢复默认",
                          "ghost", self._reset_all, font_size=9)

        # 模式选择按钮（glass 自绘 + tk.Menu 下拉）
        by += 56
        self._draw_button("b_mode", sx, by, bw, 34, self._mode_var.get(),
                          "glass", self._open_mode_menu, font_size=10)
        self._mode_btn_y = by

    def _refresh_layout(self):
        W = self.bg_canvas.winfo_width()
        H = self.bg_canvas.winfo_height()
        if W < 2 or H < 2:
            return
        current = self.mode_manager.current_name
        self._render_background(W, H)
        self._draw_titlebar(W)
        # 更新头像
        canvas = self.bg_canvas
        p = self.PADDING
        avatar_size = 72
        avatar_x = p + (self.LEFT_W - avatar_size) // 2
        avatar_y = self.TITLE_H + p + 16
        av_path = skin.avatar_path()
        if av_path:
            try:
                av_img = Image.open(av_path).convert("RGBA").resize(
                    (avatar_size, avatar_size), Image.LANCZOS)
                mask = Image.new("L", (avatar_size, avatar_size), 0)
                ImageDraw.Draw(mask).ellipse(
                    [0, 0, avatar_size - 1, avatar_size - 1], fill=255)
                av_img.putalpha(mask)
            except Exception:
                av_img = self._make_default_avatar(avatar_size)
        else:
            av_img = self._make_default_avatar(avatar_size)
        self._avatar_photo = ImageTk.PhotoImage(av_img)
        canvas.delete("avatar")
        canvas.create_image(avatar_x, avatar_y, anchor="nw",
                            image=self._avatar_photo, tags="avatar")
        if current:
            self.mode_manager.switch_to(current)

    # ---- 头像 ----

    def _make_default_avatar(self, size):
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx = size // 2
        r = size // 2 - 1
        for i in range(r, 0, -1):
            t = 1 - i / r
            cr = int(10 + t * 245)
            cg = int(132 + t * (-77))
            cb = int(255 + t * (-160))
            d.ellipse([cx - i, cx - i, cx + i, cx + i], fill=(cr, cg, cb, 255))
        try:
            from PIL import ImageFont
            font = ImageFont.truetype("arial.ttf", size // 2 + 4)
        except Exception:
            font = None
        d.text((cx - 6, cx - 12), "U", fill="white", font=font)
        return img

    def _choose_avatar(self, _e=None):
        path = filedialog.askopenfilename(
            title="选择头像图片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.webp *.bmp")])
        if not path:
            return
        from crop_dialog import CropDialog
        def on_cropped(img):
            av_path = os.path.join(skin.skins_dir(), "avatar.png")
            os.makedirs(skin.skins_dir(), exist_ok=True)
            img.save(av_path, "PNG")
            data = skin._read_config()
            data["avatar_file"] = "avatar.png"
            skin._write_config(data)
            self._refresh_layout()
        CropDialog(self, path, title="裁剪头像", callback=on_cropped)

    def _choose_skin(self, _e=None):
        path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("图片", "*.jpg *.jpeg *.png *.webp *.bmp"),
                       ("视频", "*.mp4 *.webm *.mkv *.mov *.avi *.gif")])
        if not path:
            return
        skin.import_skin(path)
        self._refresh_layout()

    def _reset_all(self, _e=None):
        skin.reset_skin()
        self._refresh_layout()

    # ---- 模式切换 ----

    def _open_mode_menu(self, _e=None):
        m = tk.Menu(self, tearoff=0, font=("Microsoft YaHei UI", 10))
        for name in self.mode_manager.mode_names:
            m.add_command(label=name,
                          command=lambda n=name: self._select_mode(n))
        self.update_idletasks()
        x = self.winfo_x() + self.PADDING + 8
        y = self.winfo_y() + self._mode_btn_y + 34
        m.tk_popup(x, y)

    def _select_mode(self, name):
        self._mode_var.set(name)
        self.bg_canvas.itemconfig("b_mode_txt", text=name)
        self.mode_manager.switch_to(name)

    # ---- 图标 ----

    def _set_taskbar_icon(self):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "OmniCalc.App")
        except Exception:
            pass
        icon_path = os.path.join(skin.bundle_dir(), "assets", "icon.ico")
        if not os.path.isfile(icon_path):
            icon_path = os.path.join(skin.app_dir(), "assets", "icon.ico")
        if os.path.isfile(icon_path):
            try:
                self.iconbitmap(icon_path)
            except Exception:
                pass


def main():
    app = UniCalcApp()
    app._set_taskbar_icon()
    app.mainloop()


if __name__ == "__main__":
    main()
