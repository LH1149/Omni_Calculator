# -*- coding: utf-8 -*-
"""
模式管理器 — 注册、切换、生命周期管理。
每个模式为 ModePanel 子类，实现 build()/teardown()。
"""


class ModePanel:
    """模式面板基类。子类需实现 build() 和 teardown()。"""

    DISPLAY_NAME = "未命名模式"

    def __init__(self, app):
        self.app = app
        self.canvas_items = []   # canvas item IDs（需 teardown 时 delete）
        self.widgets = {}         # ttk 控件（需 teardown 时 destroy）
        self._images = []        # PhotoImage 引用（防 GC）

    def build(self):
        """在 app.bg_canvas 上构建本模式 UI。"""
        raise NotImplementedError

    def teardown(self):
        """清理本模式所有 UI 元素。"""
        for item in self.canvas_items:
            try:
                self.app.bg_canvas.delete(item)
            except Exception:
                pass
        for w in self.widgets.values():
            try:
                w.destroy()
            except Exception:
                pass
        self.canvas_items.clear()
        self.widgets.clear()
        self._images.clear()


class ModeManager:
    """模式注册与切换。"""

    def __init__(self, app):
        self.app = app
        self._registry = {}   # name -> panel_class
        self._current = None  # 当前 ModePanel 实例

    def register(self, name, panel_class):
        self._registry[name] = panel_class

    @property
    def mode_names(self):
        return list(self._registry.keys())

    @property
    def current_name(self):
        for name, cls in self._registry.items():
            if self._current is not None and isinstance(self._current, cls):
                return name
        return None

    def switch_to(self, name):
        panel_cls = self._registry.get(name)
        if panel_cls is None:
            return
        if self._current:
            self._current.teardown()
        self._current = panel_cls(self.app)
        self._current.build()
