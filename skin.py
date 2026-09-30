# -*- coding: utf-8 -*-
"""
皮肤管理系统 — 背景图/头像的导入、持久化、恢复默认。
配置存储在 exe 同目录 skins/skin.json，跨版本保留。
"""

import os
import re
import sys
import json
import shutil
import subprocess

from PIL import Image

VIDEO_EXTS = (".mp4", ".webm", ".mkv", ".mov", ".avi", ".gif")
IMG_EXTS = (".jpg", ".jpeg", ".png", ".webp", ".bmp")


def app_dir():
    """程序所在目录（打包后是 exe 所在目录）。"""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def bundle_dir():
    """PyInstaller onefile 解包目录（运行期临时目录）。"""
    return getattr(sys, "_MEIPASS", app_dir())


def skins_dir():
    return os.path.join(app_dir(), "skins")


def skin_config_path():
    return os.path.join(skins_dir(), "skin.json")


def _read_config():
    try:
        with open(skin_config_path(), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _write_config(data):
    os.makedirs(skins_dir(), exist_ok=True)
    with open(skin_config_path(), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def default_skin_path():
    """内置默认背景皮肤。"""
    for p in (os.path.join(bundle_dir(), "assets", "skin.default.jpg"),
              os.path.join(app_dir(), "assets", "skin.default.jpg")):
        if p and os.path.isfile(p):
            return p
    return None


def current_skin_path():
    """当前背景图：用户自定义优先，否则默认。"""
    custom = _read_config().get("skin_file")
    if custom:
        p = os.path.join(skins_dir(), os.path.basename(custom))
        if os.path.isfile(p):
            return p
    return default_skin_path()


def avatar_path():
    """用户自定义头像路径，不存在返回 None。"""
    custom = _read_config().get("avatar_file")
    if custom:
        p = os.path.join(skins_dir(), os.path.basename(custom))
        if os.path.isfile(p):
            return p
    return None


def is_video_path(path):
    return path and os.path.splitext(path)[1].lower() in VIDEO_EXTS


def _copy_to_skins(src_path, prefix):
    os.makedirs(skins_dir(), exist_ok=True)
    ext = os.path.splitext(src_path)[1].lower()
    if ext not in IMG_EXTS and ext not in VIDEO_EXTS:
        return None
    dst = os.path.join(skins_dir(), prefix + ext)
    shutil.copy2(src_path, dst)
    return dst


def import_skin(src_path):
    name = _copy_to_skins(src_path, "skin_custom")
    if not name:
        return None
    data = _read_config()
    data["skin_file"] = os.path.basename(name)
    _write_config(data)
    return name


def import_avatar(src_path):
    name = _copy_to_skins(src_path, "avatar")
    if not name:
        return None
    data = _read_config()
    data["avatar_file"] = os.path.basename(name)
    _write_config(data)
    return name


def reset_skin():
    data = _read_config()
    data.pop("skin_file", None)
    data.pop("avatar_file", None)
    _write_config(data)
    if os.path.isdir(skins_dir()):
        for f in os.listdir(skins_dir()):
            if f.lower().startswith("skin_custom") or f.lower().startswith("avatar"):
                fp = os.path.join(skins_dir(), f)
                if os.path.isfile(fp):
                    os.remove(fp)


def cover_image(path, w, h):
    """加载图片并以 cover 方式裁剪到 w×h。"""
    img = Image.open(path)
    img = img.convert("RGBA")
    src_w, src_h = img.size
    scale = max(w / src_w, h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return img.crop((left, top, left + w, top + h))


# ---------------------------------------------------------------- 媒体尺寸

def _ffmpeg_path():
    """查找 ffmpeg.exe：bin 目录 / 打包资源目录。"""
    candidates = [
        os.path.join(app_dir(), "bin", "ffmpeg.exe"),
        os.path.join(bundle_dir(), "bin", "ffmpeg.exe"),
        os.path.join(bundle_dir(), "ffmpeg.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            return p
    return "ffmpeg"


def media_size(path):
    """读取图片或视频的原始分辨率 (width, height)，失败返回 None。"""
    if not path or not os.path.isfile(path):
        return None
    ext = os.path.splitext(path)[1].lower()
    # GIF 和图片用 PIL 读取（GIF 取首帧尺寸）
    if ext in IMG_EXTS or ext == ".gif":
        try:
            with Image.open(path) as im:
                return im.size
        except Exception:
            return None
    # 真视频：解析 ffmpeg -i 输出中的 分辨率
    try:
        proc = subprocess.run(
            [_ffmpeg_path(), "-i", path],
            capture_output=True, timeout=8,
            creationflags=0x08000000)  # CREATE_NO_WINDOW
        text = proc.stderr.decode("utf-8", errors="ignore")
        m = re.search(r"(\d{2,5})x(\d{2,5})", text)
        if m:
            return int(m.group(1)), int(m.group(2))
    except Exception:
        pass
    return None


def fit_window_size(media_w, media_h, screen_w, screen_h,
                    min_w=480, min_h=500, max_ratio=0.85):
    """按媒体原始宽高比计算窗口尺寸。
    - 上限不超过屏幕 max_ratio
    - 下限不小于 UI 最小尺寸 min_w × min_h
    """
    max_w = max(min_w, int(screen_w * max_ratio))
    max_h = max(min_h, int(screen_h * max_ratio))
    # 先等比缩放到上限内
    scale = min(1.0, max_w / media_w, max_h / media_h)
    w = media_w * scale
    h = media_h * scale
    # 仍小于 UI 最小尺寸时等比放大
    if w < min_w or h < min_h:
        scale2 = max(min_w / w, min_h / h)
        w *= scale2
        h *= scale2
    return max(min_w, int(w)), max(min_h, int(h))


# ---------------------------------------------------------------- 窗口尺寸持久化

def save_window_size(w, h):
    data = _read_config()
    data["window_w"] = int(w)
    data["window_h"] = int(h)
    _write_config(data)


def load_window_size():
    """返回 (w, h)，无记录返回 None。"""
    data = _read_config()
    w, h = data.get("window_w"), data.get("window_h")
    if isinstance(w, int) and isinstance(h, int) and w >= 480 and h >= 500:
        return w, h
    return None
