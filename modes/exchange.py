# -*- coding: utf-8 -*-
"""汇率换算模式面板"""

import json
import threading
import urllib.request
import urllib.error

import tkinter as tk
from tkinter import ttk

from PIL import Image, ImageTk, ImageDraw

from . import ModePanel
from currencies import search_currencies, CURRENCIES

DEFAULT_CURRENCIES = [
    ("CNY", "人民币"),
    ("MYR", "马来西亚林吉特"),
    ("IDR", "印尼盾"),
    ("SGD", "新加坡元"),
    ("VND", "越南盾"),
]

API_URL = "https://open.er-api.com/v6/latest/{}"


class ExchangeMode(ModePanel):
    DISPLAY_NAME = "汇率换算"
    ROW_H = 56
    ROW_GAP = 14
    ROW_START_Y = 80
    DIAMOND_SIZE = 14

    def __init__(self, app):
        super().__init__(app)
        self.currencies = list(DEFAULT_CURRENCIES)
        self._rates = {}
        self._rate_base = None
        self._fetching = False
        self._fetch_after_id = None
        self._popup = None

    def build(self):
        app = self.app
        canvas = app.bg_canvas
        W = canvas.winfo_width()
        p = app.PADDING
        rx = app.LEFT_W + 2 * p
        ry = app.TITLE_H + p
        rw = W - app.LEFT_W - 3 * p
        self._rx, self._ry, self._rw = rx, ry, rw
        self._build_rows(rx, ry, rw)

    def _build_rows(self, rx, ry, rw):
        pad = 16
        for i in range(5):
            row_y = ry + self.ROW_START_Y + i * (self.ROW_H + self.ROW_GAP)
            code, name = self.currencies[i]
            self._build_row(i, rx + pad, row_y, rw - 2 * pad, code, name, i == 0)

    def _build_row(self, idx, x, y, w, code, name, is_input):
        app = self.app
        canvas = app.bg_canvas

        # 菱形
        dia_size = self.DIAMOND_SIZE
        dia_img = self._make_diamond(dia_size, app.IOS_PINK)
        dia_photo = ImageTk.PhotoImage(dia_img)
        self._images.append(dia_photo)
        dia_x = x + 4
        dia_y = y + (self.ROW_H - dia_size) // 2
        dia_tag = f"ex_dia_{idx}"
        self.canvas_items.append(
            canvas.create_image(dia_x, dia_y, anchor="nw",
                                image=dia_photo, tags=dia_tag))
        canvas.tag_bind(dia_tag, "<Button-1>",
                        lambda e, i=idx: self._open_currency_search(i))

        # 货币文字
        text = f"{name}  {code}"
        txt_x = dia_x + dia_size + 8
        txt_y = y + self.ROW_H // 2
        txt_tag = f"ex_txt_{idx}"
        self.canvas_items.append(
            canvas.create_text(txt_x, txt_y, anchor="w", text=text,
                               fill=app.TEXT_DARK,
                               font=("Microsoft YaHei UI", 10),
                               tags=txt_tag))
        canvas.tag_bind(txt_tag, "<Button-1>",
                        lambda e, i=idx: self._open_currency_search(i))

        # 金额区域
        amt_x = x + w - 160
        amt_w = 150
        amt_y = y + (self.ROW_H - 30) // 2

        if is_input:
            var = tk.StringVar()
            entry = ttk.Entry(canvas, textvariable=var,
                              font=("Microsoft YaHei UI", 11), width=14)
            entry.place(x=amt_x, y=amt_y, width=amt_w, height=30)
            var.trace_add("write", lambda *_: self._on_input_change())
            self.widgets[f"entry_{idx}"] = entry
            self._input_var = var
        else:
            label = ttk.Label(canvas, text="—",
                              font=("Microsoft YaHei UI", 11),
                              anchor="e", width=14)
            label.place(x=amt_x, y=amt_y, width=amt_w, height=30)
            self.widgets[f"label_{idx}"] = label

        # 分隔线
        if idx < 4:
            line_y = y + self.ROW_H + self.ROW_GAP // 2
            self.canvas_items.append(
                canvas.create_line(x, line_y, x + w, line_y,
                                   fill="#d3d8e2", width=1))

    def _make_diamond(self, size, color):
        scale = 2
        im = Image.new("RGBA", (size * scale, size * scale), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        cx = size * scale / 2
        cy = size * scale / 2
        s = size * scale / 2 - 1
        pts = [(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)]
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        d.polygon(pts, fill=(r, g, b, 255))
        return im.resize((size, size), Image.LANCZOS)

    # ---- 货币搜索弹窗（普通 Toplevel + 深色主题）----

    def _open_currency_search(self, row_idx):
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
        popup = tk.Toplevel(self.app)
        popup.title("选择货币")
        popup.geometry("320x400")
        popup.transient(self.app)
        popup.grab_set()
        popup.configure(bg="#1a1a2e")
        popup.resizable(False, False)
        self._popup = popup

        # 搜索框
        search_var = tk.StringVar()
        entry = tk.Entry(popup, textvariable=search_var,
                         font=("Microsoft YaHei UI", 11),
                         bg="#2a2a4e", fg="#ffffff",
                         insertbackground="#ffffff",
                         relief="flat", bd=0,
                         highlightthickness=1,
                         highlightbackground="#3a3a5e",
                         highlightcolor="#0a84ff")
        entry.pack(fill="x", padx=12, pady=(12, 8))
        entry.focus_set()

        # 列表
        listbox = tk.Listbox(popup, font=("Microsoft YaHei UI", 10),
                             bg="#1a1a2e", fg="#e0e0e8",
                             selectbackground="#0a84ff",
                             selectforeground="white",
                             activestyle="none", relief="flat", bd=0,
                             highlightthickness=0)
        listbox.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        results = list(CURRENCIES)

        def refresh(query=""):
            nonlocal results
            results = search_currencies(query)
            listbox.delete(0, tk.END)
            for c, n in results:
                listbox.insert(tk.END, f"{n}  {c}")

        refresh()

        def on_search(*_):
            refresh(search_var.get())

        search_var.trace_add("write", on_search)

        def on_select(_=None):
            sel = listbox.curselection()
            if not sel:
                return
            code, name = results[sel[0]]
            self._apply_currency(row_idx, code, name)
            popup.destroy()
            self._popup = None

        listbox.bind("<Double-Button-1>", on_select)
        listbox.bind("<<ListboxSelect>>", on_select)
        listbox.bind("<Return>", on_select)
        entry.bind("<Return>", on_select)
        popup.bind("<Escape>", lambda _: (popup.destroy(),
                                           setattr(self, '_popup', None)))

    def _apply_currency(self, idx, code, name):
        self.currencies[idx] = (code, name)
        canvas = self.app.bg_canvas
        canvas.itemconfig(f"ex_txt_{idx}", text=f"{name}  {code}")
        if idx == 0:
            self._fetch_rates()
        else:
            self._update_outputs()

    # ---- 汇率获取 ----

    def _fetch_rates(self):
        base = self.currencies[0][0]
        if self._fetching:
            return
        self._fetching = True
        for i in range(1, 5):
            label = self.widgets.get(f"label_{i}")
            if label:
                label.config(text="加载中…")

        def do_fetch():
            try:
                url = API_URL.format(base)
                req = urllib.request.Request(url, headers={
                    "User-Agent": "OmniCalc/1.0"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if data.get("result") == "success":
                    rates = data.get("rates", {})
                    self.app.after(0, lambda: self._on_rates_fetched(base, rates))
                else:
                    self.app.after(0, lambda: self._on_fetch_error("API 返回失败"))
            except urllib.error.URLError:
                self.app.after(0, lambda: self._on_fetch_error("网络连接失败"))
            except Exception:
                self.app.after(0, lambda: self._on_fetch_error("获取汇率失败"))
            finally:
                self._fetching = False

        threading.Thread(target=do_fetch, daemon=True).start()

    def _on_rates_fetched(self, base, rates):
        self._rates = rates
        self._rate_base = base
        self._update_outputs()

    def _on_fetch_error(self, msg):
        for i in range(1, 5):
            label = self.widgets.get(f"label_{i}")
            if label:
                label.config(text=msg)

    # ---- 计算 ----

    def _on_input_change(self):
        if self._fetch_after_id:
            self.app.after_cancel(self._fetch_after_id)
        self._fetch_after_id = self.app.after(300, self._update_outputs)

    def _update_outputs(self):
        if not self._rates or not self._rate_base:
            self._fetch_rates()
            return
        try:
            amount = float(self._input_var.get() or "0")
        except ValueError:
            for i in range(1, 5):
                label = self.widgets.get(f"label_{i}")
                if label:
                    label.config(text="—")
            return
        for i in range(1, 5):
            code = self.currencies[i][0]
            label = self.widgets.get(f"label_{i}")
            if label is None:
                continue
            rate = self._rates.get(code)
            if rate is None:
                label.config(text="不支持")
                continue
            result = amount * rate
            if result >= 10000:
                text = f"{result:,.0f}"
            elif result >= 100:
                text = f"{result:,.2f}"
            else:
                text = f"{result:,.4f}"
            label.config(text=text)

    def teardown(self):
        if self._popup is not None and self._popup.winfo_exists():
            self._popup.destroy()
        if self._fetch_after_id:
            try:
                self.app.after_cancel(self._fetch_after_id)
            except Exception:
                pass
        super().teardown()
