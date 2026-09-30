# -*- coding: utf-8 -*-
"""
数学计算器模式面板。

布局：显示屏 + 4×5 按键网格（C, ⌫, %, ÷ / 7~9, × / 4~6, − / 1~3, + / 0, ., =）。
按键用 canvas 自绘圆角按钮，支持四则运算、清除、退格、百分比。
"""

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk

from . import ModePanel


class CalculatorMode(ModePanel):
    """数学计算器模式。"""

    DISPLAY_NAME = "数学计算器"

    # 按键布局 (text, kind, action_key)
    KEYS = [
        [("C", "pink", "clear"),  ("⌫", "gray", "back"),  ("%", "gray", "percent"), ("÷", "blue", "op")],
        [("7", "glass", "num"),   ("8", "glass", "num"),   ("9", "glass", "num"),    ("×", "blue", "op")],
        [("4", "glass", "num"),   ("5", "glass", "num"),   ("6", "glass", "num"),    ("−", "blue", "op")],
        [("1", "glass", "num"),   ("2", "glass", "num"),   ("3", "glass", "num"),    ("+", "blue", "op")],
        [("0", "glass", "num"),   (".", "glass", "dot"),   ("=", "blue", "equals"),  ("", "glass", "none")],
    ]

    # 操作符映射
    OP_MAP = {"÷": "/", "×": "*", "−": "-", "+": "+"}

    def __init__(self, app):
        super().__init__(app)
        self._display_var = tk.StringVar(value="0")
        self._expression = ""     # 当前表达式字符串
        self._just_evaluated = False

    def build(self):
        app = self.app
        canvas = app.bg_canvas
        W = canvas.winfo_width()
        p = app.PADDING
        rx = app.LEFT_W + 2 * p
        ry = app.TITLE_H + p
        rw = W - app.LEFT_W - 3 * p

        self._build_display(rx, ry, rw)
        self._build_buttons(rx, ry, rw)

    def _build_display(self, rx, ry, rw):
        """显示屏。"""
        app = self.app
        canvas = app.bg_canvas
        pad = 16
        disp_x = rx + pad
        disp_y = ry + 30
        disp_w = rw - 2 * pad
        disp_h = 56

        # 显示框背景
        img = app._rounded_img(disp_w, disp_h, 12,
                               (255, 255, 255, 200),
                               outline=(211, 216, 226, 255), ow=1)
        photo = ImageTk.PhotoImage(img)
        self._images.append(photo)
        self.canvas_items.append(
            canvas.create_image(disp_x, disp_y, anchor="nw",
                                image=photo, tags="calc_display_bg"))

        # 显示文字
        self.canvas_items.append(
            canvas.create_text(
                disp_x + disp_w - 12, disp_y + disp_h // 2,
                anchor="e", text="0",
                fill=app.TEXT_DARK,
                font=("Microsoft YaHei UI", 22, "bold"),
                tags="calc_display"))

    def _build_buttons(self, rx, ry, rw):
        """按键网格。"""
        app = self.app
        canvas = app.bg_canvas
        pad = 16
        grid_x = rx + pad
        grid_y = ry + 30 + 56 + 20  # display + gap
        grid_w = rw - 2 * pad
        available_h = app.winfo_height() - app.TITLE_H - 2 * app.PADDING \
                      - 30 - 56 - 20 - pad
        cols = 4
        rows = 5
        gap = 6
        btn_w = (grid_w - gap * (cols - 1)) // cols
        btn_h = max(50, min(70, (available_h - gap * (rows - 1)) // rows))

        for row_idx, row_keys in enumerate(self.KEYS):
            for col_idx, (text, kind, action) in enumerate(row_keys):
                if not text:
                    continue
                bx = grid_x + col_idx * (btn_w + gap)
                by = grid_y + row_idx * (btn_h + gap)
                tag = f"calc_btn_{row_idx}_{col_idx}"

                # 数字键用宽字体
                font_size = 16 if action in ("num", "dot", "op", "equals") else 13
                # 运算符映射
                op_char = text
                self._draw_button(
                    tag, bx, by, btn_w, btn_h, text, kind,
                    lambda e, t=op_char, a=action: self._on_key(t, a),
                    font_size=font_size)

    def _draw_button(self, tag, x, y, w, h, text, kind, command,
                     font_size=14):
        """在 canvas 上绘制计算器按钮（复用 app._draw_button 但修正 tags）。"""
        app = self.app
        app._draw_button(tag, x, y, w, h, text, kind, command,
                         font_size=font_size)
        # _draw_button 存入 self._btn_imgs，也需记录到 canvas_items
        self.canvas_items.append(tag + "_img")
        self.canvas_items.append(tag + "_txt")

    # ---------------------------------------------------------------- 计算逻辑

    def _on_key(self, text, action):
        if action == "num":
            self._input_number(text)
        elif action == "dot":
            self._input_dot()
        elif action == "op":
            self._input_operator(text)
        elif action == "equals":
            self._evaluate()
        elif action == "clear":
            self._clear()
        elif action == "back":
            self._backspace()
        elif action == "percent":
            self._percent()
        self._update_display()

    def _input_number(self, num):
        if self._just_evaluated:
            self._expression = ""
            self._just_evaluated = False
        if self._expression == "0":
            self._expression = num
        else:
            self._expression += num

    def _input_dot(self):
        if self._just_evaluated:
            self._expression = "0"
            self._just_evaluated = False
        # 防止重复小数点
        parts = self._expression.rsplit(" ", 1)
        current = parts[-1] if parts else ""
        if "." not in current:
            if not current:
                current = "0"
            self._expression = (parts[0] + " " if len(parts) > 1 else "") \
                               + current + "."

    def _input_operator(self, op_text):
        op = self.OP_MAP.get(op_text, op_text)
        if self._just_evaluated:
            self._just_evaluated = False
        # 替换末尾运算符
        if self._expression and self._expression[-1] in "+-*/":
            self._expression = self._expression[:-1] + op
        elif self._expression:
            self._expression += op
        else:
            self._expression = "0" + op

    def _evaluate(self):
        if not self._expression:
            return
        try:
            expr = self._expression.replace(" ", "")
            # 安全评估：只允许数字和运算符
            allowed = set("0123456789.+-*/()")
            if not all(c in allowed for c in expr):
                return
            result = eval(expr)
            # 格式化结果
            if isinstance(result, float) and result.is_integer():
                result = int(result)
            self._expression = str(result)
            self._just_evaluated = True
        except ZeroDivisionError:
            self._expression = "错误：除以零"
            self._just_evaluated = True
        except Exception:
            self._expression = "错误"
            self._just_evaluated = True

    def _clear(self):
        self._expression = "0"
        self._just_evaluated = False

    def _backspace(self):
        if self._just_evaluated:
            self._clear()
            return
        if len(self._expression) > 1:
            self._expression = self._expression[:-1]
        else:
            self._expression = "0"

    def _percent(self):
        try:
            val = float(self._expression) if self._expression else 0
            self._expression = str(val / 100)
            self._just_evaluated = True
        except ValueError:
            pass

    def _update_display(self):
        """更新显示屏文字。"""
        canvas = self.app.bg_canvas
        text = self._expression or "0"
        # 限制显示长度
        if len(text) > 18:
            text = text[:18] + "…"
        canvas.itemconfig("calc_display", text=text)

    def teardown(self):
        super().teardown()
